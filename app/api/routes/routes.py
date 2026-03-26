from app.services.ai.ai_service import ai_chat_response, generate_financial_insight
"""
Invoice Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from app.db.database import get_db
from app.models import Invoice, Client, User, InvoiceType
from app.schemas import InvoiceCreate, InvoiceResponse
from app.core.security import get_current_user

invoice_router = APIRouter(prefix="/invoices", tags=["Invoices"])


@invoice_router.get("/client/{client_id}", response_model=List[InvoiceResponse])
def list_invoices(
    client_id: int,
    invoice_type: Optional[InvoiceType] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_client_access(client_id, current_user.id, db)
    query = db.query(Invoice).filter(Invoice.client_id == client_id)
    if invoice_type:
        query = query.filter(Invoice.invoice_type == invoice_type)
    return query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit).all()


@invoice_router.post("/client/{client_id}", response_model=InvoiceResponse, status_code=201)
def create_invoice(
    client_id: int,
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_client_access(client_id, current_user.id, db)
    data.client_id = client_id
    invoice = Invoice(**data.model_dump(exclude={"line_items"}))
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@invoice_router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _verify_client_access(inv.client_id, current_user.id, db)
    return inv


@invoice_router.put("/{invoice_id}/verify-gst")
def verify_gst(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    _verify_client_access(inv.client_id, current_user.id, db)

    # Validate GST calculation
    expected_tax = inv.taxable_amount * (inv.cgst_rate + inv.sgst_rate + inv.igst_rate) / 100
    is_valid = abs(expected_tax - inv.total_tax) < 1.0  # Allow ₹1 rounding

    inv.gst_verified = is_valid
    db.commit()
    return {"verified": is_valid, "expected_tax": expected_tax, "actual_tax": inv.total_tax}


def _verify_client_access(client_id: int, user_id: int, db: Session):
    client = db.query(Client).filter(
        Client.id == client_id, Client.ca_user_id == user_id
    ).first()
    if not client:
        raise HTTPException(status_code=403, detail="Access denied")


"""
Compliance Routes
"""
from fastapi import APIRouter
from app.schemas import ComplianceCreate, ComplianceUpdate, ComplianceResponse
from app.models import ComplianceItem, ComplianceStatus

compliance_router = APIRouter(prefix="/compliance", tags=["Compliance"])


@compliance_router.get("/client/{client_id}", response_model=List[ComplianceResponse])
def list_compliance(
    client_id: int,
    status: Optional[ComplianceStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_client_access(client_id, current_user.id, db)
    query = db.query(ComplianceItem).filter(ComplianceItem.client_id == client_id)
    if status:
        query = query.filter(ComplianceItem.status == status)
    return query.order_by(ComplianceItem.due_date.asc()).all()


@compliance_router.get("/alerts/all")
def get_all_alerts(
    days_ahead: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get compliance alerts for all clients of this CA."""
    from datetime import timedelta
    today = date.today()
    deadline = today + timedelta(days=days_ahead)

    # Get all client IDs for this CA
    client_ids = [
        c.id for c in db.query(Client).filter(Client.ca_user_id == current_user.id).all()
    ]

    alerts = db.query(ComplianceItem, Client.company_name).join(
        Client, ComplianceItem.client_id == Client.id
    ).filter(
        ComplianceItem.client_id.in_(client_ids),
        ComplianceItem.due_date <= deadline,
        ComplianceItem.status.in_([ComplianceStatus.PENDING, ComplianceStatus.OVERDUE])
    ).order_by(ComplianceItem.due_date.asc()).limit(50).all()

    # Mark overdue
    result = []
    for item, company_name in alerts:
        if item.due_date < today and item.status == ComplianceStatus.PENDING:
            item.status = ComplianceStatus.OVERDUE
        days_left = (item.due_date - today).days
        result.append({
            "id": item.id,
            "client_id": item.client_id,
            "company_name": company_name,
            "compliance_type": item.compliance_type.value,
            "period": item.period,
            "due_date": item.due_date.isoformat(),
            "status": item.status.value,
            "days_left": days_left,
            "is_overdue": days_left < 0,
        })

    db.commit()
    return result


