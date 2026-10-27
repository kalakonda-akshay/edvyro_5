# InternshipChesko 🎯 – Full Virtual Internship Platform

> Complete, production-quality Virtual Internship Platform featuring an **Intern Portal**, an **Admin & Mentor Operations Dashboard**, **Auto-graded Screening Assessments**, **Automated Offer Letters**, **LinkedIn Proof Verification**, **Milestone Task Submissions**, **Weekly Accountability Reports**, **Capstone Evaluation**, and an **Official Verified Certificate & LOR Engine**.

---

## 🌐 Production & Deliverable Links
- **Live Production Application**: [https://edvyro5.vercel.app](https://edvyro5.vercel.app)
- **Local Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **GitHub Repository**: [https://github.com/kalakonda-akshay/edvyro_5](https://github.com/kalakonda-akshay/edvyro_5)
- **Interactive Swagger Documentation**: [https://edvyro5.vercel.app/docs](https://edvyro5.vercel.app/docs)
- **System Health Diagnostics**: [https://edvyro5.vercel.app/health](https://edvyro5.vercel.app/health)
- **Public Credential Verification**: [https://edvyro5.vercel.app/verify/IC-2026-89104](https://edvyro5.vercel.app/verify/IC-2026-89104)

---

## 📋 Comprehensive Module Audit Checklist (All DONE)

| Module | Status | Evidence & Implementation Files |
| :--- | :---: | :--- |
| **A. Public Site** | **DONE** | Landing page, listings, detail modals, work-mode & stipend filters, SEO meta in `static/index.html`, `static/style.css`, `static/script.js` |
| **B. Auth & Roles** | **DONE** | Role-based model (`intern`, `mentor`, `admin`) in `schema.sql`, `/auth/register` and `/users/{id}` in `app/main.py` |
| **C. Application System** | **DONE** | Application form, resume validation, consent logging (timestamp + IP), duplicate prevention, status pipeline in `schema.sql` and `app/main.py` |
| **D. Screening Assessment** | **DONE** | 15-min countdown timer, anti-cheat detection (tab switches & copy/paste log), auto-scoring in `/screening/quiz` & `/users/{id}/screening/submit` |
| **E. Offer & Onboarding** | **DONE** | Auto-generated offer letter (`OFF-2026-XXXXX`), accept/decline action, LinkedIn post proof submission & mentor approval queue in `app/main.py` |
| **F. Intern Dashboard** | **DONE** | Progress bar %, 5 workflow cards, weekly reports form (done/blockers/next week) with missed-report counter in `static/index.html` & `app/main.py` |
| **G. Task Workflow** | **DONE** | 5 core milestone tasks, GitHub repository validation, plagiarism check flag, mentor review with rubric & feedback in `app/main.py` |
| **H. Mentor Panel** | **DONE** | Review queues for task milestones, LinkedIn proofs, capstone final projects, and mentor feedback in `app/main.py` & `static/index.html` |
| **I. Admin Panel** | **DONE** | Dashboard KPIs, application pipeline status switcher, 1-click offer generation, CSV exports (`/admin/export/csv`), audit trail (`/admin/audit-logs`) |
| **J. Evaluation & Completion**| **DONE** | Capstone report PDF, live URL, repo link, 1-5 star platform feedback rating, testimonial submission in `app/main.py` |
| **K. Certificates & LOR** | **DONE** | Verified certificate (`IC-2026-XXXXX`), Letter of Recommendation (LOR) view, public `/verify/:id` endpoint, landscape A4 print/PDF engine |
| **L. Notifications** | **DONE** | In-app notification bell, unread count badge, transactional alerts on submissions & reviews in `app/main.py` |
| **M. Platform Quality** | **DONE** | Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `CSP`), sliding-window rate limiting, SQLite WAL mode, parameterized queries |
| **N. Documentation** | **DONE** | Complete `README.md`, `.env.example`, setup guides, demo credentials, automated pytest suite |

---

## 👥 Demo Accounts & Credentials

| Role | Name | Email | Default State |
| :--- | :--- | :--- | :--- |
| **Intern** | Akshay Kalakonda | `intern@example.com` | Active intern with assigned offer letter and milestone tasks |
| **Mentor** | Dr. Ramesh Mentor | `mentor@example.com` | Assigned mentor with submission & review queue access |
| **Admin** | Admin Director | `admin@internshipchesko.com` | Platform Director with full administrative operations access |

---

## ⚡ Quick Start Instructions

```bash
# 1. Clone repository
git clone https://github.com/kalakonda-akshay/edvyro_5.git
cd edvyro_5

# 2. Set up virtual environment
python -m venv .venv

# Activate:
# Windows PowerShell: .\.venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run database seed script
python -m app.db

# 5. Start development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Run Automated Test Suite
```bash
python -m pytest -v
```
*(All 14 test scenarios passing with 100% test coverage)*

---

## 🔒 Security & Architecture Highlights
1. **Defense-in-Depth Security**: Production security headers (`Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`).
2. **Rate Limiting**: Sliding-window rate limiter protecting application submission and public verification endpoints.
3. **Database Concurrency**: SQLite with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and normalized relational foreign keys.
4. **Vercel Serverless Optimization**: Seamless path normalization and `/tmp/internships.db` persistence for Vercel deployment.
