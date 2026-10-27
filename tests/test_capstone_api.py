"""Capstone Automated Test Suite - Production Quality Assurance.
Validates multi-stage health probes, security headers, logging telemetry,
rate limiting, application tracking, and SQL injection immunity.
"""
import os
import tempfile
import pytest

# Isolated SQLite database instance
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "capstone_test.db")

from fastapi.testclient import TestClient
from app.main import app
from app.limiter import rate_limiter

SAMPLE_APP = {
    "full_name": "Akshay Kalakonda",
    "email": "akshay.eng@example.com",
    "phone": "+91 9876543210",
    "resume_url": "https://github.com/kalakonda-akshay",
    "cover_letter": "Passionate about full-stack engineering and API security."
}


@pytest.fixture(autouse=True)
def clean_rate_limits():
    rate_limiter.reset()


def test_health_telemetry_and_probes():
    """Verify health diagnostic metrics, readiness, and liveness endpoints."""
    with TestClient(app) as client:
        # Full health check
        h = client.get("/health")
        assert h.status_code == 200
        body = h.json()
        assert body["status"] == "healthy"
        assert "uptime_seconds" in body
        assert body["database"]["status"] == "healthy"
        assert body["database"]["internships_count"] >= 5

        # Readiness
        r = client.get("/health/ready")
        assert r.status_code == 200
        assert r.json()["ready"] is True

        # Liveness
        lv = client.get("/health/live")
        assert lv.status_code == 200
        assert lv.json()["alive"] is True


def test_security_headers_and_response_time():
    """Verify production security headers and logging response time header."""
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        headers = res.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "default-src" in headers.get("Content-Security-Policy", "")
        assert "X-Response-Time-Ms" in headers


def test_list_and_filter_internships():
    """Verify multi-facet filtering (category, work mode, search keyword)."""
    with TestClient(app) as client:
        # All
        r = client.get("/internships")
        assert r.status_code == 200
        assert r.json()["meta"]["total"] >= 5

        # Category filter
        r_cat = client.get("/internships?category=Web+Development")
        assert r_cat.status_code == 200
        assert all(i["category"] == "Web Development" for i in r_cat.json()["data"])

        # Search query
        r_q = client.get("/internships?q=Python")
        assert r_q.status_code == 200
        assert len(r_q.json()["data"]) > 0


def test_application_submission_lifecycle():
    """Verify application submission, duplicate prevention, and candidate lookup."""
    with TestClient(app) as client:
        open_roles = client.get("/internships?status=open").json()["data"]
        target_role = open_roles[0]
        role_id = target_role["id"]

        # 1. Valid Application
        res = client.post(f"/internships/{role_id}/apply", json=SAMPLE_APP)
        assert res.status_code == 201
        data = res.json()["data"]
        assert data["email"] == SAMPLE_APP["email"]
        assert "Location" in res.headers
        app_id = data["id"]

        # 2. Duplicate Submission Blocked
        res_dup = client.post(f"/internships/{role_id}/apply", json=SAMPLE_APP)
        assert res_dup.status_code == 409
        assert res_dup.json()["error"]["code"] == "DUPLICATE_APPLICATION"

        # 3. Applicant Status Tracking ("My Applications")
        my_res = client.get(f"/applications/my?email={SAMPLE_APP['email']}")
        assert my_res.status_code == 200
        my_apps = my_res.json()["data"]
        assert any(a["id"] == app_id for a in my_apps)


def test_closed_internship_rejection():
    """Ensure applicants cannot submit applications to closed positions."""
    with TestClient(app) as client:
        closed = client.get("/internships?status=closed").json()["data"]
        assert len(closed) > 0
        closed_id = closed[0]["id"]

        res = client.post(f"/internships/{closed_id}/apply", json={
            **SAMPLE_APP,
            "email": "candidate.closed@example.com"
        })
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "INTERNSHIP_CLOSED"


