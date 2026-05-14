"""
Complaint CRUD + workflow operations.

Workflow statuses:
    Open → Assigned → In Progress → (Pending Customer Response | Escalated) → Resolved → Closed
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import or_

import models
import schemas
from services.sla import deadline_for, is_breached
from services import notifications as notif


VALID_STATUSES = {
    "Open", "Assigned", "In Progress", "Pending Customer Response",
    "Escalated", "Resolved", "Closed",
}


def _generate_complaint_number() -> str:
    """Human-friendly identifier: CMP-YYYYMMDD-XXXX."""
    today = datetime.utcnow().strftime("%Y%m%d")
    short = uuid4().hex[:6].upper()
    return f"CMP-{today}-{short}"


def get_complaint(db: Session, complaint_id: int) -> Optional[models.Complaint]:
    return db.query(models.Complaint).filter(models.Complaint.complaint_id == complaint_id).first()


def list_complaints(
    db: Session,
    *,
    customer_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    escalated: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[models.Complaint]:
    q = db.query(models.Complaint)
    if customer_id is not None:
        q = q.filter(models.Complaint.customer_id == customer_id)
    if agent_id is not None:
        q = q.filter(models.Complaint.assigned_agent_id == agent_id)
    if status:
        q = q.filter(models.Complaint.status == status)
    if priority:
        q = q.filter(models.Complaint.priority == priority)
    if category_id:
        q = q.filter(models.Complaint.category_id == category_id)
    if escalated is not None:
        q = q.filter(models.Complaint.is_escalated == escalated)
    if search:
        like = f"%{search}%"
        q = q.filter(
            or_(
                models.Complaint.subject.ilike(like),
                models.Complaint.description.ilike(like),
                models.Complaint.complaint_number.ilike(like),
            )
        )
    return q.order_by(models.Complaint.created_date.desc()).all()


def create_complaint(db: Session, customer: models.User, data: schemas.ComplaintCreate) -> models.Complaint:
    now = datetime.utcnow()
    c = models.Complaint(
        complaint_number=_generate_complaint_number(),
        customer_id=customer.user_id,
        category_id=data.category_id,
        subject=data.subject,
        description=data.description,
        priority=data.priority,
        status="Open",
        sla_deadline=deadline_for(data.priority, now),
        created_date=now,
        updated_date=now,
    )
    db.add(c)
    db.flush()  # populate complaint_id
    db.add(models.ComplaintHistory(
        complaint_id=c.complaint_id,
        updated_by=customer.user_id,
        old_status=None,
        new_status="Open",
        comment="Complaint registered",
    ))
    notif.notify_complaint_created(db, c)
    db.commit()
    db.refresh(c)
    return c


def update_complaint(
    db: Session, c: models.Complaint, data: schemas.ComplaintUpdate, actor: models.User
) -> models.Complaint:
    """Apply allowed updates and record history + notifications."""
    old_status = c.status

    if data.assigned_agent_id is not None:
        c.assigned_agent_id = data.assigned_agent_id
        # Auto-progress to Assigned if currently Open
        if c.status == "Open":
            c.status = "Assigned"
        notif.notify_assignment(db, c, data.assigned_agent_id)

    if data.priority is not None and data.priority != c.priority:
        c.priority = data.priority
        c.sla_deadline = deadline_for(data.priority, c.created_date)

    if data.status is not None and data.status in VALID_STATUSES:
        c.status = data.status
        if data.status == "Resolved":
            c.resolved_date = datetime.utcnow()
            if data.resolution_comment:
                c.resolution_comment = data.resolution_comment
        if data.status == "Closed":
            c.closed_date = datetime.utcnow()
        if data.status == "Escalated":
            c.is_escalated = True
            notif.notify_escalation(db, c)

    if data.resolution_comment is not None and c.status == "Resolved":
        c.resolution_comment = data.resolution_comment

    if old_status != c.status:
        db.add(models.ComplaintHistory(
            complaint_id=c.complaint_id,
            updated_by=actor.user_id,
            old_status=old_status,
            new_status=c.status,
            comment=data.comment,
        ))
        notif.notify_status_change(db, c, old_status, c.status)
    elif data.comment:
        # Even without status change, record the comment as an audit entry
        db.add(models.ComplaintHistory(
            complaint_id=c.complaint_id,
            updated_by=actor.user_id,
            old_status=old_status,
            new_status=c.status,
            comment=data.comment,
        ))

    db.commit()
    db.refresh(c)
    return c


def delete_complaint(db: Session, c: models.Complaint) -> None:
    db.delete(c)
    db.commit()


def to_out_dict(c: models.Complaint) -> dict:
    """Convert a Complaint into the wider dict shape ComplaintOut expects."""
    return {
        "complaint_id": c.complaint_id,
        "complaint_number": c.complaint_number,
        "customer_id": c.customer_id,
        "customer_name": c.customer.name if c.customer else None,
        "assigned_agent_id": c.assigned_agent_id,
        "assigned_agent_name": c.assigned_agent.name if c.assigned_agent else None,
        "category_id": c.category_id,
        "category_name": c.category.category_name if c.category else None,
        "subject": c.subject,
        "description": c.description,
        "priority": c.priority,
        "status": c.status,
        "sla_deadline": c.sla_deadline,
        "sla_breached": is_breached(c.sla_deadline, c.status),
        "created_date": c.created_date,
        "updated_date": c.updated_date,
        "resolved_date": c.resolved_date,
        "closed_date": c.closed_date,
        "resolution_comment": c.resolution_comment,
        "is_escalated": c.is_escalated,
    }


# --------- Auto-escalation sweep ---------

def auto_escalate_overdue(db: Session) -> int:
    """Mark unresolved, past-SLA complaints as Escalated. Returns count."""
    candidates = db.query(models.Complaint).filter(
        models.Complaint.status.notin_(("Resolved", "Closed", "Escalated")),
        models.Complaint.sla_deadline < datetime.utcnow(),
    ).all()
    count = 0
    for c in candidates:
        old = c.status
        c.status = "Escalated"
        c.is_escalated = True
        db.add(models.ComplaintHistory(
            complaint_id=c.complaint_id, updated_by=c.customer_id,
            old_status=old, new_status="Escalated",
            comment="Auto-escalated: SLA deadline exceeded",
        ))
        notif.notify_escalation(db, c)
        count += 1
    db.commit()
    return count
