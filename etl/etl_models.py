"""
SQLAlchemy models for ETL-specific summary and audit tables.

These tables live in the same database as the operational schema but are
prefixed with `etl_` to make their purpose clear.  They are created on
first pipeline run via ETLBase.metadata.create_all().
"""

from datetime import datetime

from sqlalchemy import Column, Float, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base

ETLBase = declarative_base()


class ETLRunLog(ETLBase):
    """One row per ETL phase execution — provides a complete audit trail."""

    __tablename__ = "etl_run_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), nullable=False)          # UUID shared by all phases in one run
    pipeline_name = Column(String(100), nullable=False)  # e.g. "import_complaints"
    phase = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running / success / failed
    records_extracted = Column(Integer, default=0)
    records_transformed = Column(Integer, default=0)
    records_loaded = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_details = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)


class ETLComplaintSummary(ETLBase):
    """Aggregated complaint counts and resolution metrics per category."""

    __tablename__ = "etl_complaint_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), unique=True, nullable=False)
    total_complaints = Column(Integer, default=0)
    open_count = Column(Integer, default=0)
    in_progress_count = Column(Integer, default=0)
    resolved_count = Column(Integer, default=0)
    closed_count = Column(Integer, default=0)
    escalated_count = Column(Integer, default=0)
    sla_breached_count = Column(Integer, default=0)
    avg_resolution_hours = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)


class ETLAgentPerformance(ETLBase):
    """Per-agent resolution metrics refreshed on each analytics run."""

    __tablename__ = "etl_agent_performance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, unique=True, nullable=False)
    agent_name = Column(String(150), nullable=False)
    agent_email = Column(String(150), nullable=False)
    total_assigned = Column(Integer, default=0)
    total_resolved = Column(Integer, default=0)
    escalation_count = Column(Integer, default=0)
    avg_resolution_hours = Column(Float, nullable=True)
    avg_feedback_rating = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)


class ETLDailyStats(ETLBase):
    """Daily complaint volume, resolution, and escalation counts."""

    __tablename__ = "etl_daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(String(10), unique=True, nullable=False)  # YYYY-MM-DD
    complaints_created = Column(Integer, default=0)
    complaints_resolved = Column(Integer, default=0)
    complaints_escalated = Column(Integer, default=0)
    avg_resolution_hours = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)


class ETLSLAAnalysis(ETLBase):
    """Per-complaint SLA classification — On Track / At Risk / Breached / Met."""

    __tablename__ = "etl_sla_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, unique=True, nullable=False)
    complaint_number = Column(String(20), nullable=False)
    priority = Column(String(20), nullable=False)
    sla_deadline = Column(DateTime, nullable=False)
    created_date = Column(DateTime, nullable=False)
    resolved_date = Column(DateTime, nullable=True)
    sla_status = Column(String(20), nullable=False)  # On Track / At Risk / Breached / Met
    resolution_hours = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
