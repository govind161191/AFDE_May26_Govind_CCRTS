"""
Transform phase — validate, clean, enrich, and aggregate extracted data.

Two categories of transformations:
  1. Import transforms  — applied to CSV data before loading into operational tables
  2. Analytics transforms — applied to operational DB data to produce summary metrics
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy.orm import Session

# ── Path bootstrap ────────────────────────────────────────────────────────────
_backend = str(Path(__file__).parent.parent / "backend")
_etl = str(Path(__file__).parent)
for p in (_backend, _etl):
    if p not in sys.path:
        sys.path.insert(0, p)

import models  # noqa: E402
from config import (  # noqa: E402
    AT_RISK_BUFFER_HOURS,
    SLA_HOURS,
    TERMINAL_STATUSES,
    VALID_PRIORITIES,
    VALID_STATUSES,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Import transformations
# ─────────────────────────────────────────────────────────────────────────────

def _new_complaint_number(existing: set[str]) -> str:
    """Generate a collision-free complaint number."""
    while True:
        number = f"CMP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        if number not in existing:
            existing.add(number)
            return number


def transform_imported_complaints(
    df: pd.DataFrame,
    session: Session,
) -> tuple[pd.DataFrame, list[str]]:
    """Validate and enrich a raw complaint CSV DataFrame.

    Required CSV columns:
        customer_email, subject, description, category_name, priority

    Optional CSV columns:
        status (default: Open), created_date, resolved_date, assigned_agent_email

    Returns:
        (clean_df, errors)  — clean_df has the exact columns needed for load.py;
        errors is a list of human-readable row-level messages (warnings + skips).
    """
    errors: list[str] = []
    clean_rows: list[dict] = []
    now = datetime.utcnow()

    # Build lookup maps once
    categories: dict[str, int] = {
        c.category_name.lower(): c.category_id
        for c in session.query(models.Category).all()
    }
    customers: dict[str, int] = {
        u.email.lower(): u.user_id
        for u in (
            session.query(models.User)
            .join(models.Role)
            .filter(models.Role.role_name == "Customer")
            .all()
        )
    }
    agents: dict[str, int] = {
        u.email.lower(): u.user_id
        for u in (
            session.query(models.User)
            .join(models.Role)
            .filter(models.Role.role_name == "Support Agent")
            .all()
        )
    }
    existing_numbers: set[str] = {
        row[0]
        for row in session.query(models.Complaint.complaint_number).all()
    }

    for idx, row in df.iterrows():
        row_num = idx + 2   # 1-based; row 1 is the header

        # ── Required fields ──────────────────────────────────────────────────
        cust_email = (row.get("customer_email") or "").strip().lower()
        subject = (row.get("subject") or "").strip()
        description = (row.get("description") or "").strip()
        cat_raw = (row.get("category_name") or "").strip()
        priority = (row.get("priority") or "Medium").strip().title()
        status = (row.get("status") or "Open").strip()

        if not cust_email:
            errors.append(f"Row {row_num}: missing customer_email — skipped")
            continue
        if cust_email not in customers:
            errors.append(f"Row {row_num}: customer '{cust_email}' not found — skipped")
            continue
        if not subject:
            errors.append(f"Row {row_num}: missing subject — skipped")
            continue
        if not description:
            errors.append(f"Row {row_num}: missing description — skipped")
            continue
        if cat_raw.lower() not in categories:
            available = ", ".join(sorted(categories))
            errors.append(
                f"Row {row_num}: category '{cat_raw}' not found "
                f"(available: {available}) — skipped"
            )
            continue

        # ── Coerce / default optional fields ─────────────────────────────────
        if priority not in VALID_PRIORITIES:
            errors.append(f"Row {row_num}: invalid priority '{priority}', defaulted to Medium")
            priority = "Medium"
        if status not in VALID_STATUSES:
            errors.append(f"Row {row_num}: invalid status '{status}', defaulted to Open")
            status = "Open"

        # ── Dates ─────────────────────────────────────────────────────────────
        created_date = _parse_date(row.get("created_date"), now)
        if row.get("created_date") and created_date == now:
            errors.append(
                f"Row {row_num}: could not parse created_date '{row.get('created_date')}', using now"
            )

        sla_deadline = created_date + timedelta(hours=SLA_HOURS.get(priority, 48))

        # resolved_date from CSV or auto-derive for terminal statuses
        resolved_date = None
        closed_date = None
        resolved_raw = row.get("resolved_date")
        if resolved_raw:
            resolved_date = _parse_date(resolved_raw, None)
        elif status == "Resolved":
            resolved_date = created_date + timedelta(hours=SLA_HOURS.get(priority, 48) * 0.75)
        elif status == "Closed":
            resolved_date = created_date + timedelta(hours=SLA_HOURS.get(priority, 48) * 0.70)
            closed_date = created_date + timedelta(hours=SLA_HOURS.get(priority, 48) * 0.90)

        # ── Agent assignment ──────────────────────────────────────────────────
        agent_email_raw = (row.get("assigned_agent_email") or "").strip().lower()
        assigned_agent_id = agents.get(agent_email_raw) if agent_email_raw else None
        if agent_email_raw and assigned_agent_id is None:
            errors.append(
                f"Row {row_num}: agent '{agent_email_raw}' not found, left unassigned"
            )

        # Auto-progress to Assigned if an agent was supplied and status is Open
        if assigned_agent_id and status == "Open":
            status = "Assigned"

        clean_rows.append({
            "complaint_number":  _new_complaint_number(existing_numbers),
            "customer_id":       customers[cust_email],
            "assigned_agent_id": assigned_agent_id,
            "category_id":       categories[cat_raw.lower()],
            "subject":           subject,
            "description":       description,
            "priority":          priority,
            "status":            status,
            "sla_deadline":      sla_deadline,
            "created_date":      created_date,
            "updated_date":      created_date,
            "resolved_date":     resolved_date,
            "closed_date":       closed_date,
            "is_escalated":      status == "Escalated",
        })

    clean_df = pd.DataFrame(clean_rows)
    logger.info(
        "[TRANSFORM] Complaints: %d valid, %d error/warning", len(clean_df), len(errors)
    )
    return clean_df, errors


def transform_imported_users(
    df: pd.DataFrame,
    session: Session,
) -> tuple[pd.DataFrame, list[str]]:
    """Validate and hash-encode a raw users CSV DataFrame.

    Required CSV columns:
        name, email, role_name, password

    Optional CSV columns:
        phone
    """
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    errors: list[str] = []
    clean_rows: list[dict] = []

    roles: dict[str, int] = {
        r.role_name.lower(): r.role_id
        for r in session.query(models.Role).all()
    }
    existing_emails: set[str] = {
        row[0].lower()
        for row in session.query(models.User.email).all()
    }

    for idx, row in df.iterrows():
        row_num = idx + 2

        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip().lower()
        role_raw = (row.get("role_name") or "Customer").strip().lower()
        phone = (row.get("phone") or "").strip() or None
        password = (row.get("password") or "").strip()

        if not name:
            errors.append(f"Row {row_num}: missing name — skipped")
            continue
        if not email:
            errors.append(f"Row {row_num}: missing email — skipped")
            continue
        if not password:
            errors.append(f"Row {row_num}: missing password — skipped")
            continue
        if email in existing_emails:
            errors.append(f"Row {row_num}: email '{email}' already exists — skipped")
            continue
        if role_raw not in roles:
            available = ", ".join(sorted(roles))
            errors.append(
                f"Row {row_num}: role '{role_raw}' not found "
                f"(available: {available}) — skipped"
            )
            continue

        existing_emails.add(email)
        clean_rows.append({
            "name":          name,
            "email":         email,
            "password_hash": pwd_ctx.hash(password),
            "role_id":       roles[role_raw],
            "phone":         phone,
            "created_date":  datetime.utcnow(),
            "is_active":     True,
        })

    clean_df = pd.DataFrame(clean_rows)
    logger.info(
        "[TRANSFORM] Users: %d valid, %d error/warning", len(clean_df), len(errors)
    )
    return clean_df, errors


# ─────────────────────────────────────────────────────────────────────────────
# Analytics transformations
# ─────────────────────────────────────────────────────────────────────────────

def compute_analytics(session: Session) -> dict:
    """Extract all operational data and compute analytics DataFrames.

    Returns a dict with keys:
        overall           — dict of scalar KPIs
        category_summary  — DataFrame
        agent_performance — DataFrame
        daily_stats       — DataFrame
        sla_analysis      — DataFrame
        all_complaints    — DataFrame (full export-ready view)
    """
    from extract import extract_complaints_from_db, extract_feedback_from_db

    complaints_df = extract_complaints_from_db(session)
    feedback_df = extract_feedback_from_db(session)

    if complaints_df.empty:
        logger.warning("[TRANSFORM] No complaints found — analytics will be empty")
        _empty = pd.DataFrame()
        return {
            "overall": {},
            "category_summary": _empty,
            "agent_performance": _empty,
            "daily_stats": _empty,
            "sla_analysis": _empty,
            "all_complaints": _empty,
        }

    now = pd.Timestamp(datetime.utcnow())   # tz-naive to match DB storage

    # ── SLA classification ────────────────────────────────────────────────────
    def _classify_sla(row) -> str:
        status = row["status"]
        deadline = row["sla_deadline"]
        resolved = row["resolved_date"]

        if status in TERMINAL_STATUSES:
            if pd.notna(resolved):
                return "Breached" if resolved > deadline else "Met"
            return "Met"

        if pd.isna(deadline):
            return "Unknown"
        if now > deadline:
            return "Breached"
        if now + timedelta(hours=AT_RISK_BUFFER_HOURS) > deadline:
            return "At Risk"
        return "On Track"

    def _resolution_hours(row) -> float | None:
        if pd.notna(row["resolved_date"]) and pd.notna(row["created_date"]):
            delta = row["resolved_date"] - row["created_date"]
            return delta.total_seconds() / 3600
        return None

    complaints_df["sla_status"] = complaints_df.apply(_classify_sla, axis=1)
    complaints_df["resolution_hours"] = complaints_df.apply(_resolution_hours, axis=1)

    # ── SLA analysis table ────────────────────────────────────────────────────
    sla_analysis = complaints_df[[
        "complaint_id", "complaint_number", "priority",
        "sla_deadline", "created_date", "resolved_date",
        "sla_status", "resolution_hours",
    ]].copy()

    # ── Category summary ──────────────────────────────────────────────────────
    cat_rows: list[dict] = []
    for cat_name, grp in complaints_df.groupby("category_name"):
        resolved_mask = grp["status"].isin(TERMINAL_STATUSES) & grp["resolution_hours"].notna()
        cat_rows.append({
            "category_name":       cat_name,
            "total_complaints":    len(grp),
            "open_count":          int((grp["status"] == "Open").sum()),
            "in_progress_count":   int((grp["status"] == "In Progress").sum()),
            "resolved_count":      int((grp["status"] == "Resolved").sum()),
            "closed_count":        int((grp["status"] == "Closed").sum()),
            "escalated_count":     int(grp["is_escalated"].sum()),
            "sla_breached_count":  int((grp["sla_status"] == "Breached").sum()),
            "avg_resolution_hours": (
                float(grp.loc[resolved_mask, "resolution_hours"].mean())
                if resolved_mask.any() else None
            ),
        })
    category_summary = pd.DataFrame(cat_rows)

    # ── Agent performance ─────────────────────────────────────────────────────
    agent_complaints = complaints_df[complaints_df["assigned_agent_id"].notna()].copy()
    agent_rows: list[dict] = []
    if not agent_complaints.empty:
        agent_ids = agent_complaints["assigned_agent_id"].astype(int).unique().tolist()
        agent_map = {
            u.user_id: u
            for u in session.query(models.User).filter(models.User.user_id.in_(agent_ids)).all()
        }
        fb_map: dict[int, int] = (
            dict(zip(feedback_df["complaint_id"], feedback_df["rating"]))
            if not feedback_df.empty else {}
        )

        for agent_id, grp in agent_complaints.groupby("assigned_agent_id"):
            agent = agent_map.get(int(agent_id))
            resolved_mask = grp["status"].isin(TERMINAL_STATUSES) & grp["resolution_hours"].notna()
            ratings = [fb_map[cid] for cid in grp["complaint_id"] if cid in fb_map]
            agent_rows.append({
                "agent_id":            int(agent_id),
                "agent_name":          agent.name if agent else f"Agent #{agent_id}",
                "agent_email":         agent.email if agent else "",
                "total_assigned":      len(grp),
                "total_resolved":      int(grp["status"].isin(TERMINAL_STATUSES).sum()),
                "escalation_count":    int(grp["is_escalated"].sum()),
                "avg_resolution_hours": (
                    float(grp.loc[resolved_mask, "resolution_hours"].mean())
                    if resolved_mask.any() else None
                ),
                "avg_feedback_rating": float(sum(ratings) / len(ratings)) if ratings else None,
            })
    agent_performance = pd.DataFrame(agent_rows)

    # ── Daily stats ───────────────────────────────────────────────────────────
    complaints_df["created_day"] = complaints_df["created_date"].dt.strftime("%Y-%m-%d")
    complaints_df["resolved_day"] = complaints_df["resolved_date"].apply(
        lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else None
    )

    daily_created = complaints_df.groupby("created_day").size()
    daily_resolved = (
        complaints_df[complaints_df["resolved_day"].notna()]
        .groupby("resolved_day")
        .size()
    )
    daily_escalated = (
        complaints_df[complaints_df["is_escalated"]]
        .groupby("created_day")
        .size()
    )

    all_dates = sorted(
        set(list(daily_created.index)) |
        set(list(daily_resolved.index)) |
        set(list(daily_escalated.index))
    )

    daily_rows: list[dict] = []
    for d in all_dates:
        resolved_on_day = complaints_df.loc[
            complaints_df["resolved_day"] == d, "resolution_hours"
        ].dropna()
        daily_rows.append({
            "stat_date":            d,
            "complaints_created":   int(daily_created.get(d, 0)),
            "complaints_resolved":  int(daily_resolved.get(d, 0)),
            "complaints_escalated": int(daily_escalated.get(d, 0)),
            "avg_resolution_hours": (
                float(resolved_on_day.mean()) if not resolved_on_day.empty else None
            ),
        })
    daily_stats = pd.DataFrame(daily_rows)

    # ── Overall KPIs ──────────────────────────────────────────────────────────
    res_hours = complaints_df["resolution_hours"].dropna()
    overall = {
        "total_complaints":     int(len(complaints_df)),
        "open":                 int((complaints_df["status"] == "Open").sum()),
        "assigned":             int((complaints_df["status"] == "Assigned").sum()),
        "in_progress":          int((complaints_df["status"] == "In Progress").sum()),
        "pending_response":     int((complaints_df["status"] == "Pending Customer Response").sum()),
        "resolved":             int((complaints_df["status"] == "Resolved").sum()),
        "closed":               int((complaints_df["status"] == "Closed").sum()),
        "escalated":            int(complaints_df["is_escalated"].sum()),
        "sla_breached":         int((complaints_df["sla_status"] == "Breached").sum()),
        "sla_at_risk":          int((complaints_df["sla_status"] == "At Risk").sum()),
        "sla_on_track":         int((complaints_df["sla_status"] == "On Track").sum()),
        "sla_met":              int((complaints_df["sla_status"] == "Met").sum()),
        "avg_resolution_hours": float(res_hours.mean()) if not res_hours.empty else None,
        "total_feedback":       int(len(feedback_df)),
        "avg_feedback_rating":  (
            float(feedback_df["rating"].mean()) if not feedback_df.empty else None
        ),
    }

    logger.info(
        "[TRANSFORM] Analytics: %d complaints | %d categories | %d agents | %d days",
        len(complaints_df), len(category_summary), len(agent_performance), len(daily_stats),
    )

    return {
        "overall":            overall,
        "category_summary":   category_summary,
        "agent_performance":  agent_performance,
        "daily_stats":        daily_stats,
        "sla_analysis":       sla_analysis,
        "all_complaints":     complaints_df,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_date(value: str | None, fallback: datetime | None) -> datetime | None:
    """Try to parse an ISO-format date string; return fallback on failure."""
    if not value:
        return fallback
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return fallback
