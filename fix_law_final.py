# -*- coding: utf-8 -*-
import os, sys

os.makedirs('app/models', exist_ok=True)
os.makedirs('app/services/ai', exist_ok=True)
os.makedirs('app/api/routes', exist_ok=True)

# ── 1. Law Models ────────────────────────────────────────────────────────
law_model = '''# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class MatterStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    URGENT = "urgent"
    CLOSED = "closed"
    DISCOVERY = "discovery"

class Matter(Base):
    __tablename__ = "matters"
    id = Column(Integer, primary_key=True, index=True)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    matter_number = Column(String(50), unique=True, index=True)
    title = Column(String(500), nullable=False)
    practice_area = Column(String(100))
    court = Column(String(200))
    judge = Column(String(200))
    status = Column(Enum(MatterStatus), default=MatterStatus.PENDING)
    filed_date = Column(Date)
    next_hearing = Column(Date)
    client_name = Column(String(255))
    opposite_party = Column(String(255))
    brief = Column(Text)
    assigned_to = Column(String(255))
    relief_sought = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    hearings = relationship("CourtHearing", back_populates="matter", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="matter", cascade="all, delete-orphan")

class CourtHearing(Base):
    __tablename__ = "court_hearings"
    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    hearing_date = Column(Date, nullable=False)
    hearing_time = Column(String(20))
    court = Column(String(200))
    purpose = Column(String(200))
    notes = Column(Text)
    is_attended = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    outcome = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    matter = relationship("Matter", back_populates="hearings")

class TimeEntry(Base):
    __tablename__ = "time_entries"
    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=False)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    rate_per_hour = Column(Float, nullable=False)
    amount = Column(Float)
    description = Column(Text)
    is_billed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    matter = relationship("Matter", back_populates="time_entries")

class LegalDocument(Base):
    __tablename__ = "legal_documents"
    id = Column(Integer, primary_key=True, index=True)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=True)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doc_type = Column(String(100))
    title = Column(String(500))
    content = Column(Text)
    client_name = Column(String(255))
    opposite_party = Column(String(255))
    jurisdiction = Column(String(200))
    ai_generated = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ContractAnalysis(Base):
    __tablename__ = "contract_analyses"
    id = Column(Integer, primary_key=True, index=True)
    ca_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    matter_id = Column(Integer, ForeignKey("matters.id"), nullable=True)
    filename = Column(String(500))
    risk_score = Column(Float)
    risk_level = Column(String(20))
    summary = Column(Text)
    red_flags = Column(Text)
    clause_analysis = Column(Text)
    recommendations = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
'''
with open('app/models/law.py', 'w', encoding='utf-8') as f:
    f.write(law_model)
print('1. Law models created')

