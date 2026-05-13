"""
SQLAlchemy ORM models for the Customer Complaint & Resolution Tracking System.

Entities:
  - Role               : RBAC role (Admin, Supervisor, Support Agent, Customer)
  - User               : Authenticated user, FK to Role
  - Category           : Complaint category (Billing, Technical, etc.)
  - Complaint          : The core entity — a customer-raised issue
  - ComplaintHistory   : Audit trail for every status / assignment change
  - Attachment        : Files uploaded against a complaint
  - Feedback           : Customer rating + comment after resolution
  - Notification       : In-app notifications for users
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database import Base


# Canonical role names — referenced from auth dependencies
ROLE_ADMIN = "Admin"
ROLE_SUPERVISOR = "Supervisor"
ROLE_AGENT = "Support Agent"
ROLE_CUSTOMER = "Customer"


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    phone = Column(String(20), nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    role = relationship("Role", back_populates="users")
    complaints_as_customer = relationship(
        "Complaint", foreign_keys="Complaint.customer_id", back_populates="customer"
    )
    complaints_as_agent = relationship(
        "Complaint", foreign_keys="Complaint.assigned_agent_id", back_populates="assigned_agent"
    )


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    assigned_agent_id = Column(Integer, ForeignKey("users.user_id"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="Medium")        # Low/Medium/High/Critical
    status = Column(String(40), nullable=False, default="Open", index=True) # see workflow statuses
    sla_deadline = Column(DateTime, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_date = Column(DateTime, nullable=True)
    closed_date = Column(DateTime, nullable=True)
    resolution_comment = Column(Text, nullable=True)
    is_escalated = Column(Boolean, default=False)

    customer = relationship("User", foreign_keys=[customer_id], back_populates="complaints_as_customer")
    assigned_agent = relationship("User", foreign_keys=[assigned_agent_id], back_populates="complaints_as_agent")
    category = relationship("Category")
    history = relationship("ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="complaint", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="complaint", uselist=False, cascade="all, delete-orphan")


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), nullable=False, index=True)
    updated_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    old_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=False)
    comment = Column(Text, nullable=True)
    updated_date = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="history")
    user = relationship("User")


class Attachment(Base):
    __tablename__ = "attachments"

    attachment_id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    uploaded_date = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="attachments")
    user = relationship("User")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), unique=True, nullable=False)
    rating = Column(Integer, nullable=False)   # 1-5
    comments = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="feedback")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.complaint_id"), nullable=True)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, index=True)
    created_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    complaint = relationship("Complaint")
