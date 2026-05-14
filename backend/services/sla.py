"""
SLA logic — translates priority into a resolution deadline and detects
breaches for escalation.

Per the spec:
    Critical : 4 hours
    High     : 24 hours
    Medium   : 48 hours
    Low      : 72 hours
"""

from datetime import datetime, timedelta
from typing import Optional


SLA_HOURS = {
    "Critical": 4,
    "High": 24,
    "Medium": 48,
    "Low": 72,
}


def deadline_for(priority: str, created_at: Optional[datetime] = None) -> datetime:
    """Return the SLA deadline for a complaint given its priority."""
    hours = SLA_HOURS.get(priority, 48)
    base = created_at or datetime.utcnow()
    return base + timedelta(hours=hours)


def is_breached(deadline: datetime, status: str) -> bool:
    """A complaint is in SLA breach if it isn't closed/resolved and the
    deadline has passed."""
    if status in ("Resolved", "Closed"):
        return False
    return datetime.utcnow() > deadline
