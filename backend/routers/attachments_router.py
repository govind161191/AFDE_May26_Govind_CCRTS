"""
Attachment uploads and downloads.

Files are stored on disk under `uploads/` with a unique generated name.
The original file_name is preserved for download.
"""

import os
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import schemas, models
from auth import get_current_user
from crud import complaints as complaints_crud
from database import get_db


UPLOAD_DIR = Path(os.getenv("CCRTS_UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 10 * 1024 * 1024  # 10 MB

router = APIRouter(prefix="/complaints/{complaint_id}/attachments", tags=["Attachments"])


def _ensure_access(user: models.User, c: models.Complaint):
    role = user.role.role_name
    if role == "Customer" and c.customer_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not your complaint")
    if role == "Support Agent" and c.assigned_agent_id != user.user_id and c.customer_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not assigned to you")


@router.post("", response_model=schemas.AttachmentOut, status_code=status.HTTP_201_CREATED)
def upload(
    complaint_id: int,
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _ensure_access(user, c)

    contents = file.file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10MB limit")

    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(contents)

    a = models.Attachment(
        complaint_id=complaint_id,
        file_name=file.filename,
        file_path=str(dest),
        content_type=file.content_type,
        uploaded_by=user.user_id,
    )
    db.add(a); db.commit(); db.refresh(a)
    return a


@router.get("", response_model=List[schemas.AttachmentOut])
def list_attachments(
    complaint_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _ensure_access(user, c)
    return c.attachments


@router.get("/{attachment_id}/download")
def download(
    complaint_id: int,
    attachment_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = complaints_crud.get_complaint(db, complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    _ensure_access(user, c)
    a = db.query(models.Attachment).filter(
        models.Attachment.attachment_id == attachment_id,
        models.Attachment.complaint_id == complaint_id,
    ).first()
    if not a or not os.path.exists(a.file_path):
        raise HTTPException(status_code=404, detail="Attachment not found")
    return FileResponse(a.file_path, filename=a.file_name, media_type=a.content_type or "application/octet-stream")
