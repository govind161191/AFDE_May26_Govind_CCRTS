-- ============================================================
-- CCRTS — SQLite schema
-- ============================================================
-- The FastAPI app auto-creates these tables via SQLAlchemy on startup.
-- Use this file when bootstrapping manually or inspecting the schema.

DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS complaint_history;
DROP TABLE IF EXISTS complaints;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

CREATE TABLE roles (
    role_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    email          TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    role_id        INTEGER NOT NULL REFERENCES roles(role_id),
    phone          TEXT,
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE categories (
    category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT    NOT NULL UNIQUE,
    description   TEXT
);

CREATE TABLE complaints (
    complaint_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_number    TEXT    NOT NULL UNIQUE,
    customer_id         INTEGER NOT NULL REFERENCES users(user_id),
    assigned_agent_id   INTEGER REFERENCES users(user_id),
    category_id         INTEGER NOT NULL REFERENCES categories(category_id),
    subject             TEXT    NOT NULL,
    description         TEXT    NOT NULL,
    priority            TEXT    NOT NULL DEFAULT 'Medium',
    status              TEXT    NOT NULL DEFAULT 'Open',
    sla_deadline        DATETIME NOT NULL,
    created_date        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_date       DATETIME,
    closed_date         DATETIME,
    resolution_comment  TEXT,
    is_escalated        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_complaint_status   ON complaints(status);
CREATE INDEX idx_complaint_customer ON complaints(customer_id);
CREATE INDEX idx_complaint_agent    ON complaints(assigned_agent_id);
CREATE INDEX idx_complaint_number   ON complaints(complaint_number);

CREATE TABLE complaint_history (
    history_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id  INTEGER NOT NULL REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    updated_by    INTEGER NOT NULL REFERENCES users(user_id),
    old_status    TEXT,
    new_status    TEXT    NOT NULL,
    comment       TEXT,
    updated_date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_history_complaint ON complaint_history(complaint_id);

CREATE TABLE attachments (
    attachment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id   INTEGER NOT NULL REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    file_name      TEXT    NOT NULL,
    file_path      TEXT    NOT NULL,
    content_type   TEXT,
    uploaded_by    INTEGER NOT NULL REFERENCES users(user_id),
    uploaded_date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feedback (
    feedback_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id  INTEGER NOT NULL UNIQUE REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments      TEXT,
    created_date  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(user_id),
    complaint_id    INTEGER REFERENCES complaints(complaint_id) ON DELETE SET NULL,
    message         TEXT    NOT NULL,
    is_read         INTEGER NOT NULL DEFAULT 0,
    created_date    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_notif_user ON notifications(user_id, is_read);
