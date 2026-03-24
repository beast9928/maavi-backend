# compliance_calendar_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Enum as SAEnum
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime, timedelta
from app.db.database import get_db, Base
from app.core.security import get_current_user
import enum

class EventPriority(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"
    urgent = "urgent"

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = {"extend_existing": True}
    id          = Column(Integer, primary_key=True, index=True)
    ca_user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id   = Column(Integer, ForeignKey("clients.id"), nullable=True)
    title       = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date    = Column(Date, nullable=False)
    event_type  = Column(String, default="compliance")
    filing_type = Column(String, nullable=True)
    priority    = Column(SAEnum(EventPriority), default=EventPriority.medium)
    is_completed = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    recurrence  = Column(String, nullable=True)

try:
    from app.db.database import engine
    CalendarEvent.__table__.create(bind=engine, checkfirst=True)
except Exception:
    pass

class EventCreate(BaseModel):
    client_id:    Optional[int] = None
    title:        str
    description:  Optional[str] = None
    due_date:     date
    event_type:   str = "compliance"
    filing_type:  Optional[str] = None
    priority:     str = "medium"
    is_recurring: bool = False
    recurrence:   Optional[str] = None

calendar_router = APIRouter(prefix="/calendar", tags=["Compliance Calendar"])

# Statutory due dates for Indian CA firms
STATUTORY_DATES = [
    # GST
    {"title": "GSTR-1 (Monthly)",    "day": 11, "months": [1,2,3,4,5,6,7,8,9,10,11,12], "type": "GST",    "priority": "high"},
    {"title": "GSTR-3B (Monthly)",   "day": 20, "months": [1,2,3,4,5,6,7,8,9,10,11,12], "type": "GST",    "priority": "high"},
    {"title": "GSTR-9 Annual",       "day": 31, "months": [12],                           "type": "GST",    "priority": "urgent"},
    # TDS
    {"title": "TDS Deposit",         "day": 7,  "months": [1,2,3,4,5,6,7,8,9,10,11,12], "type": "TDS",    "priority": "high"},
    {"title": "TDS Return Q1 (24Q)", "day": 31, "months": [7],                            "type": "TDS",    "priority": "high"},
    {"title": "TDS Return Q2 (24Q)", "day": 31, "months": [10],                           "type": "TDS",    "priority": "high"},
    {"title": "TDS Return Q3 (24Q)", "day": 31, "months": [1],                            "type": "TDS",    "priority": "high"},
    {"title": "TDS Return Q4 (24Q)", "day": 31, "months": [5],                            "type": "TDS",    "priority": "high"},
    # Income Tax
    {"title": "Advance Tax Q1",      "day": 15, "months": [6],                            "type": "IT",     "priority": "high"},
    {"title": "Advance Tax Q2",      "day": 15, "months": [9],                            "type": "IT",     "priority": "high"},
    {"title": "Advance Tax Q3",      "day": 15, "months": [12],                           "type": "IT",     "priority": "high"},
    {"title": "Advance Tax Q4",      "day": 15, "months": [3],                            "type": "IT",     "priority": "high"},
    {"title": "ITR Filing (Non-Audit)", "day": 31, "months": [7],                         "type": "IT",     "priority": "urgent"},
    {"title": "ITR Filing (Audit)",  "day": 31, "months": [10],                           "type": "IT",     "priority": "urgent"},
    {"title": "Tax Audit Report",    "day": 30, "months": [9],                            "type": "IT",     "priority": "urgent"},
    # ROC / MCA
    {"title": "MCA Annual Return",   "day": 30, "months": [11],                           "type": "ROC",    "priority": "medium"},
    {"title": "MCA Financial Stmt",  "day": 30, "months": [10],                           "type": "ROC",    "priority": "medium"},
    # PF / ESI
    {"title": "PF Payment",          "day": 15, "months": [1,2,3,4,5,6,7,8,9,10,11,12], "type": "PF/ESI", "priority": "medium"},
    {"title": "ESI Payment",         "day": 15, "months": [1,2,3,4,5,6,7,8,9,10,11,12], "type": "PF/ESI", "priority": "medium"},
]

@calendar_router.get("/statutory-dates")
def get_statutory_dates(
    year: int = None,
    month: int = None,
    current_user=Depends(get_current_user)
):
    today = date.today()
    year  = year or today.year
    events = []
    for sd in STATUTORY_DATES:
        for m in sd["months"]:
            try:
                d = date(year, m, sd["day"])
                if month and d.month != month:
                    continue
                days_left = (d - today).days
                events.append({
                    "title":       sd["title"],
                    "due_date":    str(d),
                    "filing_type": sd["type"],
                    "priority":    sd["priority"],
                    "days_left":   days_left,
                    "is_overdue":  days_left < 0,
                    "is_urgent":   0 <= days_left <= 7,
                })
            except ValueError:
                pass
    events.sort(key=lambda x: x["due_date"])
    return {"events": events, "year": year, "month": month}

@calendar_router.get("/upcoming")
def get_upcoming(days: int = 30, current_user=Depends(get_current_user)):
    today = date.today()
    end   = today + timedelta(days=days)
    events = []
    for sd in STATUTORY_DATES:
        for m in sd["months"]:
            for y in [today.year, today.year + 1]:
                try:
                    d = date(y, m, sd["day"])
                    if today <= d <= end:
                        events.append({
                            "title":       sd["title"],
                            "due_date":    str(d),
                            "filing_type": sd["type"],
                            "priority":    sd["priority"],
                            "days_left":   (d - today).days,
                        })
                except ValueError:
                    pass
    events.sort(key=lambda x: x["due_date"])
    return {"events": events, "period_days": days}

@calendar_router.post("/events")
def create_event(req: EventCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    event = CalendarEvent(
        ca_user_id=current_user.id,
        client_id=req.client_id,
        title=req.title,
        description=req.description,
        due_date=req.due_date,
        event_type=req.event_type,
        filing_type=req.filing_type,
        priority=EventPriority(req.priority),
        is_recurring=req.is_recurring,
        recurrence=req.recurrence,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"id": event.id, "title": event.title, "due_date": str(event.due_date)}

@calendar_router.get("/events")
def list_events(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    events = db.query(CalendarEvent).filter(CalendarEvent.ca_user_id == current_user.id).all()
    today  = date.today()
    return {"events": [
        {
            "id":           e.id,
            "title":        e.title,
            "due_date":     str(e.due_date),
            "event_type":   e.event_type,
            "priority":     str(e.priority.value) if e.priority else "medium",
            "is_completed": e.is_completed,
            "days_left":    (e.due_date - today).days if e.due_date else None,
            "is_overdue":   (e.due_date < today and not e.is_completed) if e.due_date else False,
        } for e in events
    ]}

@calendar_router.patch("/events/{event_id}/complete")
def mark_complete(event_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id, CalendarEvent.ca_user_id == current_user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.is_completed = True
    db.commit()
    return {"status": "completed"}
