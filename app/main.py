"""InternshipChesko Production Application
Features:
- Dual Panels: Intern Dashboard (Tasks, Submissions, Verified Certificate) & Admin Dashboard (Metrics, Candidates, Reviews, Certificate Controls)
- Structured request logging, multi-stage health probes, security headers, rate limiting, and parameterized queries.
"""
import json
import logging
import random
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from . import db
from .limiter import rate_limiter
from .schemas import (
    ApplicationCreate,
    CertificateIssue,
    InternshipCreate,
    InternshipPatch,
    InternshipReplace,
    TaskReview,
    TaskSubmit,
    UserRegister,
)

# Configure structured application logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("internshipchesko.api")

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
    logger.info("Initializing database schema and seed data...")
    ensure_db()
    yield
    logger.info("InternshipChesko server shutting down cleanly.")


app = FastAPI(
    title="InternshipChesko Platform API",
    version="3.0.0",
    description="Full-stack Internship Platform with Intern Portal, Admin Operations, Task Submissions, and Certificate Issuance.",
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
    ensure_db()
    uptime_sec = round(time.time() - START_TIME, 2)
    db_metrics = db.get_db_stats()
    return {
        "status": "healthy",
        "service": "internshipchesko-platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_sec,
        "database": db_metrics,
        "environment": "production-ready",
    }


@app.get("/health/ready", tags=["Health"])
def readiness_check():
    try:
        with db.get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"ready": True}
    except Exception as e:
        logger.error("Readiness probe failed: %s", str(e))
        return JSONResponse(status_code=503, content={"ready": False, "reason": str(e)})


@app.get("/health/live", tags=["Health"])
def liveness_check():
    return {"alive": True}


