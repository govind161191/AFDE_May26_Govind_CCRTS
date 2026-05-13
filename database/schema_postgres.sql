-- ============================================================
-- CCRTS — PostgreSQL schema
-- ============================================================

DROP TABLE IF EXISTS notifications      CASCADE;
DROP TABLE IF EXISTS feedback           CASCADE;
DROP TABLE IF EXISTS attachments        CASCADE;
DROP TABLE IF EXISTS complaint_history  CASCADE;
DROP TABLE IF EXISTS complaints         CASCADE;
DROP TABLE IF EXISTS categories         CASCADE;
DROP TABLE IF EXISTS users              CASCADE;
DROP TABLE IF EXISTS roles              CASCADE;

CREATE TABLE roles (
    role_id   SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id        SERIAL PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    role_id        INTEGER NOT NULL REFERENCES roles(role_id),
    phone          VARCHAR(20),
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_date   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);

CREATE TABLE categories (
    category_id   SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description   VARCHAR(255)
);

CREATE TABLE complaints (
    complaint_id        SERIAL PRIMARY KEY,
    complaint_number    VARCHAR(20)  NOT NULL UNIQUE,
    customer_id         INTEGER NOT NULL REFERENCES users(user_id),
    assigned_agent_id   INTEGER REFERENCES users(user_id),
    category_id         INTEGER NOT NULL REFERENCES categories(category_id),
    subject             VARCHAR(255) NOT NULL,
    description         TEXT NOT NULL,
    priority            VARCHAR(20)  NOT NULL DEFAULT 'Medium',
    status              VARCHAR(40)  NOT NULL DEFAULT 'Open',
    sla_deadline        TIMESTAMP NOT NULL,
    created_date        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_date       TIMESTAMP,
    closed_date         TIMESTAMP,
    resolution_comment  TEXT,
    is_escalated        BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_complaint_status   ON complaints(status);
CREATE INDEX idx_complaint_customer ON complaints(customer_id);
CREATE INDEX idx_complaint_agent    ON complaints(assigned_agent_id);

CREATE TABLE complaint_history (
    history_id    SERIAL PRIMARY KEY,
    complaint_id  INTEGER NOT NULL REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    updated_by    INTEGER NOT NULL REFERENCES users(user_id),
    old_status    VARCHAR(40),
    new_status    VARCHAR(40) NOT NULL,
    comment       TEXT,
    updated_date  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_history_complaint ON complaint_history(complaint_id);

CREATE TABLE attachments (
    attachment_id  SERIAL PRIMARY KEY,
    complaint_id   INTEGER NOT NULL REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    file_name      VARCHAR(255) NOT NULL,
    file_path      VARCHAR(500) NOT NULL,
    content_type   VARCHAR(100),
    uploaded_by    INTEGER NOT NULL REFERENCES users(user_id),
    uploaded_date  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feedback (
    feedback_id   SERIAL PRIMARY KEY,
    complaint_id  INTEGER NOT NULL UNIQUE REFERENCES complaints(complaint_id) ON DELETE CASCADE,
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments      TEXT,
    created_date  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(user_id),
    complaint_id    INTEGER REFERENCES complaints(complaint_id) ON DELETE SET NULL,
    message         VARCHAR(500) NOT NULL,
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    created_date    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_notif_user ON notifications(user_id, is_read);
