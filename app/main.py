"""InternHub Production Capstone Application (Task 5)
Features: Structured request logging, multi-stage health probes, security headers, rate limiting, and parameterized queries.
"""
import json
import logging
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from . import db
from .limiter import rate_limiter
from .schemas import ApplicationCreate, InternshipCreate, InternshipPatch, InternshipReplace

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("internhub.api")

START_TIME = time.time()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
COLUMNS = ["title", "company", "category", "location", "work_mode", "duration", "stipend", "skills", "description", "deadline", "status"]
NOW = "strftime('%Y-%m-%dT%H:%M:%SZ','now')"


_db_initialized = False


def ensure_db():
    global _db_initialized
    if not _db_initialized:
        try:
            db.seed_db()
            _db_initialized = True
        except Exception as e:
            logger.error("DB init error: %s", str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema and checking seed data...")
    ensure_db()
    yield
    logger.info("InternHub server shutting down cleanly.")


app = FastAPI(
    title="InternHub Production Capstone API",
    version="2.0.0",
    description="Full-stack Production Internship Board with structured logging, health checks, rate limiting, and security headers.",
    lifespan=lifespan,
)


# ---------- Middleware 1: Structured Request & Performance Logging ----------
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status_code = response.status_code

        # Log structured line
        logger.info(
            "%s %s -> %d in %0.2fms | ip=%s",
            method,
            path,
            status_code,
            duration_ms,
            client_ip,
        )
        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response


# ---------- Middleware 2: Production Security Headers ----------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' https: data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:* https:;"
        )
        return response


app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Error Formatting ----------
def error_response(status: int, code: str, message: str, details=None, headers=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": details or []}}
    return JSONResponse(status_code=status, content=body, headers=headers or {})


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(p) for p in e["loc"] if p != "body") or "body", "message": e["msg"]}
        for e in exc.errors()
    ]
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, details)
    return error_response(400, "VALIDATION_ERROR", "Request validation failed", details)


@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 429: "RATE_LIMITED"}
    return error_response(exc.status_code, codes.get(exc.status_code, "HTTP_ERROR"), str(exc.detail))


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, str(exc))
    return error_response(500, "INTERNAL_ERROR", "An unexpected server error occurred")


# ---------- Database Helpers ----------
def fetch_one(conn, internship_id: int):
    row = conn.execute("SELECT * FROM internships WHERE id = ?", (internship_id,)).fetchone()
    if row:
        d = dict(row)
        if isinstance(d.get("skills"), str):
            try:
                d["skills"] = json.loads(d["skills"])
            except Exception:
                d["skills"] = []
        return d
    return None


def not_found(internship_id: int):
    return error_response(404, "NOT_FOUND", f"Internship {internship_id} not found")


def to_row_data(data: dict) -> dict:
    if data.get("deadline") is not None:
        data["deadline"] = data["deadline"].isoformat()
    if isinstance(data.get("skills"), list):
        data["skills"] = json.dumps(data["skills"])
    return data


# ---------- Production Health Probes ----------
@app.get("/health", tags=["Health"])
def health_check():
    """Comprehensive system health diagnostics and telemetry."""
    ensure_db()
    uptime_sec = round(time.time() - START_TIME, 2)
    db_metrics = db.get_db_stats()
    return {
        "status": "healthy",
        "service": "internhub-capstone",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_sec,
        "database": db_metrics,
        "environment": "production-ready",
    }


@app.get("/health/ready", tags=["Health"])
def readiness_check():
    """Readiness probe for load balancers / deployment orchestrators."""
    try:
        with db.get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"ready": True}
    except Exception as e:
        logger.error("Readiness probe failed: %s", str(e))
        return JSONResponse(status_code=503, content={"ready": False, "reason": str(e)})


@app.get("/health/live", tags=["Health"])
def liveness_check():
    """Liveness probe verifying event loop responsiveness."""
    return {"alive": True}


