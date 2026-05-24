"""
Load phase — write transformed data into operational and ETL summary tables.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

# ── Path bootstrap ────────────────────────────────────────────────────────────
_backend = str(Path(__file__).parent.parent / "backend")
_etl = str(Path(__file__).parent)
for p in (_backend, _etl):
    if p not in sys.path:
        sys.path.insert(0, p)

import models  # noqa: E402
from etl_models import (  # noqa: E402
    ETLAgentPerformance,
    ETLComplaintSummary,
    ETLDailyStats,
    ETLRunLog,
    ETLSLAAnalysis,
)

logger = logging.getLogger(__name__)


# ── Operational loaders ───────────────────────────────────────────────────────

def load_users(session: Session, df: pd.DataFrame) -> int:
    """Bulk-insert validated user rows into the `users` table."""
    if df.empty:
        return 0
    count = 0
    for _, row in df.iterrows():
        user = models.User(
            name=row["name"],
            email=row["email"],
            password_hash=row["password_hash"],
            role_id=int(row["role_id"]),
            phone=row.get("phone"),
            created_date=row.get("created_date") or datetime.utcnow(),
            is_active=bool(row.get("is_active", True)),
        )
        session.add(user)
        count += 1
    session.commit()
    logger.info("[LOAD] Users: %d rows inserted", count)
    return count


def load_complaints(session: Session, df: pd.DataFrame) -> int:
    """Bulk-insert validated complaint rows and seed their initial history entry."""
    if df.empty:
        return 0
    count = 0
    for _, row in df.iterrows():
        agent_id = _nullable_int(row.get("assigned_agent_id"))
        c = models.Complaint(
            complaint_number=str(row["complaint_number"]),
            customer_id=_safe_int(row["customer_id"]),
            assigned_agent_id=agent_id,
            category_id=_safe_int(row["category_id"]),
            subject=str(row["subject"]),
            description=str(row["description"]),
            priority=str(row["priority"]),
            status=str(row["status"]),
            sla_deadline=_to_native_dt(row["sla_deadline"]),
            created_date=_to_native_dt(row.get("created_date")) or datetime.utcnow(),
            updated_date=_to_native_dt(row.get("updated_date")) or datetime.utcnow(),
            resolved_date=_nullable_dt(row.get("resolved_date")),
            closed_date=_nullable_dt(row.get("closed_date")),
            is_escalated=bool(row.get("is_escalated", False)),
        )
        session.add(c)
        session.flush()   # populate complaint_id before creating history

        session.add(models.ComplaintHistory(
            complaint_id=c.complaint_id,
            updated_by=_safe_int(row["customer_id"]),
            old_status=None,
            new_status=str(row["status"]),
            comment="Imported via ETL pipeline",
        ))
        count += 1

    session.commit()
    logger.info("[LOAD] Complaints: %d rows inserted", count)
    return count


# ── ETL summary table loaders ─────────────────────────────────────────────────

def upsert_summary_tables(session: Session, analytics: dict) -> int:
    """Replace all ETL summary table data with freshly computed analytics."""
    now = datetime.utcnow()
    total = 0

    # Category summary
    cat_df: pd.DataFrame = analytics.get("category_summary", pd.DataFrame())
    if not cat_df.empty:
        session.query(ETLComplaintSummary).delete()
        for _, row in cat_df.iterrows():
            session.add(ETLComplaintSummary(
                category_name=row["category_name"],
                total_complaints=int(row.get("total_complaints", 0)),
                open_count=int(row.get("open_count", 0)),
                in_progress_count=int(row.get("in_progress_count", 0)),
                resolved_count=int(row.get("resolved_count", 0)),
                closed_count=int(row.get("closed_count", 0)),
                escalated_count=int(row.get("escalated_count", 0)),
                sla_breached_count=int(row.get("sla_breached_count", 0)),
                avg_resolution_hours=_nullable_float(row.get("avg_resolution_hours")),
                last_updated=now,
            ))
            total += 1
        session.commit()

    # Agent performance
    agent_df: pd.DataFrame = analytics.get("agent_performance", pd.DataFrame())
    if not agent_df.empty:
        session.query(ETLAgentPerformance).delete()
        for _, row in agent_df.iterrows():
            session.add(ETLAgentPerformance(
                agent_id=int(row["agent_id"]),
                agent_name=row["agent_name"],
                agent_email=row["agent_email"],
                total_assigned=int(row.get("total_assigned", 0)),
                total_resolved=int(row.get("total_resolved", 0)),
                escalation_count=int(row.get("escalation_count", 0)),
                avg_resolution_hours=_nullable_float(row.get("avg_resolution_hours")),
                avg_feedback_rating=_nullable_float(row.get("avg_feedback_rating")),
                last_updated=now,
            ))
            total += 1
        session.commit()

    # Daily stats
    daily_df: pd.DataFrame = analytics.get("daily_stats", pd.DataFrame())
    if not daily_df.empty:
        session.query(ETLDailyStats).delete()
        for _, row in daily_df.iterrows():
            session.add(ETLDailyStats(
                stat_date=row["stat_date"],
                complaints_created=int(row.get("complaints_created", 0)),
                complaints_resolved=int(row.get("complaints_resolved", 0)),
                complaints_escalated=int(row.get("complaints_escalated", 0)),
                avg_resolution_hours=_nullable_float(row.get("avg_resolution_hours")),
                last_updated=now,
            ))
            total += 1
        session.commit()

    # SLA analysis
    sla_df: pd.DataFrame = analytics.get("sla_analysis", pd.DataFrame())
    if not sla_df.empty:
        session.query(ETLSLAAnalysis).delete()
        for _, row in sla_df.iterrows():
            session.add(ETLSLAAnalysis(
                complaint_id=int(row["complaint_id"]),
                complaint_number=row["complaint_number"],
                priority=row["priority"],
                sla_deadline=_to_native_dt(row["sla_deadline"]),
                created_date=_to_native_dt(row["created_date"]),
                resolved_date=_nullable_dt(row.get("resolved_date")),
                sla_status=row["sla_status"],
                resolution_hours=_nullable_float(row.get("resolution_hours")),
                last_updated=now,
            ))
            total += 1
        session.commit()

    logger.info("[LOAD] Summary tables: %d records written", total)
    return total


def log_etl_run(session: Session, run_data: dict) -> None:
    """Append a record to etl_run_log."""
    session.add(ETLRunLog(**run_data))
    session.commit()


# ── Private helpers ───────────────────────────────────────────────────────────

def _safe_int(val) -> int:
    """Convert a value to Python int; raises on NaN/None."""
    if val is None or (isinstance(val, float) and val != val):
        raise ValueError(f"Expected integer, got {val!r}")
    return int(val)


def _nullable_int(val) -> int | None:
    """Convert to int or None; treats NaN/None as None."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if (f != f) else int(f)   # NaN -> None
    except (TypeError, ValueError):
        return None


def _nullable_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return None if (f != f) else f   # NaN -> None
    except (TypeError, ValueError):
        return None


def _nullable_dt(val) -> datetime | None:
    if val is None:
        return None
    # pd.NaT, float NaN, and similar "missing" sentinels
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, pd.Timestamp):
        return val.to_pydatetime()
    if isinstance(val, datetime):
        return val
    return None


def _to_native_dt(val) -> datetime | None:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, pd.Timestamp):
        return val.to_pydatetime()
    if isinstance(val, datetime):
        return val
    return None
