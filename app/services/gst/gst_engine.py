import re
from sqlalchemy.orm import Session
from app.models import Invoice, GSTMismatch

GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}$")

def validate_gstin(g):
    return bool(g and GSTIN_RE.match(g.upper().strip()))

def get_gstin_state(gstin):
    STATES = {"01":"J&K","02":"HP","03":"Punjab","04":"Chandigarh","05":"Uttarakhand","06":"Haryana","07":"Delhi","08":"Rajasthan","09":"UP","10":"Bihar","18":"Assam","19":"WB","20":"Jharkhand","21":"Odisha","22":"CG","23":"MP","24":"Gujarat","27":"Maharashtra","29":"Karnataka","32":"Kerala","33":"TN","36":"Telangana"}
    return STATES.get(gstin[:2], "Unknown") if gstin and len(gstin) >= 2 else "Unknown"

def run_gst_analysis(client_id, db):
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    issues = []
    for inv in invoices:
        if inv.vendor_gstin and not validate_gstin(inv.vendor_gstin):
            issues.append({"invoice_id":inv.id,"type":"invalid_gstin","severity":"high","description":f"Invalid GSTIN: {inv.vendor_gstin}","vendor_gstin":inv.vendor_gstin,"invoice_number":inv.invoice_number})
        if inv.taxable_amount and inv.taxable_amount > 0:
            rate = (inv.cgst_rate or 0)+(inv.sgst_rate or 0)+(inv.igst_rate or 0)
            expected = round(inv.taxable_amount * rate / 100, 2)
            actual = round((inv.cgst_amount or 0)+(inv.sgst_amount or 0)+(inv.igst_amount or 0), 2)
            if rate > 0 and abs(expected - actual) > 1.0:
                issues.append({"invoice_id":inv.id,"type":"gst_calculation_error","severity":"medium","description":f"Expected Rs.{expected}, found Rs.{actual}","our_amount":actual,"portal_amount":expected,"difference":round(expected-actual,2),"invoice_number":inv.invoice_number})
        if not inv.invoice_number:
            issues.append({"invoice_id":inv.id,"type":"missing_invoice_number","severity":"low","description":"Invoice number missing","invoice_number":None})
    for issue in issues:
        from app.models import GSTMismatch
        ex = db.query(GSTMismatch).filter(GSTMismatch.invoice_id==issue.get("invoice_id"),GSTMismatch.mismatch_type==issue["type"],GSTMismatch.is_resolved==False).first()
        if not ex:
            m = GSTMismatch(client_id=client_id,invoice_id=issue.get("invoice_id"),mismatch_type=issue["type"],description=issue["description"],our_amount=issue.get("our_amount"),portal_amount=issue.get("portal_amount"),difference=issue.get("difference"),vendor_gstin=issue.get("vendor_gstin"),invoice_number=issue.get("invoice_number"))
            db.add(m)
    db.commit()
    sales = [i for i in invoices if i.invoice_type and i.invoice_type.value == "sale"]
    purchases = [i for i in invoices if i.invoice_type and i.invoice_type.value == "purchase"]
    output_gst = sum((i.cgst_amount or 0)+(i.sgst_amount or 0)+(i.igst_amount or 0) for i in sales)
    input_gst = sum((i.cgst_amount or 0)+(i.sgst_amount or 0)+(i.igst_amount or 0) for i in purchases)
    return {"total_invoices":len(invoices),"issues_found":len(issues),"output_gst":round(output_gst,2),"input_gst":round(input_gst,2),"net_payable":round(output_gst-input_gst,2),"issues":issues,"health":"good" if len(issues)==0 else "warning" if len(issues)<=3 else "critical"}

def get_gst_mismatches(client_id, db):
    return db.query(GSTMismatch).filter(GSTMismatch.client_id==client_id).order_by(GSTMismatch.created_at.desc()).all()

def resolve_mismatch(mismatch_id, db):
    from datetime import datetime
    m = db.query(GSTMismatch).filter(GSTMismatch.id==mismatch_id).first()
    if m:
        m.is_resolved = True
        m.resolved_at = datetime.utcnow()
        db.commit()
        return True
    return False