# ---------- 1. User & Auth Endpoints (Intern Registration & Login) ----------
@app.post("/auth/register", tags=["Auth"])
def register_or_login(payload: UserRegister):
    """
    Registers a new intern or logs in existing user by email.
    Returns user profile with ID and role.
    """
    ensure_db()
    with db.get_conn() as conn:
        existing = conn.execute("SELECT * FROM users WHERE email = ?", (payload.email,)).fetchone()
        if existing:
            # Update phone / college / domain if changed
            conn.execute(
                """UPDATE users SET name = ?, phone = ?, college = ?, domain = ? WHERE id = ?""",
                (payload.name, payload.phone or existing["phone"], payload.college, payload.domain, existing["id"]),
            )
            user_row = conn.execute("SELECT * FROM users WHERE id = ?", (existing["id"],)).fetchone()
            logger.info("User login: %s (%s)", user_row["email"], user_row["role"])
            return {"data": dict(user_row), "message": "Welcome back to InternshipChesko!"}

        # Create new user
        cur = conn.execute(
            """INSERT INTO users (name, email, phone, college, domain, role)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (payload.name, payload.email, payload.phone, payload.college, payload.domain, payload.role),
        )
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        logger.info("New intern registered: #%d %s (%s)", user_row["id"], user_row["name"], user_row["email"])
        return {"data": dict(user_row), "message": "Registration successful! Welcome to InternshipChesko 🎯"}


@app.get("/users/{user_id}", tags=["Auth"])
def get_user_profile(user_id: int):
    ensure_db()
    with db.get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return error_response(404, "NOT_FOUND", "User profile not found")
    return {"data": dict(user)}


# ---------- 2. Intern Task Milestone & Submission Endpoints ----------
@app.get("/tasks", tags=["Tasks"])
def list_milestone_tasks():
    ensure_db()
    with db.get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY task_num ASC").fetchall()
    return {"data": [dict(r) for r in rows]}


@app.get("/users/{user_id}/tasks", tags=["Tasks"])
def get_user_task_milestones(user_id: int):
    """
    Returns the 5 milestone tasks combined with the intern's submission status.
    Computes progress percentage and checks if Certificate is unlocked.
    """
    ensure_db()
    with db.get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return error_response(404, "NOT_FOUND", "User not found")

        tasks = conn.execute("SELECT * FROM tasks ORDER BY task_num ASC").fetchall()
        submissions = conn.execute(
            "SELECT * FROM task_submissions WHERE user_id = ?", (user_id,)
        ).fetchall()
        sub_map = {s["task_id"]: dict(s) for s in submissions}

        combined = []
        approved_count = 0
        for t in tasks:
            task_dict = dict(t)
            sub = sub_map.get(t["id"])
            if sub:
                task_dict["submission_status"] = sub["status"]
                task_dict["submission_url"] = sub["submission_url"]
                task_dict["submission_notes"] = sub["notes"]
                task_dict["submission_feedback"] = sub["feedback"]
                task_dict["submitted_at"] = sub["submitted_at"]
                task_dict["reviewed_at"] = sub["reviewed_at"]
                if sub["status"] == "approved":
                    approved_count += 1
            else:
                task_dict["submission_status"] = "not_submitted"
                task_dict["submission_url"] = ""
                task_dict["submission_notes"] = ""
                task_dict["submission_feedback"] = ""
                task_dict["submitted_at"] = None
                task_dict["reviewed_at"] = None

            combined.append(task_dict)

        total_tasks = len(tasks) or 5
        progress_pct = int((approved_count / total_tasks) * 100)

        # Check existing certificate
        cert = conn.execute("SELECT * FROM certificates WHERE user_id = ?", (user_id,)).fetchone()

    return {
        "data": {
            "user": dict(user),
            "tasks": combined,
            "progress_percent": progress_pct,
            "approved_count": approved_count,
            "total_tasks": total_tasks,
            "certificate_unlocked": approved_count == total_tasks,
            "certificate": dict(cert) if cert else None,
        }
    }


@app.post("/users/{user_id}/tasks/{task_id}/submit", status_code=201, tags=["Tasks"])
def submit_task_solution(user_id: int, task_id: int, payload: TaskSubmit):
    """Intern submits a task milestone proof link (GitHub / Live deploy)."""
    ensure_db()
    with db.get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return error_response(404, "NOT_FOUND", "User not found")
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return error_response(404, "NOT_FOUND", "Task not found")

        # Upsert submission
        existing = conn.execute(
            "SELECT id, status FROM task_submissions WHERE user_id = ? AND task_id = ?",
            (user_id, task_id),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE task_submissions
                   SET submission_url = ?, notes = ?, status = 'pending', submitted_at = (strftime('%Y-%m-%dT%H:%M:%SZ','now')), reviewed_at = NULL
                   WHERE id = ?""",
                (payload.submission_url, payload.notes or "", existing["id"]),
            )
            sub_id = existing["id"]
        else:
            cur = conn.execute(
                """INSERT INTO task_submissions (user_id, task_id, submission_url, notes, status)
                   VALUES (?, ?, ?, ?, 'pending')""",
                (user_id, task_id, payload.submission_url, payload.notes or ""),
            )
            sub_id = cur.lastrowid

        sub_row = conn.execute("SELECT * FROM task_submissions WHERE id = ?", (sub_id,)).fetchone()

    logger.info("Intern #%d submitted Task #%d: %s", user_id, task_id, payload.submission_url)
    return {
        "data": dict(sub_row),
        "message": f"{task['title']} submitted successfully for review! An admin will review it shortly.",
    }


# ---------- 3. Admin Panel Endpoints (Review Submissions & Management) ----------
@app.get("/admin/metrics", tags=["Admin"])
def get_admin_metrics():
    """Returns dashboard metrics for the administrator."""
    ensure_db()
    with db.get_conn() as conn:
        interns_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'intern'").fetchone()[0]
        applications_count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        internships_count = conn.execute("SELECT COUNT(*) FROM internships").fetchone()[0]
        pending_reviews = conn.execute("SELECT COUNT(*) FROM task_submissions WHERE status = 'pending'").fetchone()[0]
        certificates_count = conn.execute("SELECT COUNT(*) FROM certificates").fetchone()[0]

    return {
        "data": {
            "total_interns": interns_count,
            "total_applications": applications_count,
            "total_internships": internships_count,
            "pending_task_reviews": pending_reviews,
            "certificates_issued": certificates_count,
        }
    }