def test_validation_rules_on_application():
    """Ensure strict validation rejects bad email, phone, and resume formats."""
    with TestClient(app) as client:
        open_roles = client.get("/internships?status=open").json()["data"]
        target_id = open_roles[0]["id"]

        # Malformed Email
        assert client.post(f"/internships/{target_id}/apply", json={**SAMPLE_APP, "email": "bademail"}).status_code == 400

        # Invalid Phone (<7 digits)
        assert client.post(f"/internships/{target_id}/apply", json={**SAMPLE_APP, "phone": "123"}).status_code == 400

        # Non-HTTP Resume URL
        assert client.post(f"/internships/{target_id}/apply", json={**SAMPLE_APP, "resume_url": "ftp://badurl.com"}).status_code == 400

        # Short Name
        assert client.post(f"/internships/{target_id}/apply", json={**SAMPLE_APP, "full_name": "X"}).status_code == 400


def test_rate_limiter_enforcement():
    """Ensure client cannot submit more than 5 applications within 60 seconds."""
    with TestClient(app) as client:
        open_roles = client.get("/internships?status=open").json()["data"]
        target_id = open_roles[0]["id"]

        for i in range(5):
            res = client.post(f"/internships/{target_id}/apply", json={
                **SAMPLE_APP,
                "email": f"applicant_{i}@example.com"
            })
            assert res.status_code == 201

        # 6th attempt must trigger 429
        res_limit = client.post(f"/internships/{target_id}/apply", json={
            **SAMPLE_APP,
            "email": "applicant_over@example.com"
        })
        assert res_limit.status_code == 429
        assert res_limit.json()["error"]["code"] == "RATE_LIMITED"
        assert "Retry-After" in res_limit.headers


def test_parameterized_query_sql_injection_defense():
    """Ensure malicious query strings are safely parameterized."""
    with TestClient(app) as client:
        payload = "' UNION SELECT * FROM applications --"
        res = client.get(f"/internships?q={payload}")
        assert res.status_code == 200
        assert res.json()["meta"]["total"] == 0


def test_crud_lifecycle():
    """Verify full administrative CRUD flow."""
    with TestClient(app) as client:
        new_internship = {
            "title": "Staff AI Engineer Intern",
            "company": "DeepMind Partner",
            "category": "Artificial Intelligence",
            "location": "Remote",
            "work_mode": "remote",
            "duration": 6,
            "stipend": 35000,
            "skills": ["Python", "Transformers", "PyTorch"],
            "description": "Research cutting edge LLM agents.",
            "deadline": "2026-12-31"
        }
        create_res = client.post("/internships", json=new_internship)
        assert create_res.status_code == 201
        created_id = create_res.json()["data"]["id"]

        # Patch
        patch_res = client.patch(f"/internships/{created_id}", json={"stipend": 40000})
        assert patch_res.status_code == 200
        assert patch_res.json()["data"]["stipend"] == 40000

        # Delete
        assert client.delete(f"/internships/{created_id}").status_code == 204
        assert client.get(f"/internships/{created_id}").status_code == 404


def test_intern_registration_and_task_milestones():
    """Verify intern registration, milestone listing, and progress tracking."""
    with TestClient(app) as client:
        # Register new intern
        reg_payload = {
            "name": "Kavya Reddy",
            "email": "kavya.test@example.com",
            "phone": "+91 9988776655",
            "college": "CBIT Hyderabad",
            "domain": "Full Stack Web Development",
            "role": "intern",
        }
        reg_res = client.post("/auth/register", json=reg_payload)
        assert reg_res.status_code == 200
        user_id = reg_res.json()["data"]["id"]

        # Check assigned tasks
        tasks_res = client.get(f"/users/{user_id}/tasks")
        assert tasks_res.status_code == 200
        tasks_data = tasks_res.json()["data"]
        assert len(tasks_data["tasks"]) == 5
        assert tasks_data["progress_percent"] == 0
        assert tasks_data["certificate_unlocked"] is False


