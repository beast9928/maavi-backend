# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from app.db.database import get_db
from app.models.law import Matter, CourtHearing, TimeEntry, LegalDocument, ContractAnalysis, MatterStatus
from app.models import User
from app.core.security import get_current_user
from app.services.ai.legal_ai import generate_legal_document, analyze_contract, do_legal_research

law_router = APIRouter(prefix="/law", tags=["Law Firm"])

class MatterCreate(BaseModel):
    title: str
    practice_area: Optional[str] = None
    court: Optional[str] = None
    client_name: Optional[str] = None
    opposite_party: Optional[str] = None
    brief: Optional[str] = None
    assigned_to: Optional[str] = None
    filed_date: Optional[date] = None
    next_hearing: Optional[date] = None
    status: Optional[str] = "pending"
    relief_sought: Optional[str] = None

class HearingCreate(BaseModel):
    matter_id: int
    hearing_date: date
    hearing_time: Optional[str] = None
    court: Optional[str] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None

class TimeEntryCreate(BaseModel):
    matter_id: int
    entry_date: date
    hours: float
    rate_per_hour: float
    description: Optional[str] = None

class DraftRequest(BaseModel):
    doc_type: str
    client_name: str
    opposite_party: Optional[str] = ""
    subject: str
    jurisdiction: Optional[str] = ""
    relief: Optional[str] = ""
    matter_id: Optional[int] = None

class ResearchRequest(BaseModel):
    query: str
    court_filter: Optional[str] = ""

def gen_matter_num(db):
    count = db.query(func.count(Matter.id)).scalar() or 0
    return f"MAT-{datetime.now().year}-{count+1:03d}"

def chk_matter(matter_id, user_id, db):
    m = db.query(Matter).filter(Matter.id == matter_id, Matter.ca_user_id == user_id, Matter.is_active == True).first()
    if not m:
        raise HTTPException(status_code=404, detail="Matter not found")
    return m