@app.get("/admin/interns", tags=["Admin"])
def list_admin_interns():
    """Lists all registered interns with task completion counts and certificate status."""
    ensure_db()
    with db.get_conn() as conn:
        interns = conn.execute(
            """SELECT u.*,
                      (SELECT COUNT(*) FROM task_submissions ts WHERE ts.user_id = u.id AND ts.status = 'approved') AS approved_tasks,
                      (SELECT COUNT(*) FROM certificates c WHERE c.user_id = u.id) AS has_certificate
               FROM users u
               WHERE u.role = 'intern'
               ORDER BY u.id DESC"""
        ).fetchall()
    return {"data": [dict(i) for i in interns]}


@app.get("/admin/submissions", tags=["Admin"])
def list_admin_submissions(status: Optional[str] = None):
    """Lists all intern task submissions for administrator review."""
    ensure_db()
    where = f"WHERE ts.status = '{status}'" if status else ""
    with db.get_conn() as conn:
        rows = conn.execute(
            f"""SELECT ts.*, u.name as intern_name, u.email as intern_email, u.college, u.domain,
                       t.task_num, t.title as task_title
                FROM task_submissions ts
                JOIN users u ON ts.user_id = u.id
                JOIN tasks t ON ts.task_id = t.id
                {where}
                ORDER BY ts.id DESC"""
        ).fetchall()
    return {"data": [dict(r) for r in rows]}


@app.post("/admin/submissions/{submission_id}/review", tags=["Admin"])
def review_task_submission(submission_id: int, payload: TaskReview):
    """
    Admin approves or rejects a task submission.
    If all 5 tasks become approved, automatically generates the Verified Certificate!
    """
    ensure_db()
    with db.get_conn() as conn:
        sub = conn.execute("SELECT * FROM task_submissions WHERE id = ?", (submission_id,)).fetchone()
        if not sub:
            return error_response(404, "NOT_FOUND", "Submission not found")

        user_id = sub["user_id"]
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

        conn.execute(
            """UPDATE task_submissions
               SET status = ?, feedback = ?, reviewed_at = (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
               WHERE id = ?""",
            (payload.status, payload.feedback or "", submission_id),
        )

        logger.info("Admin reviewed submission #%d: status=%s", submission_id, payload.status)

        # Check if intern has now completed all 5 tasks
        approved_count = conn.execute(
            "SELECT COUNT(*) FROM task_submissions WHERE user_id = ? AND status = 'approved'",
            (user_id,),
        ).fetchone()[0]

        cert_issued = False
        cert_data = None

        if approved_count >= 5:
            existing_cert = conn.execute("SELECT * FROM certificates WHERE user_id = ?", (user_id,)).fetchone()
            if not existing_cert:
                cert_id = f"IC-2026-{random.randint(10000, 99999)}"
                start_date = "2026-09-01"
                completion_date = datetime.now().strftime("%Y-%m-%d")
                conn.execute(
                    """INSERT INTO certificates
                       (certificate_id, user_id, intern_name, college, domain, internship_title, company, start_date, completion_date, grade)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Outstanding (A+)')""",
                    (
                        cert_id,
                        user_id,
                        user["name"],
                        user["college"],
                        user["domain"],
                        f"{user['domain']} Engineering Internship",
                        "InternshipChesko Tech Labs",
                        start_date,
                        completion_date,
                    ),
                )
                existing_cert = conn.execute("SELECT * FROM certificates WHERE certificate_id = ?", (cert_id,)).fetchone()
                cert_issued = True
                logger.info("🎉 Certificate %s automatically issued to %s!", cert_id, user["name"])

            cert_data = dict(existing_cert)

    return {
        "data": {
            "submission_id": submission_id,
            "status": payload.status,
            "approved_count": approved_count,
            "certificate_issued": cert_issued,
            "certificate": cert_data,
        },
        "message": f"Submission marked as {payload.status}."
        + (" 🎉 All tasks completed! Official Certificate has been issued!" if cert_issued else ""),
    }


