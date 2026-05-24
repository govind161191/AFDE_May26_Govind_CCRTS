"""
Extract phase — read raw data from CSV files or the operational database.

All functions return pandas DataFrames with lower-snake-case column names.
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

# ── Path bootstrap ────────────────────────────────────────────────────────────
_backend = str(Path(__file__).parent.parent / "backend")
if _backend not in sys.path:
    sys.path.insert(0, _backend)

import models  # noqa: E402 — backend models

logger = logging.getLogger(__name__)


# ── CSV extraction ────────────────────────────────────────────────────────────

def extract_csv(filepath: str | Path) -> pd.DataFrame:
    """Read a CSV file into a DataFrame.

    Column names are lower-cased and spaces replaced with underscores so
    downstream code can use attribute-style access consistently.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV not found: {filepath}")

    logger.info("[EXTRACT] Reading CSV: %s", filepath)
    df = pd.read_csv(filepath, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.where(df != "", other=None)   # convert empty strings to None
    logger.info("[EXTRACT]   -> %d rows, %d columns", len(df), len(df.columns))
    return df


# ── Database extraction ───────────────────────────────────────────────────────

def extract_complaints_from_db(session: Session) -> pd.DataFrame:
    """Return all complaints joined with customer and category names."""
    logger.info("[EXTRACT] Loading complaints from database")

    rows = (
        session.query(
            models.Complaint,
            models.User.name.label("customer_name"),
            models.User.email.label("customer_email"),
            models.Category.category_name,
        )
        .join(models.User, models.User.user_id == models.Complaint.customer_id)
        .join(models.Category, models.Category.category_id == models.Complaint.category_id)
        .order_by(models.Complaint.created_date.desc())
        .all()
    )

    records = []
    for complaint, cust_name, cust_email, cat_name in rows:
        records.append({
            "complaint_id":        complaint.complaint_id,
            "complaint_number":    complaint.complaint_number,
            "customer_id":         complaint.customer_id,
            "customer_name":       cust_name,
            "customer_email":      cust_email,
            "assigned_agent_id":   complaint.assigned_agent_id,
            "category_id":         complaint.category_id,
            "category_name":       cat_name,
            "subject":             complaint.subject,
            "description":         complaint.description,
            "priority":            complaint.priority,
            "status":              complaint.status,
            "sla_deadline":        complaint.sla_deadline,
            "created_date":        complaint.created_date,
            "updated_date":        complaint.updated_date,
            "resolved_date":       complaint.resolved_date,
            "closed_date":         complaint.closed_date,
            "resolution_comment":  complaint.resolution_comment,
            "is_escalated":        complaint.is_escalated,
        })

    df = pd.DataFrame(records)
    if not df.empty:
        for col in ["sla_deadline", "created_date", "updated_date", "resolved_date", "closed_date"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    logger.info("[EXTRACT]   -> %d complaints", len(df))
    return df


def extract_feedback_from_db(session: Session) -> pd.DataFrame:
    """Return all feedback rows."""
    logger.info("[EXTRACT] Loading feedback from database")
    rows = session.query(models.Feedback).order_by(models.Feedback.complaint_id).all()
    records = [
        {
            "feedback_id":   f.feedback_id,
            "complaint_id":  f.complaint_id,
            "rating":        f.rating,
            "comments":      f.comments,
            "created_date":  f.created_date,
        }
        for f in rows
    ]
    df = pd.DataFrame(records)
    logger.info("[EXTRACT]   -> %d feedback records", len(df))
    return df


def extract_users_from_db(session: Session) -> pd.DataFrame:
    """Return all users joined with role names (password_hash excluded)."""
    logger.info("[EXTRACT] Loading users from database")
    rows = (
        session.query(models.User, models.Role.role_name)
        .join(models.Role, models.Role.role_id == models.User.role_id)
        .order_by(models.User.user_id)
        .all()
    )
    records = [
        {
            "user_id":      u.user_id,
            "name":         u.name,
            "email":        u.email,
            "role_name":    role_name,
            "phone":        u.phone,
            "created_date": u.created_date,
            "is_active":    u.is_active,
        }
        for u, role_name in rows
    ]
    df = pd.DataFrame(records)
    logger.info("[EXTRACT]   -> %d users", len(df))
    return df