@law_router.get("/dashboard")
def law_dashboard(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    from datetime import timedelta
    today = date.today()
    matters = db.query(Matter).filter(Matter.ca_user_id == u.id, Matter.is_active == True).all()
    matter_ids = [m.id for m in matters]
    urgent = len([m for m in matters if m.status and m.status.value == "urgent"])
    week_h = 0
    today_h = 0
    if matter_ids:
        week_h = db.query(CourtHearing).filter(CourtHearing.matter_id.in_(matter_ids), CourtHearing.hearing_date >= today, CourtHearing.hearing_date <= today + timedelta(days=7)).count()
        today_h = db.query(CourtHearing).filter(CourtHearing.matter_id.in_(matter_ids), CourtHearing.hearing_date == today).count()
    entries = db.query(TimeEntry).filter(TimeEntry.matter_id.in_(matter_ids)).all() if matter_ids else []
    billed = sum(e.amount or 0 for e in entries if e.is_billed)
    return {"total_matters": len(matters), "urgent_matters": urgent, "week_hearings": week_h, "today_hearings": today_h, "total_billed": round(billed, 2), "total_hours": round(sum(e.hours for e in entries), 1)}

@law_router.get("/matters")
def list_matters(status: Optional[str] = None, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    q = db.query(Matter).filter(Matter.ca_user_id == u.id, Matter.is_active == True)
    if status:
        q = q.filter(Matter.status == status)
    matters = q.order_by(Matter.created_at.desc()).all()
    return [{"id": m.id, "matter_number": m.matter_number, "title": m.title, "practice_area": m.practice_area, "court": m.court, "status": m.status.value if m.status else "pending", "client_name": m.client_name, "opposite_party": m.opposite_party, "next_hearing": str(m.next_hearing) if m.next_hearing else None, "assigned_to": m.assigned_to, "created_at": str(m.created_at)} for m in matters]

@law_router.post("/matters", status_code=201)
def create_matter(data: MatterCreate, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    status_val = MatterStatus.PENDING
    if data.status:
        try:
            status_val = MatterStatus(data.status)
        except Exception:
            pass
    m = Matter(
        ca_user_id=u.id,
        matter_number=gen_matter_num(db),
        title=data.title,
        practice_area=data.practice_area,
        court=data.court,
        client_name=data.client_name,
        opposite_party=data.opposite_party,
        brief=data.brief,
        assigned_to=data.assigned_to,
        filed_date=data.filed_date,
        next_hearing=data.next_hearing,
        relief_sought=data.relief_sought,
        status=status_val
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "matter_number": m.matter_number, "title": m.title, "status": m.status.value}

@law_router.get("/matters/{mid}")
def get_matter(mid: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    m = chk_matter(mid, u.id, db)
    hearings = [{"id": h.id, "hearing_date": str(h.hearing_date), "hearing_time": h.hearing_time, "court": h.court, "purpose": h.purpose, "is_attended": h.is_attended} for h in m.hearings]
    entries = [{"id": e.id, "entry_date": str(e.entry_date), "hours": e.hours, "rate_per_hour": e.rate_per_hour, "amount": e.amount, "description": e.description, "is_billed": e.is_billed} for e in m.time_entries]
    return {"id": m.id, "matter_number": m.matter_number, "title": m.title, "practice_area": m.practice_area, "court": m.court, "status": m.status.value if m.status else "pending", "client_name": m.client_name, "opposite_party": m.opposite_party, "brief": m.brief, "next_hearing": str(m.next_hearing) if m.next_hearing else None, "filed_date": str(m.filed_date) if m.filed_date else None, "assigned_to": m.assigned_to, "relief_sought": m.relief_sought, "hearings": hearings, "time_entries": entries}

@law_router.put("/matters/{mid}")
def update_matter(mid: int, data: dict, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    m = chk_matter(mid, u.id, db)
    for k, v in data.items():
        if k == "status":
            try:
                setattr(m, k, MatterStatus(v))
            except Exception:
                pass
        elif hasattr(m, k):
            setattr(m, k, v)
    db.commit()
    return {"updated": True}

@law_router.delete("/matters/{mid}")
def delete_matter(mid: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    m = chk_matter(mid, u.id, db)
    m.is_active = False
    db.commit()
    return {"deleted": True}

@law_router.get("/hearings")
def list_hearings(days: int = 30, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    from datetime import timedelta
    today = date.today()
    matter_ids = [m.id for m in db.query(Matter).filter(Matter.ca_user_id == u.id, Matter.is_active == True).all()]
    if not matter_ids:
        return []
    hs = db.query(CourtHearing).filter(CourtHearing.matter_id.in_(matter_ids), CourtHearing.hearing_date >= today, CourtHearing.hearing_date <= today + timedelta(days=days)).order_by(CourtHearing.hearing_date).all()
    result = []
    for h in hs:
        m = db.query(Matter).filter(Matter.id == h.matter_id).first()
        days_left = (h.hearing_date - today).days
        result.append({"id": h.id, "matter_id": h.matter_id, "matter_number": m.matter_number if m else "", "matter_title": m.title if m else "", "client_name": m.client_name if m else "", "hearing_date": str(h.hearing_date), "hearing_time": h.hearing_time, "court": h.court or (m.court if m else ""), "purpose": h.purpose, "is_attended": h.is_attended, "days_left": days_left, "is_today": days_left == 0, "is_urgent": days_left <= 3})
    return result

@law_router.post("/hearings", status_code=201)
def add_hearing(data: HearingCreate, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    chk_matter(data.matter_id, u.id, db)
    h = CourtHearing(matter_id=data.matter_id, hearing_date=data.hearing_date, hearing_time=data.hearing_time, court=data.court, purpose=data.purpose, notes=data.notes)
    db.add(h)
    db.commit()
    db.refresh(h)
    m = db.query(Matter).filter(Matter.id == data.matter_id).first()
    if m and (not m.next_hearing or h.hearing_date < m.next_hearing):
        m.next_hearing = h.hearing_date
        db.commit()
    return {"id": h.id, "hearing_date": str(h.hearing_date)}

@law_router.put("/hearings/{hid}/attend")
def mark_attended(hid: int, data: dict = {}, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    h = db.query(CourtHearing).filter(CourtHearing.id == hid).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hearing not found")
    h.is_attended = True
    h.outcome = data.get("outcome", "")
    db.commit()
    return {"attended": True}

@law_router.get("/time-entries")
def list_time(matter_id: Optional[int] = None, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    matter_ids = [m.id for m in db.query(Matter).filter(Matter.ca_user_id == u.id).all()]
    if not matter_ids:
        return []
    q = db.query(TimeEntry).filter(TimeEntry.matter_id.in_(matter_ids))
    if matter_id:
        q = q.filter(TimeEntry.matter_id == matter_id)
    entries = q.order_by(TimeEntry.entry_date.desc()).all()
    result = []
    for e in entries:
        m = db.query(Matter).filter(Matter.id == e.matter_id).first()
        result.append({"id": e.id, "matter_id": e.matter_id, "matter_number": m.matter_number if m else "", "matter_title": m.title if m else "", "entry_date": str(e.entry_date), "hours": e.hours, "rate_per_hour": e.rate_per_hour, "amount": e.amount or round(e.hours * e.rate_per_hour, 2), "description": e.description, "is_billed": e.is_billed})
    return result

@law_router.post("/time-entries", status_code=201)
def add_time(data: TimeEntryCreate, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    chk_matter(data.matter_id, u.id, db)
    e = TimeEntry(matter_id=data.matter_id, ca_user_id=u.id, entry_date=data.entry_date, hours=data.hours, rate_per_hour=data.rate_per_hour, description=data.description, amount=round(data.hours * data.rate_per_hour, 2))
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id, "amount": e.amount}

@law_router.put("/time-entries/{eid}/bill")
def mark_billed(eid: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    e = db.query(TimeEntry).filter(TimeEntry.id == eid, TimeEntry.ca_user_id == u.id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    e.is_billed = True
    db.commit()
    return {"billed": True}

@law_router.get("/billing-summary")
def billing_summary(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    matter_ids = [m.id for m in db.query(Matter).filter(Matter.ca_user_id == u.id).all()]
    entries = db.query(TimeEntry).filter(TimeEntry.matter_id.in_(matter_ids)).all() if matter_ids else []
    return {"total_hours": round(sum(e.hours for e in entries), 1), "total_billed": round(sum(e.amount or 0 for e in entries if e.is_billed), 2), "total_unbilled": round(sum(e.amount or 0 for e in entries if not e.is_billed), 2), "total_entries": len(entries)}

@law_router.post("/draft")
def draft_document(data: DraftRequest, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    content = generate_legal_document(data.doc_type, data.client_name, data.opposite_party or "", data.subject, data.jurisdiction or "", data.relief or "")
    doc = LegalDocument(ca_user_id=u.id, matter_id=data.matter_id, doc_type=data.doc_type, title=f"{data.doc_type} - {data.client_name}", content=content, client_name=data.client_name, opposite_party=data.opposite_party, jurisdiction=data.jurisdiction, ai_generated=True)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return {"id": doc.id, "content": content, "title": doc.title}

@law_router.get("/drafts")
def list_drafts(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    docs = db.query(LegalDocument).filter(LegalDocument.ca_user_id == u.id).order_by(LegalDocument.created_at.desc()).limit(20).all()
    return [{"id": d.id, "doc_type": d.doc_type, "title": d.title, "client_name": d.client_name, "created_at": str(d.created_at)} for d in docs]

@law_router.get("/drafts/{did}")
def get_draft(did: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    d = db.query(LegalDocument).filter(LegalDocument.id == did, LegalDocument.ca_user_id == u.id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"id": d.id, "doc_type": d.doc_type, "title": d.title, "content": d.content, "client_name": d.client_name, "created_at": str(d.created_at)}

@law_router.post("/analyze-contract")
def analyze_contract(data: dict, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    text = data.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Contract text required")
    result = analyze_contract(text)
    ca = ContractAnalysis(ca_user_id=u.id, matter_id=data.get("matter_id"), filename=data.get("filename", "contract.pdf"), risk_score=result.get("risk_score", 5), risk_level=result.get("risk_level", "medium"), summary=result.get("summary", ""), red_flags=str(result.get("red_flags", [])), clause_analysis=str(result.get("clause_analysis", [])), recommendations=str(result.get("recommendations", [])))
    db.add(ca)
    db.commit()
    return result

@law_router.post("/research")
def research(data: ResearchRequest, u: User = Depends(get_current_user)):
    result = do_legal_research(data.query, data.court_filter or "")
    return {"result": result, "query": data.query}

class PrecedentRequest(BaseModel):
    matter_type: str
    facts: str
    court: Optional[str] = ""

class EvidenceRequest(BaseModel):
    matter_id: Optional[int] = None
    evidence_list: list
    matter_type: str

@law_router.post("/precedent-search")
def search_precedents(data: PrecedentRequest, u: User = Depends(get_current_user)):
    from app.services.ai.legal_ai import precedent_search
    result = precedent_search(data.matter_type, data.facts, data.court or "")
    return {"result": result, "matter_type": data.matter_type}

@law_router.post("/analyze-evidence")
def analyze_evidence_list(data: EvidenceRequest, u: User = Depends(get_current_user)):
    from app.services.ai.legal_ai import analyze_evidence
    result = analyze_evidence(data.evidence_list, data.matter_type)
    return {"result": result}

@law_router.get("/matters/{mid}/generate-invoice")
def generate_matter_invoice(mid: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    m = chk_matter(mid, u.id, db)
    entries = [e for e in m.time_entries if not e.is_billed]
    if not entries:
        return {"total_amount": 0, "message": "No unbilled entries"}
    total_hours = sum(e.hours for e in entries)
    total_amount = sum(e.amount or (e.hours * e.rate_per_hour) for e in entries)
    gst = total_amount * 0.18
    return {
        "matter_number": m.matter_number,
        "client_name": m.client_name,
        "total_hours": round(total_hours, 1),
        "subtotal": round(total_amount, 2),
        "gst_18pct": round(gst, 2),
        "grand_total": round(total_amount + gst, 2),
        "entries_count": len(entries),
    }

@law_router.get("/retainers")
def list_retainers(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    matters = db.query(Matter).filter(Matter.ca_user_id == u.id, Matter.is_active == True).all()
    result = []
    for m in matters:
        total = sum(e.amount or 0 for e in m.time_entries)
        billed = sum(e.amount or 0 for e in m.time_entries if e.is_billed)
        result.append({
            "matter_id": m.id,
            "matter_number": m.matter_number,
            "client_name": m.client_name,
            "total_value": round(total, 2),
            "billed": round(billed, 2),
            "outstanding": round(total - billed, 2),
        })
    return result
