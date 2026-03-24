# client_portal_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from app.db.database import get_db, Base
from app.core.security import get_current_user, create_access_token, verify_password, get_password_hash
from app.models import Client, Invoice, ComplianceItem
import secrets

# ── Client portal token model ─────────────────────────────────────────────────
class ClientPortalAccess(Base):
    __tablename__ = "client_portal_access"
    __table_args__ = {"extend_existing": True}
    id          = Column(Integer, primary_key=True)
    client_id   = Column(Integer, ForeignKey("clients.id"), nullable=False)
    email       = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    access_token  = Column(String, nullable=True)
    is_active     = Column(Boolean, default=True)
    last_login    = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

try:
    from app.db.database import engine
    ClientPortalAccess.__table__.create(bind=engine, checkfirst=True)
except Exception:
    pass

portal_router = APIRouter(prefix="/portal", tags=["Client Portal"])

class PortalSetup(BaseModel):
    client_id: int
    email:     str
    password:  str

class PortalLogin(BaseModel):
    email:    str
    password: str

@portal_router.post("/setup")
def setup_portal(req: PortalSetup, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == req.client_id, Client.ca_user_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    existing = db.query(ClientPortalAccess).filter(ClientPortalAccess.client_id == req.client_id).first()
    if existing:
        existing.email         = req.email
        existing.password_hash = get_password_hash(req.password)
        existing.is_active     = True
    else:
        access = ClientPortalAccess(
            client_id=req.client_id,
            email=req.email,
            password_hash=get_password_hash(req.password),
            is_active=True,
        )
        db.add(access)
    db.commit()
    return {"status": "Portal access created", "email": req.email, "client": client.company_name}

@portal_router.post("/login")
def portal_login(req: PortalLogin, db: Session = Depends(get_db)):
    access = db.query(ClientPortalAccess).filter(
        ClientPortalAccess.email == req.email,
        ClientPortalAccess.is_active == True
    ).first()
    if not access or not verify_password(req.password, access.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_urlsafe(32)
    access.access_token = token
    access.last_login   = datetime.utcnow()
    db.commit()
    return {"access_token": token, "client_id": access.client_id, "token_type": "bearer"}

@portal_router.get("/dashboard/{client_id}")
def portal_dashboard(client_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    invoices   = db.query(Invoice).filter(Invoice.client_id == client_id).order_by(Invoice.id.desc()).limit(10).all()
    compliance = db.query(ComplianceItem).filter(ComplianceItem.client_id == client_id).all()
    sales    = [i for i in invoices if i.invoice_type and str(i.invoice_type.value) == "sale"]
    purchases = [i for i in invoices if i.invoice_type and str(i.invoice_type.value) == "purchase"]
    return {
        "client":          {"name": client.company_name, "gstin": client.gstin, "pan": client.pan_number},
        "summary":         {
            "total_revenue":      sum(i.total_amount or 0 for i in sales),
            "total_expenses":     sum(i.total_amount or 0 for i in purchases),
            "pending_compliance": sum(1 for c in compliance if c.status and str(c.status.value) == "pending"),
            "overdue":            sum(1 for c in compliance if c.status and str(c.status.value) == "overdue"),
        },
        "recent_invoices": [
            {"number": i.invoice_number, "vendor": i.vendor_name, "amount": i.total_amount,
             "type": str(i.invoice_type.value) if i.invoice_type else ""} for i in invoices[:5]
        ],
        "compliance":      [
            {"title": c.title, "due_date": str(c.due_date) if c.due_date else None,
             "status": str(c.status.value) if c.status else "pending"} for c in compliance
        ],
    }
