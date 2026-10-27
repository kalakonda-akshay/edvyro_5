-- Capstone Production Schema for InternHub
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
CREATE INDEX IF NOT EXISTS idx_internships_work_mode ON internships(work_mode);
CREATE INDEX IF NOT EXISTS idx_internships_category ON internships(category);
CREATE INDEX IF NOT EXISTS idx_applications_internship ON applications(internship_id);
CREATE INDEX IF NOT EXISTS idx_applications_email ON applications(email);
