# fix_all_routes.py - Fixes all AI route handlers
# Run from backend folder: python fix_all_routes.py
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROUTES = os.path.join(BASE, 'app', 'api', 'routes')
os.makedirs(ROUTES, exist_ok=True)

# ── 1. Legal Drafting Route ───────────────────────────────────────────────────
legal_draft = '''# legal_draft_routes.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user
from app.services.ai.ai_service import generate_legal_document, analyze_contract

draft_router = APIRouter(prefix="/legal/draft", tags=["Legal Drafting"])

class DraftRequest(BaseModel):
    doc_type: str
    client_name: str
    opposite_party: str = ""
    subject: str
    jurisdiction: str = "Delhi"
    relief: str = ""
    extra: str = ""

class ContractRequest(BaseModel):
    text: str

@draft_router.post("/generate")
def generate_doc(req: DraftRequest, current_user=Depends(get_current_user)):
    result = generate_legal_document(
        req.doc_type, req.client_name, req.opposite_party,
        req.subject, req.jurisdiction, req.relief, req.extra
    )
    return {"document": result, "doc_type": req.doc_type}

@draft_router.post("/analyze-contract")
def analyze(req: ContractRequest, current_user=Depends(get_current_user)):
    return analyze_contract(req.text)

@draft_router.get("/templates")
def get_templates(current_user=Depends(get_current_user)):
    return {"templates": [
        "Legal Notice", "NDA", "Service Agreement", "Demand Notice",
        "Affidavit", "Plaint", "Legal Opinion", "Rent Agreement",
        "Employment Contract", "Power of Attorney"
    ]}
'''
open(os.path.join(ROUTES, 'legal_draft_routes.py'), 'w', encoding='utf-8').write(legal_draft)
print("1. legal_draft_routes.py created")

# ── 2. Legal Research Route ───────────────────────────────────────────────────
legal_research = '''# legal_research_routes.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user
from app.services.ai.ai_service import do_legal_research, find_precedents

research_router = APIRouter(prefix="/legal/research", tags=["Legal Research"])

class ResearchRequest(BaseModel):
    query: str
    court_filter: Optional[str] = ""

class PrecedentRequest(BaseModel):
    matter_type: str
    facts: str
    court: Optional[str] = ""

@research_router.post("/search")
def search(req: ResearchRequest, current_user=Depends(get_current_user)):
    result = do_legal_research(req.query, req.court_filter)
    return {"result": result, "query": req.query}

@research_router.post("/precedents")
def precedents(req: PrecedentRequest, current_user=Depends(get_current_user)):
    result = find_precedents(req.matter_type, req.facts, req.court)
    return {"result": result}
'''
open(os.path.join(ROUTES, 'legal_research_routes.py'), 'w', encoding='utf-8').write(legal_research)
print("2. legal_research_routes.py created")

# ── 3. Financial Statements Route ─────────────────────────────────────────────
fin_routes = '''# financial_routes.py
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
'''
open(os.path.join(ROUTES, 'financial_routes.py'), 'w', encoding='utf-8').write(fin_routes)
print("3. financial_routes.py created")

# ── 4. GST Routes (ensure exists) ────────────────────────────────────────────
gst_routes = '''# gst_routes.py
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
'''
open(os.path.join(ROUTES, 'gst_routes.py'), 'w', encoding='utf-8').write(gst_routes)
print("4. gst_routes.py created/updated")

# ── 5. Dashboard Route ────────────────────────────────────────────────────────
dashboard_routes = '''# dashboard_routes.py
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
'''
open(os.path.join(ROUTES, 'dashboard_routes.py'), 'w', encoding='utf-8').write(dashboard_routes)
print("5. dashboard_routes.py created")

# ── 6. Update main.py to register all routers ────────────────────────────────
main_path = os.path.join(BASE, 'main.py')
main = open(main_path, encoding='utf-8').read()

new_imports = []
new_routers = []

router_map = [
    ('legal_draft_routes',    'draft_router'),
    ('legal_research_routes', 'research_router'),
    ('financial_routes',      'financial_router'),
    ('gst_routes',            'gst_router'),
    ('dashboard_routes',      'dashboard_router'),
]

for mod, router in router_map:
    if f'from app.api.routes.{mod}' not in main:
        new_imports.append(f'from app.api.routes.{mod} import {router}')
    if f'include_router({router})' not in main:
        new_routers.append(router)

if new_imports:
    # Add imports at the top after existing route imports
    lines = main.split('\n')
    insert_at = 0
    for i, line in enumerate(lines):
        if 'from app.api.routes' in line or 'import' in line:
            insert_at = i
    lines.insert(insert_at + 1, '\n'.join(new_imports))
    main = '\n'.join(lines)

if new_routers:
    for router in new_routers:
        # Try to add after existing include_router calls
        if 'include_router' in main:
            # Find last include_router and add after it
            import re
            last = list(re.finditer(r'app\.include_router\([^)]+\)', main))
            if last:
                pos = last[-1].end()
                main = main[:pos] + f'\n    app.include_router({router})' + main[pos:]
            else:
                main = main.replace('return app', f'    app.include_router({router})\n    return app')
        else:
            main = main.replace('return app', f'    app.include_router({router})\n    return app')

open(main_path, 'w', encoding='utf-8').write(main)
print(f"6. main.py updated — added {len(new_imports)} imports, {len(new_routers)} routers")

print("""
==========================================
✅ All routes created and registered!

Now run:
  taskkill /F /IM python.exe
  uvicorn main:app --port 8000

Then check: http://127.0.0.1:8000/docs
==========================================
""")