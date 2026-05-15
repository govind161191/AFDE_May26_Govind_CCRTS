# Setup Guide

## Prerequisites

| Tool | Min version | Check |
|---|---|---|
| Python | 3.10 | `python --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| Git | any | `git --version` |

## 1. Clone

```bash
git clone https://github.com/<your-username>/AFDE_May26_Govind_CCRTS.git
cd AFDE_May26_Govind_CCRTS
```

## 2. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Seed roles, categories, demo users, sample complaints
python services/seed_data.py

# Run
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs for Swagger UI.

## 3. Frontend

```bash
cd frontend
npm install
npm start
```

Open http://localhost:3000 and log in with one of the demo accounts printed by `seed_data.py`.

## 4. PostgreSQL (optional)

```bash
createdb ccrts_db
psql -d ccrts_db -f ../database/schema_postgres.sql
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost/ccrts_db"
uvicorn main:app --reload
```

## 5. Configuration

| Env var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./ccrts.db` | SQLAlchemy URL |
| `CCRTS_SECRET_KEY` | dev-only fallback | JWT signing key (**override in production**) |
| `CCRTS_TOKEN_EXPIRE_MINUTES` | 480 | Access token TTL |
| `CCRTS_UPLOAD_DIR` | `./uploads` | Where attachments are written |

## 6. Troubleshooting

**"value is not a valid email address" on login**
Emails like `name@host.local` are blocked by Pydantic's email validator (it considers `.local` a special-use TLD). Use a real-looking domain.

**`401 Unauthorized` after a long session**
Tokens expire after 8 hours. Log in again — the frontend will redirect you.

**Bcrypt warning at startup**
Harmless `passlib`-vs-`bcrypt` version chatter; we pin `bcrypt==4.0.1` in `requirements.txt` to silence it.

**Backend can't write `ccrts.db`**
Run uvicorn from inside `backend/`, so the relative SQLite path resolves correctly.
