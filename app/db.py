import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parent.parent
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/internships.db"
else:
    DB_PATH = os.environ.get("DB_PATH", str(ROOT / "internships.db"))

DEFAULT_TASKS = [
    {
        "task_num": 1,
        "title": "Task 1: Interactive Frontend Interface",
        "objective": "Build responsive UI components, search filtering, and client-side validation.",
        "deliverable": "Working web UI with search, work-mode filter, and application modal.",
        "guide_url": "https://github.com/kalakonda-akshay/internship-board"
    },
    {
        "task_num": 2,
        "title": "Task 2: RESTful API & Backend Service",
        "objective": "Develop FastAPI / Python backend service with full CRUD operations and structured schemas.",
        "deliverable": "API endpoints for listing, details, creation, and updating internships.",
        "guide_url": "https://github.com/kalakonda-akshay/edvyro_3"
    },
    {
        "task_num": 3,
        "title": "Task 3: Database Modeling & Data Persistence",
        "objective": "Design normalized SQLite schema with foreign keys, seed data, and query indexing.",
        "deliverable": "SQLite database persistence with automated seed scripts and migration checks.",
        "guide_url": "https://github.com/kalakonda-akshay/edvyro_3"
    },
    {
        "task_num": 4,
        "title": "Task 4: Security, Rate Limiting & Validation",
        "objective": "Implement defense-in-depth security headers, sliding-window rate limiting, and parameterized queries.",
        "deliverable": "Secured endpoints, test suite, and security checklist report.",
        "guide_url": "https://github.com/kalakonda-akshay/edvyro_4"
    },
    {
        "task_num": 5,
        "title": "Task 5: Production Capstone & Certificate Verification",
        "objective": "Deploy polished full-stack portal with logging, health probes, candidate tracking, and verified certificates.",
        "deliverable": "Live production application, QA report, and certificate engine.",
        "guide_url": "https://github.com/kalakonda-akshay/edvyro_5"
    }
]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
    except Exception:
        pass
    return conn


def init_db() -> None:
    """Initialize SQLite database with complete schema."""
    schema_file = ROOT / "schema.sql"
    if schema_file.exists():
        with get_conn() as conn:
            conn.executescript(schema_file.read_text(encoding="utf-8"))


def seed_db(reset: bool = False) -> int:
    """Seed sample data, default milestones, and default admin."""
    init_db()
    with get_conn() as conn:
        if reset:
            conn.execute("DELETE FROM certificates")
            conn.execute("DELETE FROM task_submissions")
            conn.execute("DELETE FROM tasks")
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM applications")
            conn.execute("DELETE FROM internships")
            conn.execute("DELETE FROM sqlite_sequence")

        # 1. Seed Internships
        seed_file = ROOT / "data" / "seed.json"
        internship_count = conn.execute("SELECT COUNT(*) FROM internships").fetchone()[0]
        if internship_count == 0 and seed_file.exists():
            records = json.loads(seed_file.read_text(encoding="utf-8"))
            conn.executemany(
                """INSERT INTO internships
                   (title, company, category, location, work_mode, duration, stipend, skills, description, deadline, status)
                   VALUES (:title, :company, :category, :location, :work_mode, :duration, :stipend, :skills, :description, :deadline, :status)""",
                records,
            )

        # 2. Seed Tasks (Tasks 1-5)
        task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if task_count == 0:
            conn.executemany(
                """INSERT INTO tasks (task_num, title, objective, deliverable, guide_url)
                   VALUES (:task_num, :title, :objective, :deliverable, :guide_url)""",
                DEFAULT_TASKS,
            )

        # 3. Seed Default Admin User
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if admin_count == 0:
            conn.execute(
                """INSERT INTO users (name, email, phone, college, domain, role)
                   VALUES ('Admin Director', 'admin@internshipchesko.com', '+91 9876500000', 'InternshipChesko HQ', 'Platform Operations', 'admin')"""
            )

        return conn.execute("SELECT COUNT(*) FROM internships").fetchone()[0]


def get_db_stats() -> Dict[str, Any]:
    """Provide health probe statistics regarding the database."""
    start = time.perf_counter()
    with get_conn() as conn:
        internships_count = conn.execute("SELECT COUNT(*) FROM internships").fetchone()[0]
        applications_count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        certificates_count = conn.execute("SELECT COUNT(*) FROM certificates").fetchone()[0]
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "status": "healthy",
        "internships_count": internships_count,
        "applications_count": applications_count,
        "users_count": users_count,
        "certificates_count": certificates_count,
        "query_latency_ms": latency_ms,
    }


if __name__ == "__main__":
    n = seed_db(reset=True)
    print(f"Database initialized and seeded: {n} internships into {DB_PATH}")
