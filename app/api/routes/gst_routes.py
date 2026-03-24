# gst_routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.db.database import get_db
from app.core.security import get_current_user
from app.models import Client, Invoice, ComplianceItem

gst_router = APIRouter(prefix="/gst", tags=["GST"])

@gst_router.get("/summary/{client_id}")
def gst_summary(client_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    total_cgst = sum(i.cgst_amount or 0 for i in invoices)
    total_sgst = sum(i.sgst_amount or 0 for i in invoices)
    total_igst = sum(i.igst_amount or 0 for i in invoices)
    return {
        "client": client.company_name,
        "gstin": client.gstin,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "total_gst": total_cgst + total_sgst + total_igst,
        "invoice_count": len(invoices),
    }

@gst_router.get("/compliance/{client_id}")
def gst_compliance(client_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    items = db.query(ComplianceItem).filter(ComplianceItem.client_id == client_id).all()
    return {
        "client": client.company_name,
        "compliance_items": [
            {
                "id": c.id,
                "title": c.title,
                "due_date": str(c.due_date) if c.due_date else None,
                "status": str(c.status.value) if c.status else "pending",
                "filing_type": c.filing_type,
            } for c in items
        ]
    }
