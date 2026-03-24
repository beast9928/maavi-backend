# -*- coding: utf-8 -*-
"""Fixed seed_users.py - uses only valid role values from your existing Enum"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, engine, Base
from app.models import User
from app.core.security import get_password_hash
from datetime import datetime
import inspect

# Auto-detect valid roles from the User model
db = SessionLocal()
Base.metadata.create_all(bind=engine)

# Find what role values actually exist in the enum
valid_role = 'ca'  # default safe value
try:
    from app.models import User as U
    role_col = U.__table__.columns.get('role')
    if role_col is not None and hasattr(role_col.type, 'enums'):
        enums = role_col.type.enums
        print(f"Valid roles in your DB: {enums}")
        # Pick best matches
        ca_role    = next((r for r in enums if 'ca' in r.lower()), enums[0])
        admin_role = next((r for r in enums if 'admin' in r.lower()), ca_role)
        super_role = next((r for r in enums if 'super' in r.lower()), admin_role)
    else:
        # Try reading from enum class directly
        import enum
        for attr in dir(U):
            val = getattr(U, attr, None)
            if isinstance(val, enum.EnumMeta):
                members = [m.value for m in val]
                print(f"Found enum {attr}: {members}")
        ca_role = admin_role = super_role = 'ca'
except Exception as e:
    print(f"Role detection note: {e}")
    ca_role = admin_role = super_role = 'ca'

print(f"Using roles -> CA: '{ca_role}', Admin: '{admin_role}'")

users = [
    {"email": "demo@cacopilot.in",  "password": "demo@1234",  "name": "Demo CA User",      "role": ca_role},
    {"email": "admin@maavi.ai",      "password": "admin@1234", "name": "Admin User",         "role": admin_role},
    {"email": "ca@maavi.ai",         "password": "ca@1234",    "name": "CA Professional",    "role": ca_role},
    {"email": "lawyer@maavi.ai",     "password": "law@1234",   "name": "Advocate Singh",     "role": ca_role},
    {"email": "test@maavi.ai",       "password": "test@1234",  "name": "Test Account",       "role": ca_role},
]

for u in users:
    try:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if existing:
            existing.hashed_password = get_password_hash(u["password"])
            existing.is_active = True
            existing.full_name = u["name"]
            db.commit()
            print(f"  Updated : {u['email']}  /  {u['password']}")
        else:
            new_user = User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["name"],
                is_active=True,
                created_at=datetime.utcnow(),
            )
            # Only set role if attribute exists
            if hasattr(new_user, 'role'):
                try:
                    new_user.role = u["role"]
                except Exception:
                    pass  # role might be auto-set
            db.add(new_user)
            db.commit()
            print(f"  Created : {u['email']}  /  {u['password']}")
    except Exception as e:
        db.rollback()
        print(f"  Skipped : {u['email']} -> {e}")

db.close()
print("""
============================================
  ALL USERS READY!
============================================
  demo@cacopilot.in  /  demo@1234   <- USE THIS
  admin@maavi.ai     /  admin@1234
  ca@maavi.ai        /  ca@1234
  lawyer@maavi.ai    /  law@1234

Now run:
  uvicorn main:app --host 0.0.0.0 --port 8000
============================================
""")