# ---------- 4. Verified Certificate Endpoints ----------
@app.get("/certificates/{certificate_id}", tags=["Certificates"])
def get_verified_certificate(certificate_id: str):
    """Public verification lookup for an issued internship certificate."""
    ensure_db()
    with db.get_conn() as conn:
        cert = conn.execute(
            "SELECT * FROM certificates WHERE certificate_id = ?",
            (certificate_id.strip().upper(),),
        ).fetchone()

        if not cert:
            return error_response(404, "NOT_FOUND", f"Certificate '{certificate_id}' is not recognized or verified.")

    return {
        "data": {
            **dict(cert),
            "verification_status": "VERIFIED & AUTHENTIC",
            "issuer": "InternshipChesko Certification Board",
            "accreditation": "EdVyro Educational Technologies Partner Network",
        }
    }


@app.get("/users/{user_id}/certificate", tags=["Certificates"])
def get_user_certificate(user_id: int):
    """Retrieve the certificate for a specific user."""
    ensure_db()
    with db.get_conn() as conn:
        cert = conn.execute("SELECT * FROM certificates WHERE user_id = ?", (user_id,)).fetchone()
        if not cert:
            return error_response(404, "NOT_FOUND", "No certificate has been issued for this user yet.")
    return {"data": dict(cert)}


@app.post("/admin/certificates/issue", status_code=201, tags=["Certificates"])
def issue_certificate_manual(payload: CertificateIssue):
    """Admin manual certificate issuance."""
    ensure_db()
    with db.get_conn() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (payload.user_id,)).fetchone()
        if not user:
            return error_response(404, "NOT_FOUND", "User not found")

        existing = conn.execute("SELECT * FROM certificates WHERE user_id = ?", (payload.user_id,)).fetchone()
        if existing:
            return {"data": dict(existing), "message": "Certificate already exists for this intern."}

        cert_id = f"IC-2026-{random.randint(10000, 99999)}"
        conn.execute(
            """INSERT INTO certificates
               (certificate_id, user_id, intern_name, college, domain, internship_title, company, start_date, completion_date, grade)
               VALUES (?, ?, ?, ?, ?, ?, ?, '2026-09-01', ?, ?)""",
            (
                cert_id,
                payload.user_id,
                user["name"],
                user["college"],
                user["domain"],
                payload.internship_title,
                payload.company,
                datetime.now().strftime("%Y-%m-%d"),
                payload.grade,
            ),
        )
        cert_row = conn.execute("SELECT * FROM certificates WHERE certificate_id = ?", (cert_id,)).fetchone()

    logger.info("Manual certificate issued: %s to %s", cert_id, user["name"])
    return {"data": dict(cert_row), "message": f"Certificate {cert_id} successfully issued to {user['name']}!"}


# ---------- 5. Internship Listings & Applications (Core Features) ----------
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
    ensure_db()
    with db.get_conn() as conn:
        row = fetch_one(conn, internship_id)
    if row is None:
        return not_found(internship_id)
    return {"data": row}


@app.post("/internships", status_code=201, tags=["Internships"])
def create_internship(payload: InternshipCreate, response: Response):
    ensure_db()
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
    ensure_db()
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
    ensure_db()
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
    ensure_db()
    with db.get_conn() as conn:
        cur = conn.execute("DELETE FROM internships WHERE id = ?", (internship_id,))
    if cur.rowcount == 0:
        return not_found(internship_id)
    logger.info("Deleted internship #%d", internship_id)
    return Response(status_code=204)


@app.post("/internships/{internship_id}/apply", status_code=201, tags=["Applications"])
def submit_application(internship_id: int, payload: ApplicationCreate, request: Request, response: Response):
    ensure_db()
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_key = f"apply:{client_ip}"

    allowed, retry_after = rate_limiter.is_allowed(rate_key, max_requests=5, window_seconds=60)
    if not allowed:
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

        existing = conn.execute(
            "SELECT id FROM applications WHERE internship_id = ? AND email = ?",
            (internship_id, payload.email),
        ).fetchone()

        if existing is not None:
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
            "message": "Application submitted successfully! Reference number: #" + str(app_id),
        }
    }


@app.get("/internships/{internship_id}/applications", tags=["Applications"])
def list_internship_applications(internship_id: int):
    ensure_db()
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
    ensure_db()
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
        return HTMLResponse(index_file.read_text(encoding="utf-8"))
    return {"message": "InternshipChesko API is online. Visit /docs for Swagger UI documentation."}
