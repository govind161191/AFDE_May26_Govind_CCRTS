"""
ETL pipeline configuration.

Override defaults via environment variables:
  CCRTS_DB_PATH   — absolute path to ccrts.db
  DATABASE_URL    — full SQLAlchemy URL (takes precedence over CCRTS_DB_PATH)
  ETL_LOG_LEVEL   — logging level (default: INFO)
"""

import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent                        # project root
BACKEND_DIR = BASE_DIR / "backend"
ETL_DIR = Path(__file__).parent
EXPORT_DIR = ETL_DIR / "exports"
SAMPLE_DIR = ETL_DIR / "sample_data"

# ── Database ──────────────────────────────────────────────────────────────────

_db_path = os.environ.get("CCRTS_DB_PATH", str(BACKEND_DIR / "ccrts.db"))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_db_path}")

# ── Domain constants (must stay in sync with backend/services/sla.py) ────────

SLA_HOURS: dict[str, int] = {
    "Critical": 4,
    "High": 24,
    "Medium": 48,
    "Low": 72,
}

VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]

VALID_STATUSES = [
    "Open",
    "Assigned",
    "In Progress",
    "Pending Customer Response",
    "Escalated",
    "Resolved",
    "Closed",
]

TERMINAL_STATUSES = {"Resolved", "Closed"}

# How many hours before the deadline a complaint is flagged "At Risk"
AT_RISK_BUFFER_HOURS = 4

# ── Misc ──────────────────────────────────────────────────────────────────────

LOG_LEVEL: str = os.environ.get("ETL_LOG_LEVEL", "INFO")
