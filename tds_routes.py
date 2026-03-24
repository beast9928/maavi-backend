# tds_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum as SAEnum
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.db.database import get_db, Base
from app.core.security import get_current_user
from app.services.ai.ai_service import ai_chat_response
import enum

# ── Model ─────────────────────────────────────────────────────────────────────
class TDSStatus(str, enum.Enum):
    pending   = "pending"
    deducted  = "deducted"
    deposited = "deposited"
    filed     = "filed"

class TDSEntry(Base):
    __tablename__ = "tds_entries"
    __table_args__ = {"extend_existing": True}
    id             = Column(Integer, primary_key=True, index=True)
    ca_user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id      = Column(Integer, ForeignKey("clients.id"), nullable=True)
    deductee_name  = Column(String, nullable=False)
    pan_number     = Column(String, nullable=True)
    section        = Column(String, nullable=False, default="194C")
    payment_nature = Column(String, nullable=True)
    payment_amount = Column(Float, default=0.0)
    tds_rate       = Column(Float, default=1.0)
    tds_amount     = Column(Float, default=0.0)
    payment_date   = Column(Date, nullable=True)
    due_date       = Column(Date, nullable=True)
    status         = Column(SAEnum(TDSStatus), default=TDSStatus.pending)
    quarter        = Column(String, nullable=True)
    financial_year = Column(String, nullable=True)
    remarks        = Column(String, nullable=True)

try:
    from app.db.database import engine
    TDSEntry.__table__.create(bind=engine, checkfirst=True)
except Exception:
    pass

# ── Schemas ───────────────────────────────────────────────────────────────────
class TDSCreate(BaseModel):
    client_id:      Optional[int] = None
    deductee_name:  str
    pan_number:     Optional[str] = None
    section:        str = "194C"
    payment_nature: Optional[str] = None
    payment_amount: float
    tds_rate:       float = 1.0
    payment_date:   Optional[date] = None
    due_date:       Optional[date] = None
    quarter:        Optional[str] = None
    financial_year: Optional[str] = None
    remarks:        Optional[str] = None

class TDSUpdate(BaseModel):
    status:  Optional[str] = None
    remarks: Optional[str] = None

# ── Router ────────────────────────────────────────────────────────────────────
tds_router = APIRouter(prefix="/tds", tags=["TDS"])

TDS_SECTIONS = {
    "192":  {"name": "Salary",                   "rate": 5.0,  "threshold": 250000},
    "194A": {"name": "Interest (non-bank)",       "rate": 10.0, "threshold": 5000},
    "194B": {"name": "Lottery winnings",          "rate": 30.0, "threshold": 10000},
    "194C": {"name": "Contractor payment",        "rate": 1.0,  "threshold": 30000},
    "194D": {"name": "Insurance commission",      "rate": 5.0,  "threshold": 15000},
    "194H": {"name": "Commission / brokerage",    "rate": 5.0,  "threshold": 15000},
    "194I": {"name": "Rent",                      "rate": 10.0, "threshold": 240000},
    "194J": {"name": "Professional fees",         "rate": 10.0, "threshold": 30000},
    "194Q": {"name": "Purchase of goods",         "rate": 0.1,  "threshold": 5000000},
    "206C": {"name": "TCS on sales",              "rate": 0.1,  "threshold": 0},
}

@tds_router.get("/sections")
def get_sections(current_user=Depends(get_current_user)):
    return {"sections": TDS_SECTIONS}

@tds_router.post("/calculate")
def calculate_tds(data: dict, current_user=Depends(get_current_user)):
    section = data.get("section", "194C")
    amount  = float(data.get("amount", 0))
    pan     = data.get("pan", "")
    info    = TDS_SECTIONS.get(section, {"rate": 1.0, "threshold": 0})
    rate    = info["rate"]
    if not pan or len(pan) != 10:
        rate = min(rate * 2, 20.0)  # higher rate without PAN
    tds = round(amount * rate / 100, 2)
    return {
        "section":        section,
        "section_name":   info.get("name", ""),
        "payment_amount": amount,
        "tds_rate":       rate,
        "tds_amount":     tds,
        "net_payable":    round(amount - tds, 2),
        "pan_available":  bool(pan and len(pan) == 10),
        "threshold":      info.get("threshold", 0),
        "above_threshold": amount >= info.get("threshold", 0),
    }

@tds_router.post("/entries")
def create_entry(req: TDSCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tds_amt = round(req.payment_amount * req.tds_rate / 100, 2)
    entry = TDSEntry(
        ca_user_id=current_user.id,
        client_id=req.client_id,
        deductee_name=req.deductee_name,
        pan_number=req.pan_number,
        section=req.section,
        payment_nature=req.payment_nature,
        payment_amount=req.payment_amount,
        tds_rate=req.tds_rate,
        tds_amount=tds_amt,
        payment_date=req.payment_date,
        due_date=req.due_date,
        quarter=req.quarter,
        financial_year=req.financial_year,
        remarks=req.remarks,
        status=TDSStatus.pending,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "tds_amount": tds_amt, "status": "created"}

@tds_router.get("/entries")
def list_entries(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    entries = db.query(TDSEntry).filter(TDSEntry.ca_user_id == current_user.id).all()
    return {"entries": [
        {
            "id": e.id, "deductee_name": e.deductee_name, "pan_number": e.pan_number,
            "section": e.section, "payment_amount": e.payment_amount,
            "tds_rate": e.tds_rate, "tds_amount": e.tds_amount,
            "status": str(e.status.value) if e.status else "pending",
            "quarter": e.quarter, "financial_year": e.financial_year,
            "due_date": str(e.due_date) if e.due_date else None,
        } for e in entries
    ]}

@tds_router.patch("/entries/{entry_id}")
def update_entry(entry_id: int, req: TDSUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    entry = db.query(TDSEntry).filter(TDSEntry.id == entry_id, TDSEntry.ca_user_id == current_user.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if req.status:
        entry.status = TDSStatus(req.status)
    if req.remarks:
        entry.remarks = req.remarks
    db.commit()
    return {"status": "updated"}

@tds_router.get("/summary")
def tds_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    entries = db.query(TDSEntry).filter(TDSEntry.ca_user_id == current_user.id).all()
    total_tds    = sum(e.tds_amount or 0 for e in entries)
    deposited    = sum(e.tds_amount or 0 for e in entries if e.status == TDSStatus.deposited)
    pending      = sum(e.tds_amount or 0 for e in entries if e.status == TDSStatus.pending)
    by_section   = {}
    for e in entries:
        by_section[e.section] = by_section.get(e.section, 0) + (e.tds_amount or 0)
    return {
        "total_tds_deducted": round(total_tds, 2),
        "total_deposited":    round(deposited, 2),
        "total_pending":      round(pending, 2),
        "by_section":         {k: round(v, 2) for k, v in by_section.items()},
        "entry_count":        len(entries),
    }

@tds_router.post("/ai-advice")
def tds_ai_advice(data: dict, current_user=Depends(get_current_user)):
    query = data.get("query", "")
    response = ai_chat_response(
        f"TDS query from CA: {query}. Provide advice on TDS sections, rates, due dates, and compliance under Indian Income Tax Act.",
        None
    )
    return {"advice": response}
