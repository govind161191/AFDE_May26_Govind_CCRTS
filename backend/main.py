"""
FastAPI application entrypoint for the Customer Complaint & Resolution
Tracking System (CCRTS).

Run locally:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models  # noqa: F401
from routers import (
    auth_router, users_router, categories_router, complaints_router,
    attachments_router, feedback_router, notifications_router, dashboard_router,
)


# Auto-create tables on startup (Phase 1 — no migrations yet)
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Customer Complaint & Resolution Tracking System API",
    description=(
        "Phase 1 of the AFDE capstone CCRTS — full complaint lifecycle, "
        "JWT authentication, role-based access control (Admin / Supervisor / "
        "Support Agent / Customer), SLA tracking with auto-escalation, "
        "attachments, in-app notifications, and feedback."
    ),
    version="1.0.0",
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:5173", "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(categories_router.router)
app.include_router(complaints_router.router)
app.include_router(attachments_router.router)
app.include_router(feedback_router.router)
app.include_router(notifications_router.router)
app.include_router(dashboard_router.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "CCRTS API",
        "version": "1.0.0",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
