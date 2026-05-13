"""
Pydantic schemas — request / response shapes for the CCRTS API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============== Auth ==============

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone: Optional[str] = None
    role_name: Optional[str] = "Customer"   # Default registration creates a Customer


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role_name: str
    is_active: bool
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    role_name: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


# ============== Categories ==============

class CategoryBase(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    category_id: int
    model_config = ConfigDict(from_attributes=True)


# ============== Complaints ==============

class ComplaintCreate(BaseModel):
    category_id: int
    subject: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    priority: str = Field("Medium", pattern="^(Low|Medium|High|Critical)$")


class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    priority: Optional[str] = None
    resolution_comment: Optional[str] = None
    comment: Optional[str] = None   # Audit-trail comment that accompanies the change


class ComplaintOut(BaseModel):
    complaint_id: int
    complaint_number: str
    customer_id: int
    customer_name: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    assigned_agent_name: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    subject: str
    description: str
    priority: str
    status: str
    sla_deadline: datetime
    sla_breached: bool = False
    created_date: datetime
    updated_date: datetime
    resolved_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    resolution_comment: Optional[str] = None
    is_escalated: bool

    model_config = ConfigDict(from_attributes=True)


class HistoryOut(BaseModel):
    history_id: int
    complaint_id: int
    updated_by: int
    updated_by_name: Optional[str] = None
    old_status: Optional[str] = None
    new_status: str
    comment: Optional[str] = None
    updated_date: datetime

    model_config = ConfigDict(from_attributes=True)


class AttachmentOut(BaseModel):
    attachment_id: int
    complaint_id: int
    file_name: str
    content_type: Optional[str] = None
    uploaded_by: int
    uploaded_date: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Feedback ==============

class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None


class FeedbackOut(BaseModel):
    feedback_id: int
    complaint_id: int
    rating: int
    comments: Optional[str] = None
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Notifications ==============

class NotificationOut(BaseModel):
    notification_id: int
    user_id: int
    complaint_id: Optional[int] = None
    message: str
    is_read: bool
    created_date: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Dashboard ==============

class CategoryCount(BaseModel):
    category: str
    count: int


class AgentPerformance(BaseModel):
    agent_id: int
    agent_name: str
    assigned: int
    resolved: int
    sla_breaches: int


class DashboardStats(BaseModel):
    total_complaints: int
    open_complaints: int
    in_progress_complaints: int
    resolved_complaints: int
    closed_complaints: int
    escalated_complaints: int
    sla_breaches: int
    avg_resolution_hours: Optional[float] = None
    by_category: List[CategoryCount] = []
    by_priority: List[CategoryCount] = []
    agent_performance: List[AgentPerformance] = []


# Late binding — Token references UserOut
Token.model_rebuild()
