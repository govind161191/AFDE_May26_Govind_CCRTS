"""
In-app notifications for the current user.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import schemas, models
from auth import get_current_user
from database import get_db


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[schemas.NotificationOut])
def list_notifications(
    unread_only: bool = Query(False),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.Notification).filter(models.Notification.user_id == user.user_id)
    if unread_only:
        q = q.filter(models.Notification.is_read == False)  # noqa: E712
    return q.order_by(models.Notification.created_date.desc()).limit(100).all()


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(models.Notification).filter(
        models.Notification.notification_id == notification_id,
        models.Notification.user_id == user.user_id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return {"message": "marked read"}


@router.post("/read-all")
def mark_all_read(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.Notification).filter(
        models.Notification.user_id == user.user_id,
        models.Notification.is_read == False,   # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return {"message": "all marked read"}
