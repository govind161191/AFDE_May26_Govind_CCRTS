# High-Level Design

## 1. Architecture

The system follows a 3-tier architecture:

```
┌─────────────────────────────────────────────────┐
│  Presentation Tier — React SPA (port 3000)      │
│  - AuthContext owns JWT + current user          │
│  - ProtectedRoute enforces role-based routing   │
│  - Axios interceptor injects Bearer token       │
│  - Pages: Login, Dashboard, Complaints (list,   │
│    detail, register), Queue, Escalations,       │
│    Reports, Users                               │
└─────────────────────────────────────────────────┘
                       │  HTTPS / JSON
                       ▼
┌─────────────────────────────────────────────────┐
│  Application Tier — FastAPI (port 8000)         │
│  - Routers per resource                         │
│  - auth.py: JWT issuance, OAuth2PasswordBearer, │
│    require_roles(...) dependency factory        │
│  - CRUD layer (pure DB ops)                     │
│  - Services: sla, notifications                 │
└─────────────────────────────────────────────────┘
                       │  SQLAlchemy ORM
                       ▼
┌─────────────────────────────────────────────────┐
│  Data Tier — SQLite (default) / PostgreSQL      │
│  Tables: roles, users, categories, complaints,  │
│  complaint_history, attachments, feedback,      │
│  notifications                                  │
└─────────────────────────────────────────────────┘
```

## 2. Authentication & Authorization

- Passwords hashed with **bcrypt** (passlib).
- JWT issued at login (`/auth/login`), HS256, default TTL 8h, carries `sub` (user_id) and `role` claims.
- `OAuth2PasswordBearer` extracts the token; `get_current_user` validates it and loads the user.
- `require_roles("Admin", "Supervisor")` is a dependency factory used per-endpoint.
- Public registration is hard-coded to the **Customer** role.
- Frontend: `AuthContext` persists `{ token, user }` to localStorage; Axios injects the token on every request.

## 3. Complaint Lifecycle (state machine)

```
            ┌────────────────────────────────┐
            ▼                                │
   Open ──► Assigned ──► In Progress ──► Pending Customer Response
                                  │
                                  ├─► Escalated ───────┐
                                  │                    ▼
                                  └─► Resolved ──► Closed
```

- Transitions are validated by the backend (`VALID_STATUSES`) and persisted in `complaint_history`.
- Each status change creates a notification for the customer and (when applicable) the assigned agent.
- Auto-escalation: `auto_escalate_overdue` selects unresolved complaints whose `sla_deadline < now()` and flips them to `Escalated`.

## 4. SLA Policy

Resolution-time targets, computed at creation and on every priority change:

| Priority | SLA |
|---|---|
| Critical | 4 h |
| High | 24 h |
| Medium | 48 h |
| Low | 72 h |

`sla_deadline = created_date + SLA(priority)`. The `sla_breached` flag in API responses is derived on every read so a "breach" never gets stale.

## 5. Notifications

- Single `notifications` table indexed on `(user_id, is_read)`.
- Services emit notifications for: complaint created, assigned, status changed, escalated.
- The React `NotificationBell` polls every 30 seconds and exposes an unread-count badge.

## 6. Data Flow — Customer files a complaint

```
React (Customer)
   │ POST /complaints  { category_id, subject, description, priority }
   ▼
FastAPI complaints_router → crud.create_complaint
   │ INSERT complaint (status=Open)
   │ INSERT complaint_history (None → Open)
   │ Notify customer + every Supervisor
   ▼
SQLite
   │
   ▲
Notification bell polling for customer + supervisors
```

## 7. Non-Functional

| Concern | How |
|---|---|
| Performance | Indexed FKs and `status`; eager-loaded relations in CRUD |
| Security | bcrypt + JWT, RBAC dependencies per endpoint, parameterized queries via ORM |
| Reliability | Pydantic input validation, FastAPI structured error responses |
| Scalability | Stateless API + swappable DATABASE_URL; no server-side session |
| Usability | Responsive CSS, role-aware navigation, in-app notifications |

## 8. Deployment Sketch (out of Phase 1 scope but designed for)

- Containerize backend (`Dockerfile`), serve frontend `npm run build` from a CDN or nginx
- Promote DB from SQLite to managed PostgreSQL via `DATABASE_URL`
- Move attachments to object storage (S3/GCS) by abstracting `attachments_router.upload`
- Add a Celery / APScheduler worker that calls `auto_escalate_overdue` every 15 minutes
