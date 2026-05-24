# Customer Complaint & Resolution Tracking System (CCRTS)

> **AFDE Capstone — Phase 1**
> Full-stack enterprise complaint-management application with role-based access control, complete complaint lifecycle, SLA tracking with auto-escalation, attachments, in-app notifications, and feedback.

![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI%20%2B%20JWT%20%2B%20SQLite-blue)
![Auth](https://img.shields.io/badge/auth-JWT%20%2B%20bcrypt-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Project Information

| Field | Value |
|---|---|
| **Project Title** | Customer Complaint & Resolution Tracking System |
| **Project Code** | CCRTS |
| **Batch** | AFDE_May26 |
| **Participant** | Govind |
| **Phase** | 1 |

### Overview

Manual complaint handling — emails, spreadsheets, scattered tools — leaves customers waiting and managers blind. CCRTS gives an organization a single, centralized platform where customers raise issues, supervisors triage and assign them, agents resolve them, and everyone has live visibility into status, SLA, and history.

### Features Implemented

All 8 modules described in the Phase 1 requirements:

1. **Authentication & Authorization** — Registration, JWT-based login, password change, role-based access control (Admin / Supervisor / Support Agent / Customer).
2. **Complaint Registration** — Auto-generated complaint number (`CMP-YYYYMMDD-XXXXXX`), category, priority, attachments.
3. **Complaint Workflow** — 7 statuses: Open → Assigned → In Progress → Pending Customer Response → Escalated → Resolved → Closed.
4. **SLA & Escalation** — Priority-based deadlines (Critical 4h / High 24h / Medium 48h / Low 72h), manual + on-demand auto-escalation sweep.
5. **Resolution** — Comments, audit trail, customer reopen via "Pending Customer Response".
6. **Notifications** — In-app bell with unread badge, polling every 30s.
7. **Dashboard & Analytics** — KPIs, by-category, by-priority, agent performance, SLA breaches, average resolution time.
8. **Feedback** — 5-star rating + comments after a complaint is resolved.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 (functional + hooks) + React Router v6 |
| State | React Context (auth) + per-page hooks |
| HTTP | Axios with JWT auto-injection |
| Styling | Hand-rolled responsive CSS |
| Backend | Python 3.10+, FastAPI |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic v2 |
| Auth | OAuth2 password flow → JWT (HS256); bcrypt for passwords |
| Database | SQLite (PostgreSQL-ready via `DATABASE_URL`) |
| Files | Multipart uploads stored to `backend/uploads/` |

---

## Project Structure

```
AFDE_May26_Govind_CCRTS/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── database.py              # SQLAlchemy engine + session
│   ├── models.py                # ORM models for all 8 tables
│   ├── schemas.py               # Pydantic request/response shapes
│   ├── auth.py                  # JWT, password hashing, RBAC dependencies
│   ├── crud/
│   │   ├── users.py
│   │   ├── complaints.py        # Workflow + audit trail
│   │   └── dashboard.py
│   ├── routers/
│   │   ├── auth_router.py
│   │   ├── users_router.py
│   │   ├── categories_router.py
│   │   ├── complaints_router.py
│   │   ├── attachments_router.py
│   │   ├── feedback_router.py
│   │   ├── notifications_router.py
│   │   └── dashboard_router.py
│   ├── services/
│   │   ├── sla.py               # Priority -> deadline + breach detection
│   │   ├── notifications.py     # Notification creation
│   │   └── seed_data.py         # Roles, categories, demo users
│   ├── uploads/                 # Attachment storage (gitignored)
│   └── requirements.txt
├── etl/                         # ETL pipeline (standalone)
│   ├── pipeline.py              # CLI orchestrator — entry point
│   ├── config.py                # DB path, SLA constants, valid statuses
│   ├── etl_models.py            # SQLAlchemy models for 5 ETL summary tables
│   ├── extract.py               # Extract from CSV files or operational DB
│   ├── transform.py             # Validate, clean, enrich, aggregate
│   ├── load.py                  # Load into operational + summary tables
│   ├── export.py                # Export to CSV and multi-sheet Excel
│   ├── sample_data/
│   │   ├── complaints_import.csv
│   │   └── users_import.csv
│   ├── exports/                 # Runtime output (gitignored)
│   └── requirements.txt         # pandas, openpyxl
├── frontend/
│   ├── public/index.html
│   ├── src/
│   │   ├── context/AuthContext.js
│   │   ├── components/          # Navbar, Modal, Toast, Badges, NotificationBell, StatCard, ProtectedRoute
│   │   ├── pages/               # Login, Register, Dashboard, Registration, List, Detail, Queue, Escalations, Reports, Users
│   │   ├── services/            # complaintService.js, userService.js
│   │   ├── api.js               # Axios + JWT interceptor
│   │   ├── App.js
│   │   ├── index.js
│   │   └── styles.css
│   └── package.json
├── database/
│   ├── schema_sqlite.sql
│   ├── schema_postgres.sql
│   └── sample_data.sql
├── docs/
│   ├── API.md
│   ├── SETUP.md
│   ├── HLD.md
│   └── DB_DESIGN.md
├── screenshots/
├── .gitignore
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd backend
python -m venv venv
# Activate venv (Windows: venv\Scripts\activate)
source venv/bin/activate
pip install -r requirements.txt

# Seed demo data
python services/seed_data.py

# Run
uvicorn main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm start
```

Opens http://localhost:3000.

### Demo accounts (created by seed)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@ccrts.io` | `Admin@123` |
| Supervisor | `sarah@ccrts.io` | `Super@123` |
| Support Agent | `alex@ccrts.io` | `Agent@123` |
| Support Agent | `maria@ccrts.io` | `Agent@123` |
| Customer | `govind@example.com` | `Customer@123` |
| Customer | `priya@example.com` | `Customer@123` |
| Customer | `rahul@example.com` | `Customer@123` |

---

## End-to-end happy path

1. Customer (`govind@example.com`) logs in → **+ New Complaint** → submits issue
2. Supervisor (`sarah@ccrts.io`) opens the complaint → assigns to **Alex Agent** → adjusts priority
3. Agent (`alex@ccrts.io`) opens **Work Queue** → marks **In Progress** → adds resolution → **Resolved**
4. Customer sees update on dashboard / bell → opens complaint → leaves **5-star feedback**
5. Supervisor visits **Reports** → sees Alex's resolution rate climb

If a complaint blows its SLA, the dashboard's **Run Escalation Sweep** button or `POST /complaints/sweep-escalations` flips it to **Escalated** and notifies supervisors.

---

## API At-a-glance

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Self-service customer registration |
| POST | `/auth/login` | OAuth2 password flow → JWT |
| GET  | `/auth/me` | Current user |
| POST | `/auth/change-password` | Change password |
| GET  | `/users`, `/users/agents` | List users (Admin/Supervisor) |
| POST/PUT/DELETE | `/users` | User management (Admin) |
| GET/POST/DELETE | `/categories` | Category management |
| POST | `/complaints` | Register a complaint |
| GET  | `/complaints` | List complaints (role-filtered) |
| GET  | `/complaints/{id}` | Get one |
| PUT  | `/complaints/{id}` | Status/assign/priority/comment update |
| GET  | `/complaints/{id}/history` | Audit trail |
| POST | `/complaints/sweep-escalations` | Auto-escalation sweep |
| POST | `/complaints/{id}/attachments` | Upload file (multipart) |
| GET  | `/complaints/{id}/attachments` | List files |
| GET  | `/complaints/{id}/attachments/{aid}/download` | Download |
| POST | `/complaints/{id}/feedback` | Submit rating + comments |
| GET  | `/notifications` | In-app notifications |
| POST | `/notifications/read-all` | Mark all read |
| GET  | `/dashboard/stats` | KPIs + breakdowns |

See [`docs/API.md`](docs/API.md) for full request/response examples.

---

## Role-Based Access Control (summary)

| Action | Customer | Agent | Supervisor | Admin |
|---|:-:|:-:|:-:|:-:|
| Register complaint | ✅ | ✅ | ✅ | ✅ |
| View own complaints | ✅ | ✅ | ✅ | ✅ |
| View all complaints | — | own assignments | ✅ | ✅ |
| Assign / reassign | — | — | ✅ | ✅ |
| Change priority | — | — | ✅ | ✅ |
| Update status | own → Closed | own assignments | ✅ | ✅ |
| Sweep escalations | — | — | ✅ | ✅ |
| Submit feedback | own | — | — | — |
| Manage users | — | — | view | ✅ |
| Manage categories | — | — | view | ✅ |

---

## Evaluation Mapping

| Criterion | Where |
|---|---|
| Frontend Development | `frontend/` — 10 pages, role-aware Navbar, RBAC routes, responsive CSS |
| Backend API Development | `backend/routers/` — 8 router files, ~35 endpoints |
| Authentication & RBAC | `backend/auth.py`, `frontend/src/context/AuthContext.js` |
| Database Integration | `backend/models.py`, `database/schema_*.sql` |
| CRUD | Books-equivalent CRUD on Complaints, Users, Categories, Feedback |
| Search & Filter | `/complaints?status=&priority=&search=` + UI filter bar |
| SLA & Escalation | `services/sla.py`, `auto_escalate_overdue` |
| ETL Pipeline | `etl/` — full Extract / Transform / Load / Export pipeline |
| Documentation | This README + `docs/API.md` + `docs/HLD.md` + `docs/DB_DESIGN.md` |

---

## ETL Pipeline

The `etl/` directory adds a standalone Python data pipeline that sits alongside the FastAPI application and operates directly on the same SQLite database.

### Why ETL?

The application captures live operational data but has no way to:
- **Ingest** historical or bulk complaint data from external sources (CSV / legacy systems)
- **Summarise** that data into analytics-ready tables without burdening the OLTP API
- **Publish** reports as downloadable CSV or Excel files for external stakeholders

The ETL pipeline solves all three.

---

### Pipeline Flow

```
                          CCRTS ETL PIPELINE
  ================================================================

  SOURCES                    STAGES                    TARGETS
  -------                    ------                    -------

  CSV Files                  EXTRACT                   pandas
  (complaints_import.csv) -->  extract_csv()        --> DataFrame
  (users_import.csv)           extract_*_from_db()
  Operational DB          -->                           DataFrame
  (ccrts.db)

                             TRANSFORM
                    +------------------------------+
                    | Import path:                 |
                    |  - validate required fields  |
                    |  - resolve FK lookups        |    clean
                    |    (email -> customer_id,    | --> DataFrame
                    |     name  -> category_id,    |
                    |     name  -> agent_id)        |
                    |  - calculate SLA deadline     |
                    |  - hash passwords (bcrypt)   |
                    |  - generate complaint number  |
                    +------------------------------+
                    | Analytics path:              |
                    |  - classify SLA status       |
                    |    (On Track / At Risk /     |    analytics
                    |     Breached / Met)          | --> dict of
                    |  - compute resolution hours  |    DataFrames
                    |  - aggregate by category     |
                    |  - aggregate by agent        |
                    |  - build daily stats         |
                    +------------------------------+

                              LOAD
                    +--------------------------+
                    | Operational tables:      |
                    |  complaints              | --> ccrts.db
                    |  complaint_history       |
                    |  users                   |
                    +--------------------------+
                    | ETL summary tables:      |
                    |  etl_run_log             |
                    |  etl_complaint_summary   | --> ccrts.db
                    |  etl_agent_performance   |
                    |  etl_daily_stats         |
                    |  etl_sla_analysis        |
                    +--------------------------+

                             EXPORT
                    +--------------------------+
                    |  complaints_export.csv   |
                    |  users_export.csv        | --> etl/exports/
                    |  analytics_report.xlsx   |
                    |   - Overview (KPIs)      |
                    |   - Category Summary     |
                    |   - Agent Performance    |
                    |   - Daily Stats          |
                    |   - SLA Analysis         |
                    |   - All Complaints       |
                    +--------------------------+

                          ETL RUN LOG
                    (every phase writes a row to
                     etl_run_log: status, records
                     extracted / transformed /
                     loaded, duration, errors)
```

---

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `config.py` | Central constants — database URL, SLA hours, valid statuses |
| `etl_models.py` | SQLAlchemy models for 5 ETL summary tables (`etl_` prefix) |
| `extract.py` | `extract_csv()` reads any delimiter-separated file; `extract_*_from_db()` queries the operational DB and returns typed DataFrames |
| `transform.py` | **Import path** — validates fields, resolves FK lookups, hashes passwords, generates complaint numbers, calculates SLA deadlines. **Analytics path** — SLA classification, resolution-hour calculation, category/agent/daily aggregations |
| `load.py` | `load_complaints()` / `load_users()` insert into operational tables; `upsert_summary_tables()` truncates and repopulates all ETL summary tables; `log_etl_run()` audits every phase |
| `export.py` | `export_complaints_csv()`, `export_users_csv()`, `export_analytics_excel()` — all output is timestamped and written to `etl/exports/` |
| `pipeline.py` | CLI entry point; `--import-complaints`, `--import-users`, `--analytics`, `--export`, `--all` flags; per-phase error recovery with `session.rollback()` |

---

### ETL Summary Tables

Five new tables are created in `ccrts.db` on first pipeline run:

| Table | Description |
|---|---|
| `etl_run_log` | Audit trail of every phase execution — status, record counts, duration, error details |
| `etl_complaint_summary` | Per-category counts: total, open, in-progress, resolved, escalated, SLA-breached, avg resolution hours |
| `etl_agent_performance` | Per-agent metrics: assigned, resolved, escalation count, avg resolution hours, avg feedback rating |
| `etl_daily_stats` | Daily complaint volume: created, resolved, escalated per calendar day, avg resolution hours |
| `etl_sla_analysis` | Per-complaint SLA classification: `On Track` / `At Risk` / `Breached` / `Met`, resolution hours |

---

### Quick Start

```bash
# 1. Install ETL dependencies (on top of backend deps)
pip install -r backend/requirements.txt
pip install -r etl/requirements.txt

# 2. Seed the database first (if not already done)
cd backend && python services/seed_data.py && cd ..

# 3a. Run the full pipeline with bundled sample data
python etl/pipeline.py --all

# 3b. Import your own complaints CSV
python etl/pipeline.py --import-complaints path/to/complaints.csv

# 3c. Refresh analytics summary tables only
python etl/pipeline.py --analytics

# 3d. Export all data to etl/exports/
python etl/pipeline.py --export

# 3e. Chain: import + analytics + export in one call
python etl/pipeline.py --import-complaints data.csv --analytics --export
```

### Sample Import CSV Columns

**complaints_import.csv** (required: `customer_email`, `subject`, `description`, `category_name`, `priority`):

| Column | Required | Notes |
|---|:-:|---|
| `customer_email` | Yes | Must match an existing Customer account |
| `subject` | Yes | Free text |
| `description` | Yes | Free text |
| `category_name` | Yes | Must match a category in the DB (case-insensitive) |
| `priority` | Yes | `Low` / `Medium` / `High` / `Critical` |
| `status` | No | Defaults to `Open` |
| `created_date` | No | ISO 8601 (`YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS`); defaults to now |
| `resolved_date` | No | ISO 8601; auto-calculated for `Resolved`/`Closed` rows if omitted |
| `assigned_agent_email` | No | Must match a Support Agent account |

**users_import.csv** (required: `name`, `email`, `role_name`, `password`):

| Column | Required | Notes |
|---|:-:|---|
| `name` | Yes | Display name |
| `email` | Yes | Must be unique; duplicates are skipped with a warning |
| `role_name` | Yes | `Admin` / `Supervisor` / `Support Agent` / `Customer` |
| `password` | Yes | Plain text in the CSV; bcrypt-hashed before insert |
| `phone` | No | Optional contact number |

---

### Export Outputs

Every export run writes three timestamped files to `etl/exports/`:

| File | Contents |
|---|---|
| `complaints_export_YYYYMMDD_HHMMSS.csv` | All complaints with customer/category names joined |
| `users_export_YYYYMMDD_HHMMSS.csv` | All users (password hashes excluded) |
| `analytics_report_YYYYMMDD_HHMMSS.xlsx` | 6-sheet workbook: Overview, Category Summary, Agent Performance, Daily Stats, SLA Analysis, All Complaints |

---

## Author

**Govind** — AFDE Capstone, Batch May 2026

## License

MIT
