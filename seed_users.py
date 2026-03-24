# -*- coding: utf-8 -*-
"""Run this to ensure demo users exist in the database"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.db.database import SessionLocal, engine, Base
from app.models import User
from app.core.security import get_password_hash
from datetime import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

users = [
    {"email":"demo@cacopilot.in","password":"demo@1234","name":"Demo CA","role":"ca"},
    {"email":"admin@maavi.ai","password":"admin@1234","name":"Admin User","role":"admin"},
    {"email":"ca@maavi.ai","password":"ca@1234","name":"CA Professional","role":"ca"},
    {"email":"lawyer@maavi.ai","password":"law@1234","name":"Advocate Singh","role":"ca"},
]

for u in users:
    exists = db.query(User).filter(User.email==u["email"]).first()
    if not exists:
        db.add(User(
            email=u["email"],
            hashed_password=get_password_hash(u["password"]),
            full_name=u["name"],
            role=u["role"],
            is_active=True,
            created_at=datetime.utcnow()
        ))
        print(f"Created: {u['email']} / {u['password']}")
    else:
        # Reset password in case it changed
        exists.hashed_password = get_password_hash(u["password"])
        exists.is_active = True
        print(f"Updated: {u['email']} / {u['password']}")

db.commit()
db.close()
print("\nAll users ready! Login credentials:")
print("  demo@cacopilot.in  / demo@1234")
print("  admin@maavi.ai     / admin@1234")
print("  ca@maavi.ai        / ca@1234")
print("  lawyer@maavi.ai    / law@1234")
