"""
In-app notification service.

Notifications are created in the DB and surfaced via /notifications.
This service centralizes notification creation so routers stay tidy.
"""

from typing import Optional
from sqlalchemy.orm import Session

import models


def notify(db: Session, user_id: int, message: str, complaint_id: Optional[int] = None) -> models.Notification:
    """Create a single notification (caller commits)."""
    n = models.Notification(user_id=user_id, complaint_id=complaint_id, message=message)
    db.add(n)
    return n


def notify_complaint_created(db: Session, complaint: models.Complaint):
    """Notify the customer that their complaint was registered."""
    notify(
        db, complaint.customer_id,
        f"Complaint {complaint.complaint_number} registered successfully.",
        complaint.complaint_id,
    )
    # Notify all supervisors so they can assign / monitor
    supervisors = db.query(models.User).join(models.Role).filter(
        models.Role.role_name == models.ROLE_SUPERVISOR, models.User.is_active == True  # noqa: E712
    ).all()
    for sup in supervisors:
        notify(
            db, sup.user_id,
            f"New {complaint.priority}-priority complaint {complaint.complaint_number}: {complaint.subject}",
            complaint.complaint_id,
        )


def notify_assignment(db: Session, complaint: models.Complaint, agent_id: int):
    """Tell the agent and the customer about a new assignment."""
    notify(
        db, agent_id,
        f"Complaint {complaint.complaint_number} has been assigned to you.",
        complaint.complaint_id,
    )
    notify(
        db, complaint.customer_id,
        f"Your complaint {complaint.complaint_number} has been assigned to a support agent.",
        complaint.complaint_id,
    )


def notify_status_change(db: Session, complaint: models.Complaint, old_status: str, new_status: str):
    notify(
        db, complaint.customer_id,
        f"Status of complaint {complaint.complaint_number} changed: {old_status} → {new_status}.",
        complaint.complaint_id,
    )
    if complaint.assigned_agent_id:
        notify(
            db, complaint.assigned_agent_id,
            f"Complaint {complaint.complaint_number} status updated: {old_status} → {new_status}.",
            complaint.complaint_id,
        )


def notify_escalation(db: Session, complaint: models.Complaint):
    # Notify supervisors
    supervisors = db.query(models.User).join(models.Role).filter(
        models.Role.role_name == models.ROLE_SUPERVISOR, models.User.is_active == True  # noqa: E712
    ).all()
    for sup in supervisors:
        notify(
            db, sup.user_id,
            f"⚠️ Complaint {complaint.complaint_number} has been escalated.",
            complaint.complaint_id,
        )
