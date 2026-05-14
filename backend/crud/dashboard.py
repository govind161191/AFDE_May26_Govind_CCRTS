"""Dashboard aggregates."""

from datetime import datetime
from sqlalchemy import func, case
from sqlalchemy.orm import Session

import models
from services.sla import is_breached


def compute_dashboard(db: Session) -> dict:
    total = db.query(func.count(models.Complaint.complaint_id)).scalar() or 0

    def count_status(s):
        return db.query(func.count(models.Complaint.complaint_id)).filter(
            models.Complaint.status == s
        ).scalar() or 0

    open_ct = count_status("Open") + count_status("Assigned")
    in_progress = count_status("In Progress") + count_status("Pending Customer Response")
    resolved = count_status("Resolved")
    closed = count_status("Closed")
    escalated = count_status("Escalated")

    # SLA breaches — anything past deadline & not resolved/closed
    open_complaints = db.query(models.Complaint).filter(
        models.Complaint.status.notin_(("Resolved", "Closed"))
    ).all()
    sla_breaches = sum(1 for c in open_complaints if is_breached(c.sla_deadline, c.status))

    # Average resolution time (hours)
    resolved_complaints = db.query(models.Complaint).filter(
        models.Complaint.resolved_date.isnot(None)
    ).all()
    if resolved_complaints:
        deltas = [(c.resolved_date - c.created_date).total_seconds() / 3600.0
                  for c in resolved_complaints]
        avg_hours = round(sum(deltas) / len(deltas), 2)
    else:
        avg_hours = None

    # By category
    by_category_q = (
        db.query(models.Category.category_name, func.count(models.Complaint.complaint_id))
        .join(models.Complaint, models.Complaint.category_id == models.Category.category_id)
        .group_by(models.Category.category_name)
        .all()
    )
    by_category = [{"category": cat, "count": cnt} for cat, cnt in by_category_q]

    # By priority
    by_priority_q = (
        db.query(models.Complaint.priority, func.count(models.Complaint.complaint_id))
        .group_by(models.Complaint.priority)
        .all()
    )
    by_priority = [{"category": p, "count": c} for p, c in by_priority_q]

    # Agent performance
    agents = db.query(models.User).join(models.Role).filter(
        models.Role.role_name == models.ROLE_AGENT
    ).all()
    agent_perf = []
    for agent in agents:
        assigned = db.query(func.count(models.Complaint.complaint_id)).filter(
            models.Complaint.assigned_agent_id == agent.user_id
        ).scalar() or 0
        resolved_by = db.query(func.count(models.Complaint.complaint_id)).filter(
            models.Complaint.assigned_agent_id == agent.user_id,
            models.Complaint.status.in_(("Resolved", "Closed")),
        ).scalar() or 0
        breaches = sum(
            1 for c in db.query(models.Complaint).filter(
                models.Complaint.assigned_agent_id == agent.user_id,
                models.Complaint.status.notin_(("Resolved", "Closed")),
            ).all()
            if is_breached(c.sla_deadline, c.status)
        )
        agent_perf.append({
            "agent_id": agent.user_id,
            "agent_name": agent.name,
            "assigned": assigned,
            "resolved": resolved_by,
            "sla_breaches": breaches,
        })

    return {
        "total_complaints": total,
        "open_complaints": open_ct,
        "in_progress_complaints": in_progress,
        "resolved_complaints": resolved,
        "closed_complaints": closed,
        "escalated_complaints": escalated,
        "sla_breaches": sla_breaches,
        "avg_resolution_hours": avg_hours,
        "by_category": by_category,
        "by_priority": by_priority,
        "agent_performance": agent_perf,
    }
