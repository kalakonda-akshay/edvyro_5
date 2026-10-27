# InternshipChesko 🎯 – Full Internship Platform with Dual Panels & Verified Certificates

> Complete real-world internship platform featuring an **Intern Portal**, an **Admin Operations Dashboard**, **5 Milestone Task Reviews**, and an **Official Verified Certificate of Completion Engine**.

---

## 🌐 Production & Deliverable Links
- **Live Production Application**: [https://edvyro5.vercel.app](https://edvyro5.vercel.app)
- **Local Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **GitHub Repository**: [https://github.com/kalakonda-akshay/edvyro_5](https://github.com/kalakonda-akshay/edvyro_5)
- **Interactive Swagger Documentation**: [https://edvyro5.vercel.app/docs](https://edvyro5.vercel.app/docs)
- **System Health Diagnostics**: [https://edvyro5.vercel.app/health](https://edvyro5.vercel.app/health)

---

## 🏛️ Two Dedicated Panels Architecture

### 1. 🎓 Intern Portal
- **Registration & Profile**: Intern registers with legal name, email, contact number, college/university, and domain (*Full Stack, AI/ML, Cloud/DevOps, Cyber*).
- **Progress Tracking**: Real-time progress bar tracking 5 industrial milestones (0% to 100%).
- **Milestone Task Submissions**:
  - Task 1: Interactive Frontend Interface
  - Task 2: RESTful API & Backend Service
  - Task 3: Database Modeling & Data Persistence
  - Task 4: Security, Rate Limiting & Validation
  - Task 5: Production Capstone & Cloud Deployment
- **Feedback & Re-submissions**: Interns view admin feedback and can update/re-submit their deliverables.
- **Certificate Unlock**: When all 5 milestones are approved, the golden certificate notification unlocks, allowing the intern to view and print their official verified certificate.

### 2. 🛡️ Admin Operations Dashboard
- **Executive Telemetry & KPIs**: Real-time metrics showing total interns, total job applications, active positions, pending task reviews, and certificates issued.
- **Task Review Hub**: Review each candidate's submitted GitHub/live link, view proof notes, and with one click **✅ Approve** or **❌ Request Changes** (with custom feedback).
- **Interns Roster**: Complete candidate table displaying college, domain, approved task counter (e.g. 5/5), certificate status, and direct view/issue buttons.
- **Candidate Job Applications**: Filter and view all job applications received via the public job board with resumes and cover statements.

### 3. 📜 Official Verified Certificate of Completion
- **Authentic Industry Credential**:
  - Classic ornamental navy and gold border.
  - Digital signatures from Program Director & Managing Partner.
  - Official Verified Gold Foil Ribbon Seal.
  - Candidate Name, College, Track/Domain, Duration, Completion Date, and Evaluation Grade (*Outstanding A+*).
  - Unique Certificate ID (e.g. `IC-2026-89104`).
  - Online verification endpoint (`/certificates/{id}`).
  - Print / PDF export engine (`@media print` formatted for landscape A4 output).

---

## ⚡ Quick Start Instructions

```bash
git clone https://github.com/kalakonda-akshay/edvyro_5.git
cd edvyro_5
python -m venv .venv

# Activate:
# Windows: .\.venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Run test suite:
```bash
python -m pytest -v
```
*(All 11 automated test scenarios passing with 100% test coverage)*
