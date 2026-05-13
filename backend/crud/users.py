"""User and role CRUD operations."""

from typing import List, Optional
from sqlalchemy.orm import Session

import models
import schemas
from auth import hash_password


def get_role_by_name(db: Session, name: str) -> Optional[models.Role]:
    return db.query(models.Role).filter(models.Role.role_name == name).first()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def list_users(db: Session, role_name: Optional[str] = None) -> List[models.User]:
    q = db.query(models.User)
    if role_name:
        q = q.join(models.Role).filter(models.Role.role_name == role_name)
    return q.order_by(models.User.user_id).all()


def create_user(db: Session, data: schemas.UserRegister) -> models.User:
    role = get_role_by_name(db, data.role_name or "Customer")
    if not role:
        # Fall back to Customer if the requested role doesn't exist
        role = get_role_by_name(db, "Customer")
    u = models.User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=role.role_id,
        phone=data.phone,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def update_user(db: Session, user_id: int, data: schemas.UserUpdate) -> Optional[models.User]:
    u = get_user(db, user_id)
    if not u:
        return None
    if data.name is not None: u.name = data.name
    if data.phone is not None: u.phone = data.phone
    if data.is_active is not None: u.is_active = data.is_active
    if data.role_name is not None:
        role = get_role_by_name(db, data.role_name)
        if role:
            u.role_id = role.role_id
    db.commit()
    db.refresh(u)
    return u


def delete_user(db: Session, user_id: int) -> bool:
    u = get_user(db, user_id)
    if not u:
        return False
    db.delete(u)
    db.commit()
    return True


def user_to_out(u: models.User) -> dict:
    """Flatten the User + Role into the dict shape UserOut expects."""
    return {
        "user_id": u.user_id,
        "name": u.name,
        "email": u.email,
        "phone": u.phone,
        "role_name": u.role.role_name if u.role else "",
        "is_active": u.is_active,
        "created_date": u.created_date,
    }
