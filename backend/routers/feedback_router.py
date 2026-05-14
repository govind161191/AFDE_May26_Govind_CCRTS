"""
Feedback endpoints — customer rating + comments after a complaint is resolved.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import schemas, models
from auth import get_current_user
from crud import complaints as complaints_crud
from database import get_db


router = APIRouter(prefix="/complaints/{complaint_id}/feedback", tags=["Feedback"])


@router.post("", response_model=schemas.FeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    complaint_id: int,
    data: schemas.FeedbackCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if c.customer_id != user.user_id:
        raise HTTPException(status_code=403, detail="Only the complaint owner can submit feedback")
    if c.status not in ("Resolved", "Closed"):
        raise HTTPException(status_code=400, detail="Feedback can only be submitted for resolved or closed complaints")
    if c.feedback:
        raise HTTPException(status_code=400, detail="Feedback already submitted")
    fb = models.Feedback(complaint_id=complaint_id, rating=data.rating, comments=data.comments)
    db.add(fb); db.commit(); db.refresh(fb)
    return fb


@router.get("", response_model=schemas.FeedbackOut)
def get_feedback(
    complaint_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c or not c.feedback:
        raise HTTPException(status_code=404, detail="No feedback for this complaint")
    return c.feedback
