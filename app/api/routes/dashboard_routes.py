# dashboard_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.models import Client, Invoice, ComplianceItem

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@dashboard_router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    clients = db.query(Client).filter(Client.ca_user_id == current_user.id).all()
    client_ids = [c.id for c in clients]
    invoices = db.query(Invoice).filter(Invoice.client_id.in_(client_ids)).all() if client_ids else []
    compliance = db.query(ComplianceItem).filter(ComplianceItem.client_id.in_(client_ids)).all() if client_ids else []
    total_revenue = sum(i.total_amount or 0 for i in invoices if i.invoice_type and str(i.invoice_type.value) == "sale")
    total_expenses = sum(i.total_amount or 0 for i in invoices if i.invoice_type and str(i.invoice_type.value) == "purchase")
    pending_compliance = sum(1 for c in compliance if c.status and str(c.status.value) in ["pending", "overdue"])
    overdue_compliance = sum(1 for c in compliance if c.status and str(c.status.value) == "overdue")
    return {
        "total_clients": len(clients),
        "total_invoices": len(invoices),
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": total_revenue - total_expenses,
        "pending_compliance": pending_compliance,
        "overdue_compliance": overdue_compliance,
        "total_gst": sum((i.cgst_amount or 0) + (i.sgst_amount or 0) + (i.igst_amount or 0) for i in invoices),
    }

@dashboard_router.get("/recent-activity")
def recent_activity(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    clients = db.query(Client).filter(Client.ca_user_id == current_user.id).all()
    client_ids = [c.id for c in clients]
    invoices = db.query(Invoice).filter(Invoice.client_id.in_(client_ids)).order_by(Invoice.id.desc()).limit(5).all() if client_ids else []
    compliance = db.query(ComplianceItem).filter(ComplianceItem.client_id.in_(client_ids)).order_by(ComplianceItem.id.desc()).limit(5).all() if client_ids else []
    return {
        "recent_invoices": [
            {"id": i.id, "invoice_number": i.invoice_number, "vendor_name": i.vendor_name, "total_amount": i.total_amount, "invoice_type": str(i.invoice_type.value) if i.invoice_type else ""}
            for i in invoices
        ],
        "recent_compliance": [
            {"id": c.id, "title": c.title, "due_date": str(c.due_date) if c.due_date else None, "status": str(c.status.value) if c.status else "pending"}
            for c in compliance
        ],
    }
