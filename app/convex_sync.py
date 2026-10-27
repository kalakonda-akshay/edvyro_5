"""Convex Cloud Database Synchronization Module
Connects InternshipChesko to Convex Deployment: harmless-axolotl-105
Endpoint: https://harmless-axolotl-105.convex.cloud
"""
import json
import logging
import os
import threading
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("internshipchesko.convex")

CONVEX_URL = os.environ.get("CONVEX_URL", "https://harmless-axolotl-105.convex.cloud")
CONVEX_DEPLOY_KEY = os.environ.get("CONVEX_DEPLOY_KEY", "dev:harmless-axolotl-105|eyJ2MiI6IjlmODhiZjBkZTAzNjQ4ZjQ5MWE2YTg2YTRiMGMwMTgzIn0=")


def call_convex_mutation(path: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Execute a mutation against the Convex cloud deployment."""
    endpoint = f"{CONVEX_URL.rstrip('/')}/api/mutation"
    payload = json.dumps({"path": path, "args": args}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except Exception as e:
        logger.warning("Convex sync non-blocking error on %s: %s", path, str(e))
        return None


def call_convex_query(path: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Execute a query against the Convex cloud deployment."""
    endpoint = f"{CONVEX_URL.rstrip('/')}/api/query"
    payload = json.dumps({"path": path, "args": args}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5.0) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except Exception as e:
        logger.warning("Convex query non-blocking error on %s: %s", path, str(e))
        return None


def sync_record_to_convex_async(table: str, data: Dict[str, Any]) -> None:
    """Asynchronously sync a record to Convex without blocking request thread."""
    def _run():
        clean_data = {}
        for k, v in data.items():
            if k == "id":
                continue  # Convex provides its own _id
            if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
                try:
                    clean_data[k] = json.loads(v)
                except Exception:
                    clean_data[k] = v
            else:
                clean_data[k] = v
        call_convex_mutation("records:insertRecord", {"table": table, "data": clean_data})

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def sync_all_from_sqlite(conn) -> Dict[str, int]:
    """Batch synchronizes all tables from SQLite to Convex Cloud DB."""
    tables = [
        "internships",
        "users",
        "applications",
        "offers",
        "linkedin_proofs",
        "screening_quizzes",
        "quiz_submissions",
        "tasks",
        "task_submissions",
        "weekly_reports",
        "final_projects",
        "certificates",
        "in_app_notifications",
        "audit_logs",
    ]

    synced_counts = {}

    for tbl in tables:
        try:
            rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
            records = []
            for r in rows:
                d = dict(r)
                d.pop("id", None)
                for k, v in list(d.items()):
                    if isinstance(v, str) and (v.startswith("[") or v.startswith("{")):
                        try:
                            d[k] = json.loads(v)
                        except Exception:
                            pass
                records.append(d)

            if records:
                call_convex_mutation("records:batchSync", {"table": tbl, "records": records})
            synced_counts[tbl] = len(records)
        except Exception as e:
            logger.error("Error syncing table %s to Convex: %s", tbl, str(e))
            synced_counts[tbl] = 0

    return synced_counts


def restore_users_from_convex(conn) -> int:
    """Restores any missing users from Convex into local SQLite on cold starts."""
    restored = 0
    try:
        res = call_convex_query("records:listTable", {"table": "users"})
        if res and res.get("status") == "success":
            users = res.get("value", [])
            for u in users:
                email = (u.get("email") or "").strip().lower()
                if not email:
                    continue
                existing = conn.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO users (name, email, phone, college, domain, role, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            u.get("name", "Intern User"),
                            email,
                            u.get("phone", ""),
                            u.get("college", ""),
                            u.get("domain", "Full Stack Web Development"),
                            u.get("role", "intern"),
                            u.get("created_at", "2026-10-27T00:00:00Z"),
                        ),
                    )
                    restored += 1
            if restored > 0:
                conn.commit()
                logger.info("Restored %d user(s) from Convex Cloud DB.", restored)
    except Exception as e:
        logger.warning("Error restoring users from Convex: %s", str(e))
    return restored


def get_convex_status() -> Dict[str, Any]:
    """Check connectivity to Convex cloud deployment."""
    test = call_convex_query("records:listTable", {"table": "audit_logs"})
    is_live = test is not None and test.get("status") == "success"
    return {
        "status": "connected" if is_live else "error",
        "deployment": "harmless-axolotl-105",
        "convex_url": CONVEX_URL,
        "is_live": is_live,
    }