# ── 2. Legal AI Service ───────────────────────────────────────────────────
legal_ai = '''# -*- coding: utf-8 -*-
import json, logging
from app.core.config import settings
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    _client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    AI_OK = bool(settings.OPENAI_API_KEY)
except Exception:
    _client = None
    AI_OK = False

TEMPLATES = {
    "Legal Notice": "Draft a formal Indian Legal Notice with: advocate details placeholder, date, recipient address, subject, numbered facts, 15-day demand, consequences, signature block.",
    "Service Agreement": "Draft a Service Agreement under Indian law with: parties, scope, payment, IP ownership, confidentiality, termination, arbitration clause.",
    "NDA": "Draft an NDA under Indian law with: confidential info definition, obligations, exclusions, 3-year term, remedies, governing law.",
    "Plaint": "Draft a Civil Plaint for Indian District Court with: court name, plaintiff/defendant, cause of action, facts, prayer/relief, verification.",
    "Affidavit": "Draft an Affidavit with: deponent details, sworn statement, numbered paragraphs, verification clause.",
    "Demand Notice": "Draft a Demand Notice under Section 138 NI Act with: cheque details, dishonour details, 15-day demand, legal consequences.",
    "Legal Opinion": "Draft a Legal Opinion with: facts, legal issues, analysis with case citations, conclusion and recommendations.",
    "Rent Agreement": "Draft a Rent Agreement under Indian law with: parties, property, rent, deposit, duration, termination, maintenance.",
    "Employment Contract": "Draft an Employment Contract under Indian law with: designation, CTC, probation, confidentiality, IP assignment, termination.",
    "Power of Attorney": "Draft a Power of Attorney under Indian law with: principal, attorney, specific powers, duration, revocation.",
}

def _call_ai(system_msg, user_msg, json_mode=False):
    if not AI_OK or not _client:
        if json_mode:
            return json.dumps({"error": "OpenAI API key not configured. Add OPENAI_API_KEY to .env"})
        return """LEGAL NOTICE

[Advocate Name & Enrollment No.]
[Firm Name & Address]
Date: [Date]

To,
[Recipient Name]
[Address]

Subject: LEGAL NOTICE

Dear Sir/Madam,

Under instructions of our client [Client Name], we hereby serve this legal notice:

1. That [facts of the matter].
2. That despite requests, you have failed to [action required].
3. You are hereby called upon to [demand] within 15 days of receipt.

Failing compliance, legal proceedings shall be initiated without further notice.

[Advocate Signature]
Note: Add your OpenAI API key in Settings to generate AI-powered documents."""
    try:
        kwargs = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 2000,
            "temperature": 0.2
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        r = _client.chat.completions.create(**kwargs)
        return r.choices[0].message.content
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        if json_mode:
            return json.dumps({"error": str(e)})
        return f"AI generation failed: {e}. Check your OpenAI API key."

def generate_legal_document(doc_type, client_name, opposite_party, subject, jurisdiction, relief, extra=""):
    template = TEMPLATES.get(doc_type, TEMPLATES["Legal Notice"])
    system_msg = f"""You are a senior Indian advocate. {template}
Use formal legal language appropriate for Indian courts.
Generate a complete, ready-to-use document."""
    user_msg = f"""Generate a complete {doc_type} with:
Client / Party A: {client_name}
Opposite Party: {opposite_party}
Matter: {subject}
Jurisdiction: {jurisdiction}
Relief Sought: {relief}
Extra details: {extra}

Generate the full document now."""
    return _call_ai(system_msg, user_msg)

def analyze_contract_text(text):
    system_msg = """You are an expert Indian contract lawyer. Analyze the contract and respond ONLY with valid JSON:
{
  "risk_score": <number 1-10>,
  "risk_level": "<low|medium|high>",
  "summary": "<2-3 sentence summary>",
  "red_flags": ["<flag1>", "<flag2>"],
  "clause_analysis": [
    {"clause": "<name>", "risk": "<high|medium|low>", "description": "<issue>", "recommendation": "<fix>"}
  ],
  "missing_clauses": ["<clause1>"],
  "recommendations": ["<rec1>", "<rec2>"]
}"""
    user_msg = f"Analyze this contract:\\n\\n{text[:4000]}"
    result = _call_ai(system_msg, user_msg, json_mode=True)
    try:
        return json.loads(result)
    except Exception:
        return {
            "risk_score": 5, "risk_level": "medium",
            "summary": "Unable to parse analysis. Check OpenAI API key.",
            "red_flags": [], "clause_analysis": [], "recommendations": []
        }

def do_legal_research(query, court_filter=""):
    system_msg = """You are a senior Indian advocate. Provide legal research with:
1. Relevant Supreme Court and High Court judgments with citations
2. Applicable sections of Indian law
3. Current legal position
4. Practical advice for the matter
Format with clear headings and case citations."""
    user_msg = f"Research: {query}\\nCourt preference: {court_filter or 'All courts'}\\n\\nProvide relevant case law and legal analysis."
    return _call_ai(system_msg, user_msg)
'''
with open('app/services/ai/legal_ai.py', 'w', encoding='utf-8') as f:
    f.write(legal_ai)
open('app/services/ai/__init__.py', 'w', encoding='utf-8').write('')
print('2. Legal AI service created')

