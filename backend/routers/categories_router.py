"""
Category management endpoints.

Read: any authenticated user (customers need this for the dropdown)
Write: Admin only.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas, models
from auth import get_current_user, require_roles
from database import get_db


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[schemas.CategoryOut])
def list_categories(_: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Category).order_by(models.Category.category_name).all()


@router.post("", response_model=schemas.CategoryOut, status_code=201)
def create_category(
    data: schemas.CategoryCreate,
    _: models.User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    if db.query(models.Category).filter(models.Category.category_name == data.category_name).first():
        raise HTTPException(status_code=400, detail="Category already exists")
    c = models.Category(**data.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return c


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    _: models.User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    c = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(c); db.commit()
    return {"message": "Category deleted"}
