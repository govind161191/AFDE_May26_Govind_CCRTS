"""
Dashboard analytics — aggregate counts, by-category breakdowns, agent performance.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas, models
from auth import require_roles
from crud import dashboard as dashboard_crud
from database import get_db


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(
    _: models.User = Depends(require_roles("Admin", "Supervisor", "Support Agent")),
    db: Session = Depends(get_db),
):
    return dashboard_crud.compute_dashboard(db)
