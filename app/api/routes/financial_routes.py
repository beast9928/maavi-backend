# financial_routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.models import Client, Invoice
from app.services.ai.ai_service import generate_financial_insight

financial_router = APIRouter(prefix="/financial", tags=["Financial"])

@financial_router.get("/statements/{client_id}")
def get_statements(client_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == current_user.id).first()
    if not client:
        return {"error": "Client not found"}
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    sales = [i for i in invoices if i.invoice_type and str(i.invoice_type.value) == "sale"]
    purchases = [i for i in invoices if i.invoice_type and str(i.invoice_type.value) == "purchase"]
    total_revenue = sum(i.total_amount or 0 for i in sales)
    total_expenses = sum(i.total_amount or 0 for i in purchases)
    return {
        "client": client.company_name,
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": total_revenue - total_expenses,
        "total_invoices": len(invoices),
        "sales_count": len(sales),
        "purchase_count": len(purchases),
    }

@financial_router.get("/insights/{client_id}")
def get_insights(client_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == current_user.id).first()
    if not client:
        return {"error": "Client not found"}
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    invoice_data = [{"invoice_type": str(i.invoice_type.value) if i.invoice_type else "", "total_amount": i.total_amount or 0} for i in invoices]
    insight = generate_financial_insight(client.company_name, invoice_data, [])
    return {"insight": insight, "client": client.company_name}
