from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db.database import get_db
from app.models import Client, User, Invoice, ComplianceItem, ComplianceStatus, GSTMismatch
from app.schemas import ClientCreate, ClientUpdate, ClientResponse, ClientSummary
from app.core.security import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("", response_model=List[ClientSummary])
def list_clients(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Client).filter(Client.ca_user_id == current_user.id)
    if search:
        query = query.filter(
            Client.company_name.ilike(f"%{search}%") |
            Client.gstin.ilike(f"%{search}%") |
            Client.pan.ilike(f"%{search}%")
        )
    clients = query.offset(skip).limit(limit).all()

    result = []
    for c in clients:
        total_invoices = db.query(func.count(Invoice.id)).filter(Invoice.client_id == c.id).scalar() or 0
        total_revenue = db.query(func.sum(Invoice.total_amount)).filter(
            Invoice.client_id == c.id
        ).scalar() or 0
        pending_compliance = db.query(func.count(ComplianceItem.id)).filter(
            ComplianceItem.client_id == c.id,
            ComplianceItem.status.in_([ComplianceStatus.PENDING, ComplianceStatus.OVERDUE])
        ).scalar() or 0
        gst_mismatches = db.query(func.count(GSTMismatch.id)).filter(
            GSTMismatch.client_id == c.id,
            GSTMismatch.is_resolved == False
        ).scalar() or 0

        summary = ClientSummary(
            id=c.id,
            company_name=c.company_name,
            pan=c.pan,
            gstin=c.gstin,
            email=c.email,
            phone=c.phone,
            address=c.address,
            state=c.state,
            business_type=c.business_type,
            industry=c.industry,
            is_active=c.is_active,
            notes=c.notes,
            created_at=c.created_at,
            total_invoices=len(c.invoices) if hasattr(c, "invoices") else 0,
            total_revenue=sum(i.total_amount or 0 for i in c.invoices) if hasattr(c, "invoices") else 0,
            pending_compliance=len([x for x in c.compliance_items if str(x.status).endswith("PENDING")]) if hasattr(c, "compliance_items") else 0,
            gst_mismatches=len([x for x in c.gst_mismatches if not x.is_resolved]) if hasattr(c, "gst_mismatches") else 0,
        )
        summary.total_invoices = total_invoices
        summary.total_revenue = float(total_revenue)
        summary.pending_compliance = pending_compliance
        summary.gst_mismatches = gst_mismatches
        result.append(summary)

    return result


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = Client(**data.model_dump(), ca_user_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)

    # Auto-create standard compliance items
    _seed_compliance_items(client, db)
    return client


@router.get("/{client_id}", response_model=ClientSummary)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = _get_client_or_404(client_id, current_user.id, db)
    total_invoices = db.query(func.count(Invoice.id)).filter(Invoice.client_id == client_id).scalar() or 0
    total_revenue = db.query(func.sum(Invoice.total_amount)).filter(Invoice.client_id == client_id).scalar() or 0
    pending_compliance = db.query(func.count(ComplianceItem.id)).filter(
        ComplianceItem.client_id == client_id,
        ComplianceItem.status.in_([ComplianceStatus.PENDING, ComplianceStatus.OVERDUE])
    ).scalar() or 0

    summary = ClientSummary.model_validate(client)
    summary.total_invoices = total_invoices
    summary.total_revenue = float(total_revenue)
    summary.pending_compliance = pending_compliance
    return summary


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = _get_client_or_404(client_id, current_user.id, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = _get_client_or_404(client_id, current_user.id, db)
    client.is_active = False
    db.commit()
    return {"message": "Client deactivated successfully"}


def _get_client_or_404(client_id: int, user_id: int, db: Session) -> Client:
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.ca_user_id == user_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


def _seed_compliance_items(client: Client, db: Session):
    """Seed standard compliance deadlines for new client."""
    from datetime import date, timedelta
    from app.models import ComplianceItem, ComplianceType
    import calendar

    today = date.today()
    current_year = today.year
    current_month = today.month

    # GST monthly filings for next 3 months
    for i in range(3):
        month = (current_month + i - 1) % 12 + 1
        year = current_year + (current_month + i - 1) // 12
        _, last_day = calendar.monthrange(year, month)
        due = date(year, month, 20)  # GSTR-3B due on 20th

        item = ComplianceItem(
            client_id=client.id,
            compliance_type=ComplianceType.GST_FILING,
            period=f"{year}-{month:02d}",
            due_date=due,
        )
        db.add(item)

    # Quarterly TDS
    tds_quarters = [
        (f"Q1-{current_year}", date(current_year, 7, 31)),
        (f"Q2-{current_year}", date(current_year, 10, 31)),
        (f"Q3-{current_year}", date(current_year + 1, 1, 31)),
        (f"Q4-{current_year}", date(current_year + 1, 5, 31)),
    ]
    for period, due in tds_quarters:
        item = ComplianceItem(
            client_id=client.id,
            compliance_type=ComplianceType.TDS_RETURN,
            period=period,
            due_date=due,
        )
        db.add(item)

    # Annual ITR
    itr_item = ComplianceItem(
        client_id=client.id,
        compliance_type=ComplianceType.INCOME_TAX,
        period=f"FY{current_year}-{str(current_year + 1)[2:]}",
        due_date=date(current_year + 1, 7, 31),
    )
    db.add(itr_item)
    db.commit()
