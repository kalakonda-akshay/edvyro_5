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


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # Production SQLite optimizations
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
    """Seed sample data from seed.json if the database is unpopulated."""
    init_db()
    seed_file = ROOT / "data" / "seed.json"
    if not seed_file.exists():
        return 0

    records = json.loads(seed_file.read_text(encoding="utf-8"))
    with get_conn() as conn:
        if reset:
            conn.execute("DELETE FROM applications")
            conn.execute("DELETE FROM internships")
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('internships', 'applications')")

        count = conn.execute("SELECT COUNT(*) FROM internships").fetchone()[0]
        if count > 0:
            return 0

        conn.executemany(
            """INSERT INTO internships
               (title, company, category, location, work_mode, duration, stipend, skills, description, deadline, status)
               VALUES (:title, :company, :category, :location, :work_mode, :duration, :stipend, :skills, :description, :deadline, :status)""",
            records,
        )
    return len(records)


def get_db_stats() -> Dict[str, Any]:
    """Provide health probe statistics regarding the database."""
    start = time.perf_counter()
    with get_conn() as conn:
        internships_count = conn.execute("SELECT COUNT(*) FROM internships").fetchone()[0]
        applications_count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "status": "healthy",
        "internships_count": internships_count,
        "applications_count": applications_count,
        "query_latency_ms": latency_ms,
    }


if __name__ == "__main__":
    n = seed_db(reset=True)
    print(f"Seeded {n} capstone internships into {DB_PATH}")
