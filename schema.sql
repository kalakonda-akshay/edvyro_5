-- Production Database Schema for Virtual Internship Platform
-- Supports: Internships, Users, Offers, Onboarding/LinkedIn, Screening,
-- Tasks, Weekly Reports, Evaluations, Certificates, Notifications & Audit Logs.

CREATE TABLE IF NOT EXISTS internships (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL CHECK (length(title) BETWEEN 3 AND 120),
    company     TEXT    NOT NULL CHECK (length(company) BETWEEN 2 AND 120),
    category    TEXT    NOT NULL DEFAULT 'Software Engineering',
    location    TEXT    NOT NULL,
    work_mode   TEXT    NOT NULL CHECK (work_mode IN ('remote','onsite','hybrid')),
    duration    INTEGER NOT NULL DEFAULT 3 CHECK (duration BETWEEN 1 AND 12),
    stipend     INTEGER CHECK (stipend IS NULL OR stipend >= 0),
    skills      TEXT    NOT NULL DEFAULT '[]',          -- JSON array
    description TEXT    NOT NULL DEFAULT '',
    deadline    TEXT,                                   -- ISO date: YYYY-MM-DD
    status      TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL CHECK (length(name) >= 2),
    email       TEXT NOT NULL UNIQUE,
    phone       TEXT NOT NULL DEFAULT '',
    college     TEXT NOT NULL DEFAULT 'Engineering College',
    domain      TEXT NOT NULL DEFAULT 'Full Stack Web Development',
    role        TEXT NOT NULL DEFAULT 'intern' CHECK (role IN ('intern', 'mentor', 'admin')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    internship_id  INTEGER NOT NULL REFERENCES internships(id) ON DELETE CASCADE,
    full_name      TEXT    NOT NULL CHECK (length(full_name) BETWEEN 2 AND 100),
    email          TEXT    NOT NULL CHECK (length(email) BETWEEN 5 AND 120),
    phone          TEXT    NOT NULL CHECK (length(phone) BETWEEN 7 AND 25),
    college        TEXT    NOT NULL DEFAULT '',
    resume_url     TEXT    NOT NULL CHECK (length(resume_url) BETWEEN 5 AND 500),
    portfolio_url  TEXT    DEFAULT '',
    skills_tags    TEXT    DEFAULT '[]',
    cover_letter   TEXT    DEFAULT '',
    consent_given  INTEGER NOT NULL DEFAULT 1,
    consent_ip     TEXT    DEFAULT '127.0.0.1',
    status         TEXT    NOT NULL DEFAULT 'Submitted' CHECK (status IN ('Submitted', 'Under Review', 'Shortlisted', 'Offered', 'Accepted', 'Declined', 'Rejected')),
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(internship_id, email)
);

CREATE TABLE IF NOT EXISTS offers (
    offer_id       TEXT PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id        INTEGER REFERENCES users(id) ON DELETE SET NULL,
    intern_name    TEXT NOT NULL,
    track          TEXT NOT NULL,
    batch          TEXT NOT NULL DEFAULT '2026-B1',
    duration       TEXT NOT NULL DEFAULT '3 Months',
    start_date     TEXT NOT NULL,
    end_date       TEXT NOT NULL,
    stipend_amount INTEGER NOT NULL DEFAULT 15000,
    mentor_name    TEXT NOT NULL DEFAULT 'Senior Engineering Lead',
    signatory_name TEXT NOT NULL DEFAULT 'Program Director',
    status         TEXT NOT NULL DEFAULT 'Offered' CHECK (status IN ('Offered', 'Accepted', 'Declined', 'Expired')),
    expires_at     TEXT NOT NULL,
    issued_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    accepted_at    TEXT
);

CREATE TABLE IF NOT EXISTS linkedin_proofs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    proof_type     TEXT NOT NULL CHECK (proof_type IN ('offer', 'completion')),
    post_url       TEXT NOT NULL,
    screenshot_url TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Resubmit')),
    review_notes   TEXT DEFAULT '',
    submitted_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    reviewed_at    TEXT,
    UNIQUE(user_id, proof_type)
);

CREATE TABLE IF NOT EXISTS screening_quizzes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    track       TEXT NOT NULL,
    title       TEXT NOT NULL,
    time_limit_mins INTEGER NOT NULL DEFAULT 20,
    pass_cutoff INTEGER NOT NULL DEFAULT 70,
    questions   TEXT NOT NULL -- JSON array of questions with options and answer
);

CREATE TABLE IF NOT EXISTS quiz_submissions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id        INTEGER NOT NULL REFERENCES screening_quizzes(id) ON DELETE CASCADE,
    score          INTEGER NOT NULL,
    passed         INTEGER NOT NULL,
    tab_switches   INTEGER NOT NULL DEFAULT 0,
    copy_paste_log TEXT DEFAULT '',
    submitted_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(user_id, quiz_id)
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_num    INTEGER NOT NULL,
    title       TEXT NOT NULL,
    objective   TEXT NOT NULL,
    deliverable TEXT NOT NULL,
    deadline_days INTEGER NOT NULL DEFAULT 7,
    guide_url   TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS task_submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id         INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    submission_url  TEXT NOT NULL,
    notes           TEXT DEFAULT '',
    is_late         INTEGER NOT NULL DEFAULT 0,
    plagiarism_flag INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    feedback        TEXT DEFAULT '',
    rubric_score    INTEGER DEFAULT 85,
    submitted_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    reviewed_at     TEXT,
    UNIQUE(user_id, task_id)
);

CREATE TABLE IF NOT EXISTS weekly_reports (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    week_number  INTEGER NOT NULL,
    done_summary TEXT NOT NULL,
    blockers     TEXT DEFAULT '',
    next_week    TEXT NOT NULL,
    submitted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(user_id, week_number)
);

CREATE TABLE IF NOT EXISTS final_projects (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_title    TEXT NOT NULL,
    repo_url         TEXT NOT NULL,
    live_url         TEXT DEFAULT '',
    report_pdf_url   TEXT NOT NULL,
    self_assessment  TEXT NOT NULL,
    feedback_rating  INTEGER NOT NULL CHECK (feedback_rating BETWEEN 1 AND 5),
    feedback_text    TEXT DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    submitted_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS certificates (
    certificate_id   TEXT PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    intern_name      TEXT NOT NULL,
    college          TEXT NOT NULL,
    domain           TEXT NOT NULL,
    internship_title TEXT NOT NULL,
    company          TEXT NOT NULL,
    start_date       TEXT NOT NULL,
    completion_date  TEXT NOT NULL,
    grade            TEXT NOT NULL DEFAULT 'Outstanding (A+)',
    lor_text         TEXT DEFAULT '',
    status           TEXT NOT NULL DEFAULT 'Valid' CHECK (status IN ('Valid', 'Revoked')),
    issued_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS in_app_notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    message     TEXT NOT NULL,
    is_read     INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action      TEXT NOT NULL,
    actor       TEXT NOT NULL,
    details     TEXT NOT NULL,
    timestamp   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_internships_status ON internships(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_submissions_user ON task_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_certificates_user ON certificates(user_id);
CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(status);
