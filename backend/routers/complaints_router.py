"""
Complaint endpoints — registration, listing, detail, updates, history, escalation.

Authorization rules:
  - Customer: can create complaints; can only view / list their OWN complaints
  - Support Agent: can list complaints assigned to them; can update status
  - Supervisor / Admin: full visibility; can assign, escalate, change priority
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import schemas, models
from auth import get_current_user, require_roles
from crud import complaints as complaints_crud
from database import get_db


router = APIRouter(prefix="/complaints", tags=["Complaints"])


def _ensure_can_view(user: models.User, c: models.Complaint):
    role = user.role.role_name
    if role == "Customer" and c.customer_id != user.user_id:
        raise HTTPException(status_code=403, detail="You can only view your own complaints")
    if role == "Support Agent" and c.assigned_agent_id != user.user_id and c.customer_id != user.user_id:
        raise HTTPException(status_code=403, detail="You can only view complaints assigned to you")


@router.post("", response_model=schemas.ComplaintOut, status_code=status.HTTP_201_CREATED)
def register_complaint(
    data: schemas.ComplaintCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # All authenticated users can file complaints, but typically customers do
    # Verify category exists
    if not db.query(models.Category).filter(models.Category.category_id == data.category_id).first():
        raise HTTPException(status_code=400, detail="Invalid category_id")
    c = complaints_crud.create_complaint(db, user, data)
    return complaints_crud.to_out_dict(c)


@router.get("", response_model=List[schemas.ComplaintOut])
def list_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = None,
    category_id: Optional[int] = None,
    escalated: Optional[bool] = None,
    search: Optional[str] = Query(None, description="Search subject / description / complaint number"),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role = user.role.role_name
    kwargs = dict(
        status=status_filter, priority=priority, category_id=category_id,
        escalated=escalated, search=search,
    )
    if role == "Customer":
        kwargs["customer_id"] = user.user_id
    elif role == "Support Agent":
        kwargs["agent_id"] = user.user_id
    # Supervisors / Admins see all
    complaints = complaints_crud.list_complaints(db, **kwargs)
    return [complaints_crud.to_out_dict(c) for c in complaints]


@router.get("/{complaint_id}", response_model=schemas.ComplaintOut)
def get_complaint(
    complaint_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _ensure_can_view(user, c)
    return complaints_crud.to_out_dict(c)


@router.put("/{complaint_id}", response_model=schemas.ComplaintOut)
def update_complaint(
    complaint_id: int,
    data: schemas.ComplaintUpdate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    role = user.role.role_name
    # Authorization matrix
    if role == "Customer":
        # Customer can only post comments or mark closed after resolution
        if data.assigned_agent_id is not None or data.priority is not None:
            raise HTTPException(status_code=403, detail="Customers cannot assign agents or change priority")
        if data.status and data.status not in ("Closed", "Pending Customer Response"):
            raise HTTPException(status_code=403, detail="Customers can only close resolved complaints or respond")
        if c.customer_id != user.user_id:
            raise HTTPException(status_code=403, detail="Not your complaint")
    elif role == "Support Agent":
        if c.assigned_agent_id != user.user_id:
            raise HTTPException(status_code=403, detail="Not assigned to you")
        if data.assigned_agent_id is not None:
            raise HTTPException(status_code=403, detail="Only supervisors can reassign")

    updated = complaints_crud.update_complaint(db, c, data, user)
    return complaints_crud.to_out_dict(updated)


@router.delete("/{complaint_id}")
def delete_complaint(
    complaint_id: int,
    _: models.User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    complaints_crud.delete_complaint(db, c)
    return {"message": "Complaint deleted", "complaint_id": complaint_id}


@router.get("/{complaint_id}/history", response_model=List[schemas.HistoryOut])
def get_history(
    complaint_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _ensure_can_view(user, c)
    rows = sorted(c.history, key=lambda h: h.updated_date)
    return [
        {
            "history_id": h.history_id,
            "complaint_id": h.complaint_id,
            "updated_by": h.updated_by,
            "updated_by_name": h.user.name if h.user else None,
            "old_status": h.old_status,
            "new_status": h.new_status,
            "comment": h.comment,
            "updated_date": h.updated_date,
        }
        for h in rows
    ]


@router.post("/sweep-escalations")
def sweep_escalations(
    _: models.User = Depends(require_roles("Admin", "Supervisor")),
    db: Session = Depends(get_db),
):
    """Auto-escalate any past-deadline complaints. Useful manual trigger
    in lieu of a real scheduler."""
    count = complaints_crud.auto_escalate_overdue(db)
    return {"escalated": count}
