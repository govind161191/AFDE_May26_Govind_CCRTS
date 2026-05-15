# Database Design

## Entity-Relationship overview

```
roles ──┐
        │ 1-N
        ▼
       users ◄────┬──────────────────────────────────┐
        │ 1-N    │ N-1 (customer)                    │ N-1 (agent)
        ▼        │                                   │
   notifications │                                   │
                 └──┐                                ┘
                    ▼
              complaints ─── N-1 ─── categories
                  │ 1-N
                  ├──► complaint_history ── N-1 ── users (updated_by)
                  ├──► attachments        ── N-1 ── users (uploaded_by)
                  └──► feedback (1-1)
```

## Tables

### `roles`
| Column | Type | Notes |
|---|---|---|
| role_id | INTEGER PK | autoincrement |
| role_name | VARCHAR(50) UNIQUE | Admin / Supervisor / Support Agent / Customer |

### `users`
| Column | Type | Notes |
|---|---|---|
| user_id | INTEGER PK | autoincrement |
| name | VARCHAR(150) | |
| email | VARCHAR(150) UNIQUE | indexed |
| password_hash | VARCHAR(255) | bcrypt |
| role_id | INTEGER FK → roles | |
| phone | VARCHAR(20) | nullable |
| is_active | BOOLEAN | default true |
| created_date | TIMESTAMP | |

### `categories`
| Column | Type | Notes |
|---|---|---|
| category_id | INTEGER PK | |
| category_name | VARCHAR(100) UNIQUE | |
| description | VARCHAR(255) | nullable |

### `complaints`
| Column | Type | Notes |
|---|---|---|
| complaint_id | INTEGER PK | |
| complaint_number | VARCHAR(20) UNIQUE | `CMP-YYYYMMDD-XXXXXX` |
| customer_id | INTEGER FK → users | indexed |
| assigned_agent_id | INTEGER FK → users | nullable, indexed |
| category_id | INTEGER FK → categories | |
| subject | VARCHAR(255) | |
| description | TEXT | |
| priority | VARCHAR(20) | Low / Medium / High / Critical |
| status | VARCHAR(40) | indexed |
| sla_deadline | TIMESTAMP | computed at create/priority-change |
| created_date | TIMESTAMP | |
| updated_date | TIMESTAMP | auto-updated |
| resolved_date | TIMESTAMP | nullable |
| closed_date | TIMESTAMP | nullable |
| resolution_comment | TEXT | nullable |
| is_escalated | BOOLEAN | default false |

### `complaint_history`
| Column | Type | Notes |
|---|---|---|
| history_id | INTEGER PK | |
| complaint_id | INTEGER FK → complaints | ON DELETE CASCADE |
| updated_by | INTEGER FK → users | |
| old_status | VARCHAR(40) | nullable (creation row) |
| new_status | VARCHAR(40) | |
| comment | TEXT | nullable |
| updated_date | TIMESTAMP | |

### `attachments`
| Column | Type | Notes |
|---|---|---|
| attachment_id | INTEGER PK | |
| complaint_id | INTEGER FK → complaints | ON DELETE CASCADE |
| file_name | VARCHAR(255) | original |
| file_path | VARCHAR(500) | local disk path |
| content_type | VARCHAR(100) | nullable |
| uploaded_by | INTEGER FK → users | |
| uploaded_date | TIMESTAMP | |

### `feedback`
| Column | Type | Notes |
|---|---|---|
| feedback_id | INTEGER PK | |
| complaint_id | INTEGER FK → complaints UNIQUE | ON DELETE CASCADE |
| rating | INTEGER | CHECK 1..5 |
| comments | TEXT | nullable |
| created_date | TIMESTAMP | |

### `notifications`
| Column | Type | Notes |
|---|---|---|
| notification_id | INTEGER PK | |
| user_id | INTEGER FK → users | indexed |
| complaint_id | INTEGER FK → complaints | nullable, ON DELETE SET NULL |
| message | VARCHAR(500) | |
| is_read | BOOLEAN | default false, indexed with user_id |
| created_date | TIMESTAMP | |

## Indexes & Constraints

- `users(email)` UNIQUE
- `complaints(complaint_number)` UNIQUE
- `feedback(complaint_id)` UNIQUE
- Composite index on `notifications(user_id, is_read)` for the bell query
- All FKs have explicit `ON DELETE` behavior (`CASCADE` for owned children, `SET NULL` for soft links)

## Why this design

- **Audit trail in its own table** rather than versioned rows on `complaints` keeps the main table compact while letting us reconstruct full history.
- **Role table** (rather than enum) so a future iteration can add roles without a migration that mutates columns.
- **`sla_deadline` stored** rather than computed on read because (a) priority can change later and (b) it lets us index/filter directly for sweeps.
- **`is_escalated` flag in addition to `status="Escalated"`** so we still know a complaint was escalated after a supervisor moves it back to In Progress.
