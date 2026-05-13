"""
User management endpoints — Admin-only except for /me-style reads.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import schemas, models
from auth import require_roles
from crud import users as users_crud
from database import get_db


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[schemas.UserOut])
def list_users(
    role: Optional[str] = Query(None, description="Filter by role name"),
    _: models.User = Depends(require_roles("Admin", "Supervisor")),
    db: Session = Depends(get_db),
):
    return [users_crud.user_to_out(u) for u in users_crud.list_users(db, role_name=role)]


@router.get("/agents", response_model=List[schemas.UserOut])
def list_agents(
    _: models.User = Depends(require_roles("Admin", "Supervisor")),
    db: Session = Depends(get_db),
):
    """Convenience endpoint — used by the assignment dropdown."""
    return [users_crud.user_to_out(u) for u in users_crud.list_users(db, role_name="Support Agent")]


@router.post("", response_model=schemas.UserOut, status_code=201)
def create_user(
    data: schemas.UserRegister,
    _: models.User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    """Admin-only: create a user with any role."""
    if users_crud.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already exists")
    return users_crud.user_to_out(users_crud.create_user(db, data))


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: int,
    data: schemas.UserUpdate,
    _: models.User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    u = users_crud.update_user(db, user_id, data)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return users_crud.user_to_out(u)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    _: models.User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db),
):
    if not users_crud.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted", "user_id": user_id}