# ── 3. Law Routes ─────────────────────────────────────────────────────────
law_routes = '''# -*- coding: utf-8 -*-
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
from app.services.ai.legal_ai import generate_legal_document, analyze_contract_text, do_legal_research

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
    result = analyze_contract_text(text)
    ca = ContractAnalysis(ca_user_id=u.id, matter_id=data.get("matter_id"), filename=data.get("filename", "contract.pdf"), risk_score=result.get("risk_score", 5), risk_level=result.get("risk_level", "medium"), summary=result.get("summary", ""), red_flags=str(result.get("red_flags", [])), clause_analysis=str(result.get("clause_analysis", [])), recommendations=str(result.get("recommendations", [])))
    db.add(ca)
    db.commit()
    return result

@law_router.post("/research")
def research(data: ResearchRequest, u: User = Depends(get_current_user)):
    result = do_legal_research(data.query, data.court_filter or "")
    return {"result": result, "query": data.query}
'''
with open('app/api/routes/law_routes.py', 'w', encoding='utf-8') as f:
    f.write(law_routes)
print('3. Law routes created')

# ── 4. Update main.py ────────────────────────────────────────────────────
content = open('main.py', encoding='utf-8').read()
if 'law_router' not in content:
    old = '    from app.api.routes.routes import ('
    new = '    from app.api.routes.law_routes import law_router\n    from app.api.routes.routes import ('
    content = content.replace(old, new)
    last_router = '    app.include_router(chat_router, prefix="/api/v1")'
    if 'alert_router' in content:
        last_router = '    app.include_router(alert_router, prefix="/api/v1")'
    elif 'org_router' in content:
        last_router = '    app.include_router(org_router, prefix="/api/v1")'
    content = content.replace(last_router, last_router + '\n    app.include_router(law_router, prefix="/api/v1")')
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('4. main.py updated')
else:
    print('4. main.py already has law_router')

# ── 5. Create DB tables ──────────────────────────────────────────────────
from app.db.database import engine, Base
from app.models.law import Matter, CourtHearing, TimeEntry, LegalDocument, ContractAnalysis
Base.metadata.create_all(bind=engine)
print('5. Law DB tables created')

# ── 6. Seed sample data ──────────────────────────────────────────────────
from app.db.database import SessionLocal
from app.models import User
from app.models.law import Matter, MatterStatus, CourtHearing
from datetime import date, timedelta

db = SessionLocal()
try:
    if not db.query(Matter).first():
        user = db.query(User).first()
        if user:
            samples = [
                dict(title="Ramesh Gupta vs ABC Builders - Property Dispute", practice_area="Civil", court="High Court Delhi", client_name="Ramesh Gupta", opposite_party="ABC Builders Pvt Ltd", status=MatterStatus.ACTIVE, brief="Refund of advance amount for flat purchase", relief_sought="Refund Rs 15L with 18% interest"),
                dict(title="XYZ Corp vs Vendor - Contract Breach", practice_area="Corporate", court="District Court Mumbai", client_name="XYZ Corp Ltd", opposite_party="TechSupply Pvt Ltd", status=MatterStatus.DISCOVERY, brief="Breach of service agreement"),
                dict(title="Priya Holdings - Trademark Infringement", practice_area="IP Trademark", court="IP Appellate Board", client_name="Priya Holdings", opposite_party="Copycat Brands Ltd", status=MatterStatus.URGENT, brief="Trademark infringement similar brand name"),
                dict(title="Arun Mehta vs Employer - Wrongful Termination", practice_area="Labour Employment", court="Labour Court Chennai", client_name="Arun Mehta", opposite_party="Mega Corp India", status=MatterStatus.ACTIVE, brief="Wrongful termination without notice"),
                dict(title="StarTech Pvt Ltd - NCLT Merger Approval", practice_area="Corporate", court="NCLT Mumbai", client_name="StarTech Pvt Ltd", opposite_party="", status=MatterStatus.PENDING, brief="Merger approval application"),
            ]
            today = date.today()
            for i, s in enumerate(samples):
                m = Matter(ca_user_id=user.id, matter_number=f"MAT-2024-{i+1:03d}", **s)
                db.add(m)
                db.flush()
                h = CourtHearing(matter_id=m.id, hearing_date=today + timedelta(days=i*7+3), hearing_time="10:30 AM", court=m.court, purpose=["Final Arguments","Preliminary Hearing","Evidence Hearing","Conciliation","First Hearing"][i])
                db.add(h)
            db.commit()
            print('6. Sample matters seeded')
    else:
        print('6. Matters already exist - skipped')
finally:
    db.close()

print('\n===================================')
print('   LAW FIRM BACKEND COMPLETE!')
print('===================================')
print('Run: uvicorn main:app --port 8000')