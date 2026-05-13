"""
Authentication endpoints: register, login, current user, password change.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import schemas
import models
from auth import (
    create_access_token, verify_password, hash_password,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES,
)
from crud import users as users_crud
from database import get_db


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(data: schemas.UserRegister, db: Session = Depends(get_db)):
    """Self-service registration — creates a Customer account by default."""
    if users_crud.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    # Don't allow public self-registration as Admin or Supervisor
    if data.role_name not in (None, "Customer"):
        data.role_name = "Customer"
    user = users_crud.create_user(db, data)
    return users_crud.user_to_out(user)


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2-style login (email goes in the `username` field)."""
    user = users_crud.get_user_by_email(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    token = create_access_token(
        {"sub": str(user.user_id), "role": user.role.role_name},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer", "user": users_crud.user_to_out(user)}


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    """Return the authenticated user."""
    return users_crud.user_to_out(user)


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    data: schemas.PasswordChange,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated"}