@compliance_router.post("/client/{client_id}", response_model=ComplianceResponse, status_code=201)
def create_compliance(
    client_id: int,
    data: ComplianceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_client_access(client_id, current_user.id, db)
    data.client_id = client_id
    item = ComplianceItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@compliance_router.put("/{item_id}", response_model=ComplianceResponse)
def update_compliance(
    item_id: int,
    data: ComplianceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(ComplianceItem).filter(ComplianceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Compliance item not found")
    _verify_client_access(item.client_id, current_user.id, db)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


"""
Analytics / Dashboard Routes
"""
from fastapi import APIRouter
from app.schemas import DashboardStats, FinancialInsight
from app.models import Transaction, LedgerEntry, GSTMismatch, Document

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client_ids = [
        c.id for c in db.query(Client).filter(Client.ca_user_id == current_user.id).all()
    ]

    total_clients = len(client_ids)
    active_clients = db.query(func.count(Client.id)).filter(
        Client.ca_user_id == current_user.id, Client.is_active == True
    ).scalar() or 0

    total_invoices = db.query(func.count(Invoice.id)).filter(
        Invoice.client_id.in_(client_ids)
    ).scalar() or 0 if client_ids else 0

    total_revenue = db.query(func.sum(Invoice.total_amount)).filter(
        Invoice.client_id.in_(client_ids),
        Invoice.invoice_type == InvoiceType.SALE
    ).scalar() or 0 if client_ids else 0

    today = date.today()
    pending_compliance = db.query(func.count(ComplianceItem.id)).filter(
        ComplianceItem.client_id.in_(client_ids),
        ComplianceItem.status == ComplianceStatus.PENDING,
        ComplianceItem.due_date >= today
    ).scalar() or 0 if client_ids else 0

    overdue_compliance = db.query(func.count(ComplianceItem.id)).filter(
        ComplianceItem.client_id.in_(client_ids),
        ComplianceItem.due_date < today,
        ComplianceItem.status != ComplianceStatus.FILED
    ).scalar() or 0 if client_ids else 0

    gst_mismatches = db.query(func.count(GSTMismatch.id)).filter(
        GSTMismatch.client_id.in_(client_ids),
        GSTMismatch.is_resolved == False
    ).scalar() or 0 if client_ids else 0

    docs_processed = db.query(func.count(Document.id)).filter(
        Document.client_id.in_(client_ids),
        Document.ocr_status == "completed"
    ).scalar() or 0 if client_ids else 0

    return {
        "total_clients": total_clients,
        "active_clients": active_clients,
        "total_invoices": total_invoices,
        "total_revenue": float(total_revenue),
        "pending_compliance": pending_compliance,
        "overdue_compliance": overdue_compliance,
        "gst_mismatches": gst_mismatches,
        "documents_processed": docs_processed,
    }


@analytics_router.get("/client/{client_id}/financial-insights")
def get_financial_insights(
    client_id: int,
    period: str = Query(default="current_fy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_client_access(client_id, current_user.id, db)

    # Aggregate financial data
    transactions = db.query(Transaction).filter(Transaction.client_id == client_id).all()
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()

    total_income = sum(t.amount for t in transactions if t.transaction_type.value == "credit")
    total_expenses = sum(t.amount for t in transactions if t.transaction_type.value == "debit")

    # Expense breakdown by category
    cat_totals = {}
    for t in transactions:
        if t.transaction_type.value == "debit":
            cat = t.category or "Other"
            cat_totals[cat] = cat_totals.get(cat, 0) + t.amount

    top_categories = sorted(
        [{"category": k, "amount": v} for k, v in cat_totals.items()],
        key=lambda x: x["amount"],
        reverse=True
    )[:10]

    # GST totals
    output_gst = sum(
        (i.cgst_amount + i.sgst_amount + i.igst_amount)
        for i in invoices if i.invoice_type == InvoiceType.SALE
    )
    input_gst = sum(
        (i.cgst_amount + i.sgst_amount + i.igst_amount)
        for i in invoices if i.invoice_type == InvoiceType.PURCHASE
    )

    financial_data = {
        "period": period,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
        "profit_margin": ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0,
        "top_expense_categories": top_categories,
        "output_gst": output_gst,
        "input_gst": input_gst,
        "net_gst_payable": output_gst - input_gst,
        "total_invoices": len(invoices),
        "invoice_breakdown": {
            "sales": len([i for i in invoices if i.invoice_type == InvoiceType.SALE]),
            "purchases": len([i for i in invoices if i.invoice_type == InvoiceType.PURCHASE]),
        }
    }

    # Generate AI insights
    ai_insights = generate_financial_insight(financial_data)
    return {**financial_data, "ai_insights": ai_insights}


@analytics_router.get("/client/{client_id}/gst-summary")
def get_gst_summary(
    client_id: int,
    period: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_client_access(client_id, current_user.id, db)

    query = db.query(Invoice).filter(Invoice.client_id == client_id)
    invoices = query.all()

    sales = [i for i in invoices if i.invoice_type == InvoiceType.SALE]
    purchases = [i for i in invoices if i.invoice_type == InvoiceType.PURCHASE]

    return {
        "total_sales": sum(i.total_amount for i in sales),
        "total_purchases": sum(i.total_amount for i in purchases),
        "output_gst": {
            "cgst": sum(i.cgst_amount for i in sales),
            "sgst": sum(i.sgst_amount for i in sales),
            "igst": sum(i.igst_amount for i in sales),
            "total": sum(i.cgst_amount + i.sgst_amount + i.igst_amount for i in sales),
        },
        "input_gst": {
            "cgst": sum(i.cgst_amount for i in purchases),
            "sgst": sum(i.sgst_amount for i in purchases),
            "igst": sum(i.igst_amount for i in purchases),
            "total": sum(i.cgst_amount + i.sgst_amount + i.igst_amount for i in purchases),
        },
        "net_gst_payable": sum(
            i.cgst_amount + i.sgst_amount + i.igst_amount for i in sales
        ) - sum(
            i.cgst_amount + i.sgst_amount + i.igst_amount for i in purchases
        ),
        "invoice_count": len(invoices),
        "unverified_invoices": len([i for i in invoices if not i.gst_verified]),
    }


"""
Chat Routes
"""
from fastapi import APIRouter
from app.schemas import ChatMessage, ChatResponse
from app.models import AIConversation
import uuid as uuid_lib

chat_router = APIRouter(prefix="/chat", tags=["AI Chat"])


@chat_router.post("/message", response_model=ChatResponse)
async def send_message(
    msg: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_id = msg.session_id or str(uuid_lib.uuid4())

    # Build financial context
    financial_context = {}
    if msg.client_id:
        client = db.query(Client).filter(Client.id == msg.client_id).first()
        if client and client.ca_user_id == current_user.id:
            invoices = db.query(Invoice).filter(Invoice.client_id == msg.client_id).limit(50).all()
            transactions = db.query(Transaction).filter(Transaction.client_id == msg.client_id).limit(50).all()
            compliance = db.query(ComplianceItem).filter(ComplianceItem.client_id == msg.client_id).all()

            financial_context = {
                "client": {"name": client.company_name, "gstin": client.gstin, "industry": client.industry},
                "invoice_summary": {
                    "total": len(invoices),
                    "total_amount": sum(i.total_amount for i in invoices),
                    "output_gst": sum(i.cgst_amount + i.sgst_amount + i.igst_amount for i in invoices if i.invoice_type == InvoiceType.SALE),
                    "input_gst": sum(i.cgst_amount + i.sgst_amount + i.igst_amount for i in invoices if i.invoice_type == InvoiceType.PURCHASE),
                },
                "transactions": [
                    {"date": str(t.transaction_date), "desc": t.description, "amount": t.amount, "type": t.transaction_type.value, "category": t.category}
                    for t in transactions[:20]
                ],
                "compliance_status": [
                    {"type": c.compliance_type.value, "period": c.period, "due": str(c.due_date), "status": c.status.value}
                    for c in compliance[:10]
                ],
            }

    # Get conversation history
    history = db.query(AIConversation).filter(
        AIConversation.session_id == session_id
    ).order_by(AIConversation.created_at.asc()).limit(10).all()

    history_dicts = [{"role": h.role, "message": h.message} for h in history]

    # Get AI response
    response = ai_chat_response(msg.message, financial_context)

    # Save conversation
    user_msg = AIConversation(
        user_id=current_user.id,
        client_id=msg.client_id,
        session_id=session_id,
        role="user",
        message=msg.message,
    )
    ai_msg = AIConversation(
        user_id=current_user.id,
        client_id=msg.client_id,
        session_id=session_id,
        role="assistant",
        message=response,
    )
    db.add_all([user_msg, ai_msg])
    db.commit()

    return ChatResponse(response=response, session_id=session_id)


@chat_router.get("/history/{session_id}")
def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    messages = db.query(AIConversation).filter(
        AIConversation.session_id == session_id,
        AIConversation.user_id == current_user.id,
    ).order_by(AIConversation.created_at.asc()).all()

    return [{"role": m.role, "message": m.message, "timestamp": m.created_at} for m in messages]
