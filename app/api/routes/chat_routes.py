# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from app.db.database import get_db
from app.models import Client, Invoice, ComplianceItem
from app.core.security import get_current_user
from app.services.ai.ai_service import ai_chat_response

chat_router = APIRouter(prefix="/chat", tags=["AI Chat"])

class ChatRequest(BaseModel):
    message: str
    client_id: Optional[int] = None
    session_id: Optional[str] = None

@chat_router.post("/")
def chat(req: ChatRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message required")
    session_id = req.session_id or str(uuid.uuid4())
    client_data = None
    if req.client_id:
        c = db.query(Client).filter(Client.id==req.client_id, Client.ca_user_id==current_user.id).first()
        if c:
            inv = db.query(Invoice).filter(Invoice.client_id==c.id).limit(20).all()
            comp = db.query(ComplianceItem).filter(ComplianceItem.client_id==c.id).limit(10).all()
            def val(x): return str(x.value) if hasattr(x,"value") else str(x)
            client_data = {
                "company_name": c.company_name,
                "gstin": getattr(c,"gstin",""),
                "total_revenue": sum(float(i.total_amount or 0) for i in inv if val(getattr(i,"invoice_type",""))=="sale"),
                "total_expenses": sum(float(i.total_amount or 0) for i in inv if val(getattr(i,"invoice_type",""))=="purchase"),
                "pending_compliance": sum(1 for x in comp if val(getattr(x,"status","")) in ["pending","overdue"]),
            }
    resp = ai_chat_response(req.message, client_data)
    return {"response": resp, "session_id": session_id, "client_id": req.client_id, "status":"success"}

@chat_router.get("/history/{session_id}")
def get_history(session_id: str, current_user=Depends(get_current_user)):
    return {"session_id": session_id, "messages": []}