# ---------- Internship Endpoints ----------
@app.get("/internships", tags=["Internships"])
def list_internships(
    status: Optional[str] = Query(None, pattern="^(open|closed)$"),
    work_mode: Optional[str] = Query(None, pattern="^(remote|onsite|hybrid)$"),
    category: Optional[str] = Query(None, max_length=60),
    max_duration: Optional[int] = Query(None, ge=1, le=12),
    min_stipend: Optional[int] = Query(None, ge=0),
    q: Optional[str] = Query(None, max_length=100, description="Search role, company, or skills"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Retrieve filtered, searchable list of internships."""
    ensure_db()
    where, params = [], []
    if status:
        where.append("status = ?")
        params.append(status)
    if work_mode:
        where.append("work_mode = ?")
        params.append(work_mode)
    if category:
        where.append("category = ?")
        params.append(category)
    if max_duration:
        where.append("duration <= ?")
        params.append(max_duration)
    if min_stipend:
        where.append("stipend >= ?")
        params.append(min_stipend)
    if q:
        where.append("(title LIKE ? OR company LIKE ? OR skills LIKE ? OR description LIKE ?)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term, search_term])

    clause = f"WHERE {' AND '.join(where)}" if where else ""

    with db.get_conn() as conn:
        total = conn.execute(f"SELECT COUNT(*) FROM internships {clause}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM internships {clause} ORDER BY id ASC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("skills"), str):
            try:
                d["skills"] = json.loads(d["skills"])
            except Exception:
                d["skills"] = []
        results.append(d)

    return {"data": results, "meta": {"total": total, "limit": limit, "offset": offset}}


@app.get("/internships/{internship_id}", tags=["Internships"])
def get_internship(internship_id: int):
    """Retrieve full details for an internship listing."""
    with db.get_conn() as conn:
        row = fetch_one(conn, internship_id)
    if row is None:
        return not_found(internship_id)
    return {"data": row}


@app.post("/internships", status_code=201, tags=["Internships"])
def create_internship(payload: InternshipCreate, response: Response):
    """Create a new internship position."""
    data = to_row_data(payload.model_dump())
    with db.get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO internships ({', '.join(COLUMNS)}) VALUES ({', '.join(':' + c for c in COLUMNS)})",
            data,
        )
        row = fetch_one(conn, cur.lastrowid)
    logger.info("Created internship #%d: '%s' at '%s'", row["id"], row["title"], row["company"])
    response.headers["Location"] = f"/internships/{row['id']}"
    return {"data": row}


@app.put("/internships/{internship_id}", tags=["Internships"])
def replace_internship(internship_id: int, payload: InternshipReplace):
    """Replace entire internship position."""
    data = to_row_data(payload.model_dump())
    data["id"] = internship_id
    sets = ", ".join(f"{c} = :{c}" for c in COLUMNS)
    with db.get_conn() as conn:
        if fetch_one(conn, internship_id) is None:
            return not_found(internship_id)
        conn.execute(f"UPDATE internships SET {sets}, updated_at = {NOW} WHERE id = :id", data)
        row = fetch_one(conn, internship_id)
    return {"data": row}


@app.patch("/internships/{internship_id}", tags=["Internships"])
def update_internship(internship_id: int, payload: InternshipPatch):
    """Partial update of internship properties."""
    data = to_row_data(payload.model_dump(exclude_unset=True))
    if not data:
        return error_response(400, "VALIDATION_ERROR", "Provide at least one field to update")
    sets = ", ".join(f"{c} = :{c}" for c in data)
    data["id"] = internship_id
    with db.get_conn() as conn:
        if fetch_one(conn, internship_id) is None:
            return not_found(internship_id)
        conn.execute(f"UPDATE internships SET {sets}, updated_at = {NOW} WHERE id = :id", data)
        row = fetch_one(conn, internship_id)
    return {"data": row}


@app.delete("/internships/{internship_id}", status_code=204, tags=["Internships"])
def delete_internship(internship_id: int):
    """Delete an internship listing."""
    with db.get_conn() as conn:
        cur = conn.execute("DELETE FROM internships WHERE id = ?", (internship_id,))
    if cur.rowcount == 0:
        return not_found(internship_id)
    logger.info("Deleted internship #%d", internship_id)
    return Response(status_code=204)


# ---------- Application Endpoints ----------
@app.post("/internships/{internship_id}/apply", status_code=201, tags=["Applications"])
def submit_application(internship_id: int, payload: ApplicationCreate, request: Request, response: Response):
    """Submit application with rate limiting and duplicate validation."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_key = f"apply:{client_ip}"

    # Rate Limit: 5 applications per 60 seconds per IP
    allowed, retry_after = rate_limiter.is_allowed(rate_key, max_requests=5, window_seconds=60)
    if not allowed:
        logger.warning("Rate limit reached for IP: %s on application submission", client_ip)
        return error_response(
            429,
            "RATE_LIMITED",
            f"Application submission rate limit reached. Please retry in {retry_after} seconds.",
            details=[{"field": "rate_limit", "message": f"Retry after {retry_after}s"}],
            headers={"Retry-After": str(retry_after)},
        )

    with db.get_conn() as conn:
        internship = fetch_one(conn, internship_id)
        if internship is None:
            return not_found(internship_id)

        if internship["status"] != "open":
            return error_response(
                400,
                "INTERNSHIP_CLOSED",
                f"Applications for '{internship['title']}' are currently closed.",
                details=[{"field": "status", "message": "Position is closed"}],
            )

        # Duplicate check
        existing = conn.execute(
            "SELECT id FROM applications WHERE internship_id = ? AND email = ?",
            (internship_id, payload.email),
        ).fetchone()

        if existing is not None:
            logger.info("Blocked duplicate application: email=%s, internship_id=%d", payload.email, internship_id)
            return error_response(
                409,
                "DUPLICATE_APPLICATION",
                f"An application from {payload.email} for this internship already exists.",
                details=[{"field": "email", "message": "Duplicate application not allowed"}],
            )

        cur = conn.execute(
            """INSERT INTO applications
               (internship_id, full_name, email, phone, resume_url, cover_letter)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                internship_id,
                payload.full_name,
                payload.email,
                payload.phone,
                payload.resume_url,
                payload.cover_letter or "",
            ),
        )
        app_id = cur.lastrowid
        app_row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()

    logger.info("Successfully recorded application #%d from %s for internship #%d", app_id, payload.email, internship_id)
    response.headers["Location"] = f"/internships/{internship_id}/applications/{app_id}"
    return {
        "data": {
            "id": app_row["id"],
            "internship_id": app_row["internship_id"],
            "internship_title": internship["title"],
            "company": internship["company"],
            "full_name": app_row["full_name"],
            "email": app_row["email"],
            "phone": app_row["phone"],
            "resume_url": app_row["resume_url"],
            "created_at": app_row["created_at"],
            "message": "Application submitted successfully! Your application reference number is #" + str(app_id),
        }
    }


@app.get("/internships/{internship_id}/applications", tags=["Applications"])
def list_internship_applications(internship_id: int):
    with db.get_conn() as conn:
        if fetch_one(conn, internship_id) is None:
            return not_found(internship_id)
        rows = conn.execute(
            "SELECT * FROM applications WHERE internship_id = ? ORDER BY id DESC",
            (internship_id,),
        ).fetchall()
    return {"data": [dict(r) for r in rows], "meta": {"total": len(rows)}}


@app.get("/applications/my", tags=["Applications"])
def list_my_applications(email: str = Query(..., min_length=5, max_length=120)):
    """Retrieve all submitted applications for an applicant email."""
    with db.get_conn() as conn:
        rows = conn.execute(
            """SELECT a.*, i.title, i.company, i.location, i.work_mode
               FROM applications a
               JOIN internships i ON a.internship_id = i.id
               WHERE a.email = ?
               ORDER BY a.id DESC""",
            (email.strip().lower(),),
        ).fetchall()
    return {"data": [dict(r) for r in rows], "meta": {"total": len(rows)}}


# ---------- Frontend Static Files Mounting ----------
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "InternHub API is online. Visit /docs for Swagger UI documentation."}
