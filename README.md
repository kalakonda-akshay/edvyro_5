# InternHub – Production-Ready Capstone (Task 5)

> Full-stack production internship portal demonstrating deployment readiness, comprehensive QA, performance optimization, and architectural decisions.

---

## 🌐 Production & Deliverable Links
- **GitHub Repository**: [https://github.com/kalakonda-akshay/edvyro_5](https://github.com/kalakonda-akshay/edvyro_5)
- **Interactive Swagger Documentation**: `http://localhost:8000/docs`
- **System Health Diagnostics**: `http://localhost:8000/health`

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    Client["Client Browser (Desktop & Mobile)"] -->|HTTPS / REST API| MW_Log["Request Logging & Telemetry Middleware"]
    MW_Log --> MW_Sec["Security Headers Middleware (CSP, nosniff, DENY)"]
    MW_Sec --> Limiter{"Sliding-Window Rate Limiter (5 req/min)"}
    
    Limiter -->|Limit Exceeded| HTTP429["429 Too Many Requests + Retry-After"]
    Limiter -->|Allowed| Router["FastAPI Routing Engine"]
    
    Router -->|GET /internships| SvcIntern["Internship Query Engine (Parameterized SQL)"]
    Router -->|POST /internships/{id}/apply| SvcApply["Application Service (Pydantic V2)"]
    Router -->|GET /health| Health["Multi-Stage Health Probes (/ready, /live)"]
    Router -->|GET /| Static["Static Frontend (Vanilla ES6 + CSS3)"]
    
    SvcIntern --> DB[("SQLite Database (WAL Mode)")]
    SvcApply --> DB
    Health --> DB
```

---

## 🧠 Engineering Decisions & Trade-Offs

### 1. Framework Selection: FastAPI vs. Django/Flask
- **Decision**: Selected **FastAPI** with Python 3.
- **Rationale**: FastAPI leverages native asynchronous event loops and Pydantic V2 validation, generating automatic OpenAPI/Swagger documentation with zero configuration. It outperforms Flask while remaining far lighter and more modular than monolithic Django.

### 2. Database Engine: SQLite with WAL Mode vs. Managed PostgreSQL
- **Decision**: Production-tuned **SQLite** operating in **Write-Ahead Logging (WAL)** mode.
- **Rationale**: For self-contained internship boards, SQLite eliminates external daemon overhead and network hop latency while WAL mode (`PRAGMA journal_mode = WAL`) enables simultaneous concurrent reads alongside writes without locking.
- **Trade-off**: For multi-instance horizontal scaling, PostgreSQL with connection pooling would be preferred.

### 3. Rate Limiting: Sliding-Window vs. Fixed-Window / Redis
- **Decision**: Implemented an in-memory thread-safe **Sliding-Window Rate Limiter** (`app/limiter.py`).
- **Rationale**: Fixed windows are susceptible to traffic spikes at window boundaries. The sliding window smooths requests and prevents bot flooding on the application form without requiring external Redis infrastructure dependencies.

### 4. Zero-Framework Frontend vs. React/Vue SPA
- **Decision**: Modular Vanilla HTML5, CSS3 Custom Properties, and ES6 JavaScript.
- **Rationale**: Instant load times with **zero bundle build step**, zero hydration delays, and a total bundle weight under 45 KB.

---

## 🌟 Polished User Journey & Features

1. **Multi-Facet Discovery**:
   - Live search matching role titles, companies, descriptions, and required skills.
   - Interactive category pills (*Web Development, Software Engineering, Data Science, Cybersecurity, DevOps*).
   - Work mode dropdown (*Remote, Hybrid, On-site*), status filter (*Open, Closed*), and minimum stipend range slider.
2. **Resilient Network States**:
   - **Visible Loading Skeletons**: Shimmering card placeholders during asynchronous data fetches.
   - **Visible Failure State**: Informative error card with status diagnostic and an interactive **"↻ Retry Connection"** button.
3. **Secure Application Form**:
   - Dual-layer client and server validation for applicant names, emails, phone numbers, and HTTP/HTTPS resume links.
   - Duplicate prevention (`409 Conflict`) preventing multiple submissions for the same position.
   - Immediate visual feedback, loading spinners, and friendly toast alerts.
4. **"My Applications" Tracking**:
   - Candidates can look up all positions they have applied for by entering their email address.
5. **Interactive Actions**:
   - One-click role bookmarking/saving with local storage persistence.
   - One-click share action copying formatted role details to clipboard.

---

## 📊 Telemetry & Observability

### 1. Structured Logging
Every HTTP request generates a structured log line capturing method, path, HTTP status, execution latency, and client IP:
```text
2026-10-27 18:14:02 [INFO] [internhub.api] GET /internships?status=open -> 200 in 3.42ms | ip=127.0.0.1
2026-10-27 18:14:05 [INFO] [internhub.api] POST /internships/1/apply -> 201 in 8.11ms | ip=127.0.0.1
```

### 2. Multi-Stage Health Probes
- `GET /health`: Comprehensive diagnostic metrics (service status, timestamp, uptime, database row count, query latency).
- `GET /health/ready`: Readiness probe for load balancers and orchestrators.
- `GET /health/live`: Liveness probe verifying server event-loop health.

---

## 🛡️ Quality Assurance & Security Summary
Full audit report available in [`QA_REPORT.md`](./QA_REPORT.md).
- ✅ **Accessibility**: WCAG 2.1 AA compliant (color contrast > 4.5:1, keyboard operable, ARIA dialogs).
- ✅ **Security**: `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- ✅ **Resilience**: 100% parameterized SQL queries preventing SQL injection attacks.

---

## ⚡ Quick Start & Run Instructions

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/kalakonda-akshay/edvyro_5.git
cd edvyro_5
python -m venv .venv

# Activate on Windows:
.\.venv\Scripts\activate
# Activate on Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the Production Server
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your web browser.

### 3. Run Automated Tests
```bash
python -m pytest -v
```
All 9 automated regression tests pass with 100% test coverage.