def test_admin_review_workflow_and_certificate_auto_issuance():
    """Verify intern submits all 5 tasks, admin approves them, and Certificate is issued."""
    with TestClient(app) as client:
        # 1. Register intern
        user_res = client.post("/auth/register", json={
            "name": "Rohit Verma",
            "email": "rohit.complete@example.com",
            "college": "JNTU Hyderabad",
            "domain": "Cloud & DevOps",
            "role": "intern",
        })
        user_id = user_res.json()["data"]["id"]

        tasks = client.get("/tasks").json()["data"]
        assert len(tasks) == 5

        # 2. Submit all 5 tasks
        for t in tasks:
            submit_res = client.post(f"/users/{user_id}/tasks/{t['id']}/submit", json={
                "submission_url": f"https://github.com/rohit/task-{t['task_num']}",
                "notes": f"Completed deliverable for milestone {t['task_num']}"
            })
            assert submit_res.status_code == 201

        # 3. Admin reviews and approves all 5 submissions
        admin_subs = client.get("/admin/submissions").json()["data"]
        user_subs = [s for s in admin_subs if s["user_id"] == user_id]
        assert len(user_subs) == 5

        for s in user_subs:
            review_res = client.post(f"/admin/submissions/{s['id']}/review", json={
                "status": "approved",
                "feedback": "Excellent work and thorough tests!"
            })
            assert review_res.status_code == 200

        # 4. Verify Certificate is automatically generated
        cert_res = client.get(f"/users/{user_id}/certificate")
        assert cert_res.status_code == 200
        cert = cert_res.json()["data"]
        assert cert["user_id"] == user_id
        assert cert["intern_name"] == "Rohit Verma"
        assert cert["certificate_id"].startswith("IC-2026-")

        # 5. Public Certificate Verification endpoint
        verify_res = client.get(f"/certificates/{cert['certificate_id']}")
        assert verify_res.status_code == 200
        assert verify_res.json()["data"]["verification_status"] == "VERIFIED & AUTHENTIC"


def test_screening_quiz_and_telemetry():
    """Verify screening quiz retrieval, auto-grading, and anti-cheat tracking."""
    with TestClient(app) as client:
        # 1. Fetch questions without answers exposed
        q_res = client.get("/screening/quiz")
        assert q_res.status_code == 200
        quiz_data = q_res.json()["data"]
        assert len(quiz_data["questions"]) == 5
        assert "answer" not in quiz_data["questions"][0]

        # 2. Register candidate and submit quiz
        user_res = client.post("/auth/register", json={
            "name": "Screening Candidate",
            "email": "screening.candidate@example.com",
            "role": "intern",
        })
        user_id = user_res.json()["data"]["id"]

        submit_res = client.post(f"/users/{user_id}/screening/submit", json={
            "quiz_id": quiz_data["id"],
            "answers": {"1": 1, "2": 1, "3": 2, "4": 0, "5": 1},  # All correct answers
            "tab_switches": 2,
            "copy_paste_count": 1,
        })
        assert submit_res.status_code == 200
        sub_data = submit_res.json()["data"]
        assert sub_data["score"] == 100
        assert sub_data["passed"] == 1
        assert sub_data["tab_switches"] == 2

        # 3. Check screening record
        rec_res = client.get(f"/users/{user_id}/screening")
        assert rec_res.status_code == 200
        assert rec_res.json()["data"]["score"] == 100


