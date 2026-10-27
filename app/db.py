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

DEFAULT_SCREENING_QUIZ = {
    "track": "Full Stack Web Development",
    "title": "Full Stack & Backend Screening Assessment",
    "time_limit_mins": 15,
    "pass_cutoff": 70,
    "questions": json.dumps([
        {
            "id": 1,
            "question": "Which HTTP status code is most appropriate for a resource that has been successfully created?",
            "options": ["200 OK", "201 Created", "204 No Content", "301 Moved Permanently"],
            "answer": 1
        },
        {
            "id": 2,
            "question": "What is the primary advantage of SQLite Write-Ahead Logging (WAL) mode?",
            "options": [
                "Disables foreign keys for speed",
                "Allows concurrent readers without blocking writers",
                "Encrypts data at rest automatically",
                "Compresses tables into zip archives"
            ],
            "answer": 1
        },
        {
            "id": 3,
            "question": "In REST API design, which HTTP method should be idempotent and used to replace an entire resource representation?",
            "options": ["POST", "PATCH", "PUT", "DELETE"],
            "answer": 2
        },
        {
            "id": 4,
            "question": "What security header prevents MIME-sniffing vulnerabilities in modern browsers?",
            "options": [
                "X-Content-Type-Options: nosniff",
                "X-Frame-Options: DENY",
                "Content-Security-Policy",
                "Strict-Transport-Security"
            ],
            "answer": 0
        },
        {
            "id": 5,
            "question": "In Python FastAPI / Pydantic, what is the best way to prevent mass-assignment attacks on request models?",
            "options": [
                "extra = 'allow'",
                "extra = 'forbid'",
                "strict = False",
                "ignore_extra = True"
            ],
            "answer": 1
        }
    ])
}


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
    """Seed sample data, default milestones, users, and screening quizzes."""
    init_db()
    with get_conn() as conn:
        if reset:
            conn.execute("DELETE FROM audit_logs")
            conn.execute("DELETE FROM in_app_notifications")
            conn.execute("DELETE FROM certificates")
            conn.execute("DELETE FROM final_projects")
            conn.execute("DELETE FROM weekly_reports")
            conn.execute("DELETE FROM task_submissions")
            conn.execute("DELETE FROM tasks")
            conn.execute("DELETE FROM quiz_submissions")
            conn.execute("DELETE FROM screening_quizzes")
            conn.execute("DELETE FROM linkedin_proofs")
            conn.execute("DELETE FROM offers")
            conn.execute("DELETE FROM applications")
            conn.execute("DELETE FROM users")
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

        # 3. Seed Screening Quiz
        quiz_count = conn.execute("SELECT COUNT(*) FROM screening_quizzes").fetchone()[0]
        if quiz_count == 0:
            conn.execute(
                """INSERT INTO screening_quizzes (track, title, time_limit_mins, pass_cutoff, questions)
                   VALUES (:track, :title, :time_limit_mins, :pass_cutoff, :questions)""",
                DEFAULT_SCREENING_QUIZ,
            )

        # 4. Seed Default Users (Admin, Mentor, Intern)
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        if admin_count == 0:
            conn.execute(
                """INSERT INTO users (name, email, phone, college, domain, role)
                   VALUES ('Admin Director', 'admin@internshipchesko.com', '+91 9876500000', 'InternshipChesko HQ', 'Platform Operations', 'admin')"""
            )

        mentor_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'mentor'").fetchone()[0]
        if mentor_count == 0:
            conn.execute(
                """INSERT INTO users (name, email, phone, college, domain, role)
                   VALUES ('Dr. Ramesh Mentor', 'mentor@example.com', '+91 9876511111', 'IIT Hyderabad', 'Engineering Mentorship', 'mentor')"""
            )

        intern_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'intern'").fetchone()[0]
        if intern_count == 0:
            cur = conn.execute(
                """INSERT INTO users (name, email, phone, college, domain, role)
                   VALUES ('Akshay Kalakonda', 'intern@example.com', '+91 9876543210', 'Osmania University College of Engineering', 'Full Stack Web Development', 'intern')"""
            )
            intern_id = cur.lastrowid

            # Also seed personal intern account
            conn.execute(
                """INSERT OR IGNORE INTO users (name, email, phone, college, domain, role)
                   VALUES ('AKSHAY KALAKONDA', 'akshaykalakonda9@gmail.com', '9390093424', 'AMRITA VISWA VIDYAPEETHAM', 'Full Stack Web Development', 'intern')"""
            )

            # Create sample application and offer for the demo intern
            first_internship = conn.execute("SELECT id, title, company FROM internships LIMIT 1").fetchone()
            if first_internship:
                app_cur = conn.execute(
                    """INSERT INTO applications
                       (internship_id, full_name, email, phone, college, resume_url, skills_tags, consent_given, consent_ip, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1, '127.0.0.1', 'Offered')""",
                    (
                        first_internship["id"],
                        "Akshay Kalakonda",
                        "intern@example.com",
                        "+91 9876543210",
                        "Osmania University College of Engineering",
                        "https://drive.google.com/file/d/demo-resume/view",
                        json.dumps(["Python", "FastAPI", "React", "SQLite"]),
                    ),
                )
                app_id = app_cur.lastrowid
                conn.execute(
                    """INSERT INTO offers
                       (offer_id, application_id, user_id, intern_name, track, batch, duration, start_date, end_date, stipend_amount, mentor_name, signatory_name, status, expires_at)
                       VALUES ('OFF-2026-90412', ?, ?, 'Akshay Kalakonda', 'Full Stack Web Development', '2026-B1', '3 Months', '2026-09-01', '2026-11-30', 15000, 'Dr. Ramesh Mentor', 'Program Director', 'Offered', '2026-12-31')""",
                    (app_id, intern_id),
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
        offers_count = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "status": "healthy",
        "internships_count": internships_count,
        "applications_count": applications_count,
        "users_count": users_count,
        "certificates_count": certificates_count,
        "offers_count": offers_count,
        "query_latency_ms": latency_ms,
    }


if __name__ == "__main__":
    n = seed_db(reset=True)
    print(f"Database initialized and seeded: {n} internships into {DB_PATH}")

