-- Production Schema for InternshipChesko Full Platform
-- Includes Internships, Users, Task Milestones, Task Submissions, and Verified Certificates

CREATE TABLE IF NOT EXISTS internships (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL CHECK (length(title) BETWEEN 3 AND 120),
    company     TEXT    NOT NULL CHECK (length(company) BETWEEN 2 AND 120),
    category    TEXT    NOT NULL DEFAULT 'Software Engineering',
    location    TEXT    NOT NULL,
    work_mode   TEXT    NOT NULL CHECK (work_mode IN ('remote','onsite','hybrid')),
    duration    INTEGER NOT NULL DEFAULT 3 CHECK (duration BETWEEN 1 AND 12),
    stipend     INTEGER CHECK (stipend IS NULL OR stipend >= 0),
    skills      TEXT    NOT NULL DEFAULT '[]',          -- JSON array of required skills
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
    role        TEXT NOT NULL DEFAULT 'intern' CHECK (role IN ('intern', 'admin')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_num    INTEGER NOT NULL,
    title       TEXT NOT NULL,
    objective   TEXT NOT NULL,
    deliverable TEXT NOT NULL,
    guide_url   TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS task_submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id         INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    submission_url  TEXT NOT NULL,
    notes           TEXT DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    feedback        TEXT DEFAULT '',
    submitted_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    reviewed_at     TEXT,
    UNIQUE(user_id, task_id)
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
    issued_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    internship_id  INTEGER NOT NULL REFERENCES internships(id) ON DELETE CASCADE,
    full_name      TEXT    NOT NULL CHECK (length(full_name) BETWEEN 2 AND 100),
    email          TEXT    NOT NULL CHECK (length(email) BETWEEN 5 AND 120),
    phone          TEXT    NOT NULL CHECK (length(phone) BETWEEN 7 AND 25),
    resume_url     TEXT    NOT NULL CHECK (length(resume_url) BETWEEN 5 AND 500),
    cover_letter   TEXT    DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
    UNIQUE(internship_id, email)
);

CREATE INDEX IF NOT EXISTS idx_internships_status ON internships(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_submissions_user ON task_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_certificates_user ON certificates(user_id);
