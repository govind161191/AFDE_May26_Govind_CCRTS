"""
Seed roles, categories, and a starter set of users + sample complaints
so the UI has data to show on first launch.

Run from inside backend/ :
    python services/seed_data.py
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
import models, schemas
from auth import hash_password
from crud import users as users_crud
from crud import complaints as complaints_crud


ROLES = ["Admin", "Supervisor", "Support Agent", "Customer"]

CATEGORIES = [
    ("Billing Issues", "Invoices, charges, refunds"),
    ("Service Disruption", "Outages, slowness, downtime"),
    ("Product Defects", "Physical or software defects"),
    ("Technical Problems", "Setup, login, integration issues"),
    ("Delivery Delays", "Shipping or fulfillment delays"),
    ("Account Issues", "Profile, access, account changes"),
    ("Customer Service Complaints", "Concerns with prior support interactions"),
]

USERS = [
    # (name, email, password, role, phone)
    ("System Admin",  "admin@ccrts.io",         "Admin@123",  "Admin",         "9999999999"),
    ("Sarah Supervisor", "sarah@ccrts.io",      "Super@123",  "Supervisor",    "9111111111"),
    ("Alex Agent",    "alex@ccrts.io",          "Agent@123",  "Support Agent", "9222222222"),
    ("Maria Agent",   "maria@ccrts.io",         "Agent@123",  "Support Agent", "9333333333"),
    ("Govind Kumar",  "govind@example.com",     "Customer@123","Customer",     "9876543210"),
    ("Priya Sharma",  "priya@example.com",      "Customer@123","Customer",     "9123456780"),
    ("Rahul Verma",   "rahul@example.com",      "Customer@123","Customer",     "9988776655"),
]

SAMPLE_COMPLAINTS = [
    # (customer_email, category_name, subject, description, priority)
    ("govind@example.com", "Billing Issues", "Duplicate charge on May invoice",
     "I was charged twice for my subscription on May 5th. Need a refund for the duplicate amount.", "High"),
    ("priya@example.com", "Service Disruption", "Internet down since morning",
     "My internet connection has been completely down since 7 AM. Tried restarting the router multiple times.", "Critical"),
    ("rahul@example.com", "Delivery Delays", "Order #45821 not received",
     "Ordered on April 28th, expected delivery May 5th. Still not received and tracking is not updated.", "Medium"),
    ("govind@example.com", "Technical Problems", "Cannot reset password",
     "The 'forgot password' link is not sending an email to my registered address. Tried 3 times.", "Low"),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Roles
        for r in ROLES:
            if not users_crud.get_role_by_name(db, r):
                db.add(models.Role(role_name=r))
        db.commit()

        # Categories
        for cname, desc in CATEGORIES:
            if not db.query(models.Category).filter(models.Category.category_name == cname).first():
                db.add(models.Category(category_name=cname, description=desc))
        db.commit()

        # Users
        added_users = 0
        for name, email, pw, role_name, phone in USERS:
            if users_crud.get_user_by_email(db, email):
                continue
            role = users_crud.get_role_by_name(db, role_name)
            db.add(models.User(
                name=name, email=email, password_hash=hash_password(pw),
                role_id=role.role_id, phone=phone,
            ))
            added_users += 1
        db.commit()

        # Sample complaints
        added_complaints = 0
        for cust_email, cat_name, subject, desc, pri in SAMPLE_COMPLAINTS:
            customer = users_crud.get_user_by_email(db, cust_email)
            cat = db.query(models.Category).filter(models.Category.category_name == cat_name).first()
            # Don't re-add if exact subject already exists for that customer
            existing = db.query(models.Complaint).filter(
                models.Complaint.customer_id == customer.user_id,
                models.Complaint.subject == subject,
            ).first()
            if existing:
                continue
            complaints_crud.create_complaint(
                db, customer,
                schemas.ComplaintCreate(
                    category_id=cat.category_id,
                    subject=subject, description=desc, priority=pri,
                )
            )
            added_complaints += 1

        print(f"Seed complete: {added_users} users, {added_complaints} complaints added.")
        print("\nLogin credentials:")
        for name, email, pw, role, _ in USERS:
            print(f"  {role:<14}  {email:<25}  password: {pw}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