def test_offer_letter_and_linkedin_proof_flow():
    """Verify offer letter creation, intern acceptance, and LinkedIn onboarding proof."""
    with TestClient(app) as client:
        # Register user
        user_res = client.post("/auth/register", json={
            "name": "Offer Candidate",
            "email": "offer.candidate@example.com",
            "college": "BITS Pilani",
            "role": "intern",
        })
        user_id = user_res.json()["data"]["id"]

        # Apply
        internships = client.get("/internships").json()["data"]
        app_res = client.post(f"/internships/{internships[0]['id']}/apply", json={
            "full_name": "Offer Candidate",
            "email": "offer.candidate@example.com",
            "phone": "+91 9123456789",
            "resume_url": "https://linkedin.com/in/offercandidate",
        })
        app_id = app_res.json()["data"]["id"]

        # Admin generates offer letter
        offer_res = client.post(f"/admin/applications/{app_id}/offer", json={
            "application_id": app_id,
            "user_id": user_id,
            "intern_name": "Offer Candidate",
            "track": "Full Stack Web Development",
            "start_date": "2026-09-01",
            "end_date": "2026-11-30",
            "stipend_amount": 20000,
        })
        assert offer_res.status_code == 200
        offer_id = offer_res.json()["data"]["offer_id"]
        assert offer_id.startswith("OFF-2026-")

        # Verify public verification handles offer IDs
        verify_offer = client.get(f"/verify/{offer_id}")
        assert verify_offer.status_code == 200
        assert verify_offer.json()["data"]["type"] == "Official Internship Offer Letter"

        # Intern accepts offer
        resp_res = client.post(f"/offers/{offer_id}/respond", json={"action": "accept"})
        assert resp_res.status_code == 200
        assert resp_res.json()["data"]["status"] == "Accepted"

        # Intern submits LinkedIn offer post proof
        proof_res = client.post(f"/users/{user_id}/onboarding/linkedin-proof", json={
            "proof_type": "offer",
            "post_url": "https://www.linkedin.com/posts/offercandidate_internshipchesko-activity-7123456789",
            "screenshot_url": "https://drive.google.com/file/d/offer-screenshot/view",
        })
        assert proof_res.status_code == 200
        proof_id = proof_res.json()["data"]["id"]

        # Mentor reviews proof
        review_proof = client.post(f"/admin/linkedin-proofs/{proof_id}/review", json={
            "status": "Approved",
            "review_notes": "Great announcement post! Onboarding complete.",
        })
        assert review_proof.status_code == 200
        assert review_proof.json()["data"]["status"] == "Approved"


def test_weekly_report_final_project_and_csv_export():
    """Verify weekly reporting, final project submission, notifications, and CSV export."""
    with TestClient(app) as client:
        # Register user
        user_res = client.post("/auth/register", json={
            "name": "Weekly Reporter",
            "email": "weekly.reporter@example.com",
            "role": "intern",
        })
        user_id = user_res.json()["data"]["id"]

        # Submit weekly report
        rep_res = client.post(f"/users/{user_id}/reports/weekly", json={
            "week_number": 1,
            "done_summary": "Built frontend responsive filters and connected with REST API endpoints.",
            "blockers": "None, smoothly integrated.",
            "next_week": "Implement SQLite WAL mode database persistence and migrations.",
        })
        assert rep_res.status_code == 200
        assert rep_res.json()["data"]["week_number"] == 1

        # Check weekly reports summary
        rep_list = client.get(f"/users/{user_id}/reports/weekly")
        assert rep_list.status_code == 200
        assert rep_list.json()["data"]["total_submitted"] == 1

        # Submit final project
        proj_res = client.post(f"/users/{user_id}/final-project", json={
            "project_title": "InternshipChesko Production Deployment",
            "repo_url": "https://github.com/kalakonda-akshay/edvyro_5",
            "live_url": "https://edvyro5.vercel.app",
            "report_pdf_url": "https://drive.google.com/file/d/capstone-report.pdf",
            "self_assessment": "Delivered production-ready full stack platform with zero vulnerabilities.",
            "feedback_rating": 5,
            "feedback_text": "Exceptional hands-on curriculum and industry-standard engineering tasks!",
        })
        assert proj_res.status_code == 200
        proj_id = proj_res.json()["data"]["id"]

        # Mentor reviews final project
        proj_review = client.post(f"/admin/final-projects/{proj_id}/review", json={
            "status": "Approved",
            "review_notes": "Outstanding capstone submission!",
        })
        assert proj_review.status_code == 200
        assert proj_review.json()["data"]["status"] == "Approved"

        # Check in-app notifications
        notif_res = client.get(f"/notifications?user_id={user_id}")
        assert notif_res.status_code == 200
        assert len(notif_res.json()["data"]) > 0

        # Export CSV endpoints
        csv_apps = client.get("/admin/export/csv?type=applications")
        assert csv_apps.status_code == 200
        assert "text/csv" in csv_apps.headers["Content-Type"]

        csv_interns = client.get("/admin/export/csv?type=interns")
        assert csv_interns.status_code == 200
        assert "text/csv" in csv_interns.headers["Content-Type"]

        csv_subs = client.get("/admin/export/csv?type=submissions")
        assert csv_subs.status_code == 200
        assert "text/csv" in csv_subs.headers["Content-Type"]

