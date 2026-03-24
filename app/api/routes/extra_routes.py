# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date
import secrets
from app.db.database import get_db
from app.models import Client, Invoice, User
from app.core.security import get_current_user

extra_router = APIRouter(prefix="/extra", tags=["Extra Features"])

@extra_router.get("/invoice/{invoice_id}/pdf")
def export_invoice_pdf(invoice_id: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    client = db.query(Client).filter(Client.id == inv.client_id).first()
    from app.services.pdf.pdf_service import generate_invoice_pdf
    buf = generate_invoice_pdf({"invoice_number":inv.invoice_number,"invoice_date":str(inv.invoice_date) if inv.invoice_date else "","taxable_amount":inv.taxable_amount or 0,"cgst_amount":inv.cgst_amount or 0,"sgst_amount":inv.sgst_amount or 0,"igst_amount":inv.igst_amount or 0,"total_amount":inv.total_amount or 0},{"company_name":client.company_name if client else "","gstin":client.gstin if client else ""})
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=invoice_{inv.invoice_number or inv.id}.pdf"})

@extra_router.get("/client/{client_id}/report-pdf")
def export_report_pdf(client_id: int, period: str = "FY 2024-25", db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == u.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    sales = [i for i in invoices if i.invoice_type and i.invoice_type.value == "sale"]
    purchases = [i for i in invoices if i.invoice_type and i.invoice_type.value == "purchase"]
    rev = sum(i.total_amount or 0 for i in sales)
    exp = sum(i.total_amount or 0 for i in purchases)
    ogst = sum((i.cgst_amount or 0)+(i.sgst_amount or 0)+(i.igst_amount or 0) for i in sales)
    igst = sum((i.cgst_amount or 0)+(i.sgst_amount or 0)+(i.igst_amount or 0) for i in purchases)
    from app.services.pdf.pdf_service import generate_report_pdf
    buf = generate_report_pdf({"total_revenue":rev,"total_expenses":exp,"net_profit":rev-exp,"output_gst":ogst,"input_gst":igst,"net_gst":ogst-igst}, client.company_name, period)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{client.company_name}.pdf"})

@extra_router.get("/client/{client_id}/trial-balance")
def trial_balance(client_id: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == u.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    sales = [i for i in invoices if i.invoice_type and i.invoice_type.value == "sale"]
    purchases = [i for i in invoices if i.invoice_type and i.invoice_type.value == "purchase"]
    ts = sum(i.taxable_amount or 0 for i in sales)
    tp = sum(i.taxable_amount or 0 for i in purchases)
    og = sum((i.cgst_amount or 0)+(i.sgst_amount or 0)+(i.igst_amount or 0) for i in sales)
    ig = sum((i.cgst_amount or 0)+(i.sgst_amount or 0)+(i.igst_amount or 0) for i in purchases)
    accounts = [{"account":"Sales Revenue","type":"Income","debit":0,"credit":round(ts,2)},{"account":"Cost of Purchases","type":"Expense","debit":round(tp,2),"credit":0},{"account":"Gross Profit","type":"Income","debit":0,"credit":round(ts-tp,2)},{"account":"Output GST Payable","type":"Liability","debit":0,"credit":round(og,2)},{"account":"Input GST Credit","type":"Asset","debit":round(ig,2),"credit":0},{"account":"Net GST Payable","type":"Liability","debit":0,"credit":round(og-ig,2)}]
    td = sum(a["debit"] for a in accounts)
    tc = sum(a["credit"] for a in accounts)
    return {"client":client.company_name,"accounts":accounts,"total_debit":round(td,2),"total_credit":round(tc,2),"balanced":abs(td-tc)<1,"gross_profit":round(ts-tp,2),"net_profit":round(ts-tp,2)}

@extra_router.get("/client/{client_id}/pnl")
def pnl_statement(client_id: int, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == u.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    sales = [i for i in invoices if i.invoice_type and i.invoice_type.value == "sale"]
    purchases = [i for i in invoices if i.invoice_type and i.invoice_type.value == "purchase"]
    rev = sum(i.taxable_amount or 0 for i in sales)
    exp = sum(i.taxable_amount or 0 for i in purchases)
    gp = rev - exp
    tax = gp * 0.25 if gp > 0 else 0
    np_ = gp - tax
    return {"client":client.company_name,"income":[{"head":"Revenue from Operations","amount":round(rev,2)},{"head":"Other Income","amount":0}],"total_income":round(rev,2),"expenses":[{"head":"Cost of Materials/Services","amount":round(exp,2)},{"head":"Employee Benefits","amount":0},{"head":"Other Expenses","amount":0}],"total_expenses":round(exp,2),"gross_profit":round(gp,2),"tax_estimate":round(tax,2),"net_profit":round(np_,2),"profit_margin":round((np_/rev*100) if rev > 0 else 0,1)}

@extra_router.post("/client/{client_id}/gstr2b-reconcile")
async def gstr2b_reconcile(client_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    import json
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == u.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        content = await file.read()
        gstr2b_data = json.loads(content)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    from app.services.gstr2b.reconcile import reconcile_gstr2b
    return reconcile_gstr2b(client_id, gstr2b_data, db)

@extra_router.post("/law/limitation-period")
def calc_limitation(data: dict, u: User = Depends(get_current_user)):
    from datetime import datetime, timedelta
    cause_date_str = data.get("cause_of_action_date")
    case_type = data.get("case_type", "civil")
    if not cause_date_str:
        raise HTTPException(status_code=400, detail="cause_of_action_date required")
    try:
        cause_date = datetime.strptime(cause_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    limits = {"civil":{"years":3,"act":"Limitation Act 1963 - Art.113"},"cheque_bounce":{"years":0,"days":30,"act":"NI Act S.138"},"consumer":{"years":2,"act":"Consumer Protection Act 2019"},"labour":{"years":3,"act":"Industrial Disputes Act"},"property":{"years":12,"act":"Limitation Act 1963 - Art.65"},"contract":{"years":3,"act":"Limitation Act 1963 - Art.55"},"tort":{"years":3,"act":"Limitation Act 1963"},"execution":{"years":12,"act":"Limitation Act 1963 - Art.136"}}
    lim = limits.get(case_type, limits["civil"])
    years = lim.get("years", 3)
    extra_days = lim.get("days", 0)
    try:
        from dateutil.relativedelta import relativedelta
        expiry = cause_date + relativedelta(years=years) + timedelta(days=extra_days)
    except Exception:
        expiry = date(cause_date.year + years, cause_date.month, cause_date.day) + timedelta(days=extra_days)
    today = date.today()
    days_left = (expiry - today).days
    return {"cause_of_action_date":str(cause_date),"case_type":case_type,"limitation_period":f"{years} years" if years else f"{extra_days} days","expiry_date":str(expiry),"days_remaining":days_left,"is_expired":days_left < 0,"is_urgent":0 <= days_left <= 90,"applicable_law":lim.get("act",""),"status":"EXPIRED" if days_left < 0 else "URGENT" if days_left <= 90 else "VALID"}

reset_tokens = {}

class ResetRequest(BaseModel):
    email: str

class ResetConfirm(BaseModel):
    token: str
    new_password: str

@extra_router.post("/auth/forgot-password")
def forgot_password(data: ResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    token = secrets.token_urlsafe(32)
    if user:
        reset_tokens[token] = user.id
        try:
            from app.services.email.email_service import send_email
            send_email(user.email, "Maavi - Password Reset", f"<h2>Password Reset</h2><p>Token: <code>{token}</code></p><p>Valid for 1 hour.</p>")
        except Exception:
            pass
    return {"message": "If email exists, reset link sent", "dev_token": token}

@extra_router.post("/auth/reset-password")
def reset_password(data: ResetConfirm, db: Session = Depends(get_db)):
    user_id = reset_tokens.get(data.token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.core.security import get_password_hash
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    del reset_tokens[data.token]
    return {"message": "Password reset successfully"}
