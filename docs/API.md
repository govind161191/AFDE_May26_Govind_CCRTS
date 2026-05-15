# API Reference

Base URL: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`

All non-auth endpoints require `Authorization: Bearer <token>`.
Timestamps are UTC ISO-8601.

---

## Authentication

### `POST /auth/register`

Creates a Customer account. Self-service requests for higher roles are silently coerced to Customer.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","email":"jane@example.com","password":"pwd1234","phone":"5550100"}'
```

### `POST /auth/login`

OAuth2 password flow — `username` field carries the email.

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=govind@example.com&password=Customer@123"
```

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "user_id": 5, "name": "Govind Kumar", "email": "govind@example.com",
    "role_name": "Customer", "is_active": true, "created_date": "..."
  }
}
```

### `GET /auth/me`
Returns the authenticated user.

### `POST /auth/change-password`
Body: `{ "current_password": "...", "new_password": "..." }`.

---

## Users (Admin / Supervisor)

```
GET    /users              # list (?role=Customer to filter)
GET    /users/agents       # Support Agents only
POST   /users              # Admin: create with any role
PUT    /users/{id}         # Admin: name/phone/is_active/role_name
DELETE /users/{id}         # Admin: delete
```

---

## Categories

```
GET    /categories         # any authenticated user
POST   /categories         # Admin: { category_name, description? }
DELETE /categories/{id}    # Admin
```

---

## Complaints

### `POST /complaints`
```json
{
  "category_id": 1,
  "subject": "Duplicate charge on May invoice",
  "description": "I was charged twice on May 5...",
  "priority": "High"
}
```
Returns 201 with the created `ComplaintOut`, including the auto-generated `complaint_number` and `sla_deadline`.

### `GET /complaints`
Optional query params: `status`, `priority`, `category_id`, `escalated`, `search`.
The list is **automatically filtered by role**:
- Customer → only their own
- Support Agent → only assignments
- Supervisor/Admin → all

### `GET /complaints/{id}`
Returns `ComplaintOut` with derived fields:
- `customer_name`, `assigned_agent_name`, `category_name`
- `sla_breached` (boolean — convenience for the UI)

### `PUT /complaints/{id}`
Partial update. Role-gated body fields:
```json
{
  "status": "Resolved",
  "assigned_agent_id": 3,
  "priority": "High",
  "resolution_comment": "Refund processed in batch 220",
  "comment": "Routing back to billing team"
}
```
- Customers can only set status `Pending Customer Response` or `Closed` on their own complaints.
- Agents can only update complaints assigned to them (no reassignment, no priority change).
- Supervisors / Admins: anything.

### `DELETE /complaints/{id}` *(Admin)*

### `GET /complaints/{id}/history`
Full audit trail with `updated_by_name` and the old → new status.

### `POST /complaints/sweep-escalations`  *(Admin / Supervisor)*
Marks every unresolved past-deadline complaint as `Escalated`, writes history rows, and notifies supervisors. Returns `{ "escalated": N }`.

---

## Attachments

```
POST   /complaints/{id}/attachments                    # multipart/form-data
GET    /complaints/{id}/attachments
GET    /complaints/{id}/attachments/{aid}/download
```

10 MB per file. Access is restricted to the customer, assigned agent, and supervisors/admins.

---

## Feedback

```
POST /complaints/{id}/feedback     # customer only, after Resolved/Closed
GET  /complaints/{id}/feedback
```
Body:
```json
{ "rating": 5, "comments": "Great service" }
```

Rating must be 1–5. One feedback per complaint.

---

## Notifications

```
GET  /notifications?unread_only=false
POST /notifications/{id}/read
POST /notifications/read-all
```

Limited to 100 most-recent.

---

## Dashboard

### `GET /dashboard/stats` *(Admin / Supervisor / Support Agent)*

```json
{
  "total_complaints": 12,
  "open_complaints": 4,
  "in_progress_complaints": 2,
  "resolved_complaints": 5,
  "closed_complaints": 1,
  "escalated_complaints": 2,
  "sla_breaches": 1,
  "avg_resolution_hours": 17.4,
  "by_category": [{ "category": "Billing Issues", "count": 5 }, ...],
  "by_priority": [{ "category": "High", "count": 6 }, ...],
  "agent_performance": [
    { "agent_id": 3, "agent_name": "Alex Agent", "assigned": 4, "resolved": 3, "sla_breaches": 0 }
  ]
}
```

---

## SLA Policy

| Priority | Resolution time |
|---|---|
| Critical | 4 hours |
| High | 24 hours |
| Medium | 48 hours |
| Low | 72 hours |

Computed at create / priority-change. Past-deadline open complaints can be auto-escalated via `POST /complaints/sweep-escalations`.

---

## Error format

```json
{ "detail": "Book not available for borrowing" }
```

`422` errors return Pydantic's structured `loc/msg/type` validation list.

---

## CORS

Allowed origins out of the box:
- `http://localhost:3000` (Create React App)
- `http://localhost:5173` (Vite, future-proofing)
