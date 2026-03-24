# -*- coding: utf-8 -*-
from app.models import Invoice

def reconcile_gstr2b(client_id, gstr2b_data, db):
    invoices = db.query(Invoice).filter(Invoice.client_id == client_id).all()
    portal_map = {}
    for supplier in gstr2b_data.get("data",{}).get("docdata",{}).get("b2b",[]):
        gstin = supplier.get("ctin","")
        for inv in supplier.get("inv",[]):
            key = f"{gstin}_{inv.get('inum','')}"
            itm = inv.get("itms",[{}])[0].get("itm_det",{})
            portal_map[key] = {"gstin":gstin,"invoice_number":inv.get("inum",""),"taxable_value":inv.get("val",0),"igst":itm.get("iamt",0),"cgst":itm.get("camt",0),"sgst":itm.get("samt",0)}
    books_map = {}
    for inv in invoices:
        if inv.vendor_gstin and inv.invoice_number:
            books_map[f"{inv.vendor_gstin}_{inv.invoice_number}"] = inv
    matched, unmatched_portal, unmatched_books = [], [], []
    for key in set(list(portal_map.keys()) + list(books_map.keys())):
        if key in portal_map and key in books_map:
            p,b = portal_map[key], books_map[key]
            diff = abs((p.get("taxable_value",0) or 0) - (b.taxable_amount or 0))
            matched.append({"invoice_number":b.invoice_number,"vendor_gstin":b.vendor_gstin,"books_amount":b.taxable_amount,"portal_amount":p.get("taxable_value",0),"difference":diff,"status":"matched" if diff < 1 else "amount_mismatch"})
        elif key in portal_map:
            p = portal_map[key]
            unmatched_portal.append({"invoice_number":p.get("invoice_number"),"vendor_gstin":p.get("gstin"),"portal_amount":p.get("taxable_value",0),"status":"missing_in_books"})
        else:
            b = books_map[key]
            unmatched_books.append({"invoice_number":b.invoice_number,"vendor_gstin":b.vendor_gstin,"books_amount":b.taxable_amount,"status":"missing_in_portal"})
    itc = sum((p.get("igst",0) or 0)+(p.get("cgst",0) or 0)+(p.get("sgst",0) or 0) for p in portal_map.values())
    return {"total_portal_invoices":len(portal_map),"total_books_invoices":len(books_map),"matched":len([m for m in matched if m["status"]=="matched"]),"amount_mismatch":len([m for m in matched if m["status"]=="amount_mismatch"]),"missing_in_books":len(unmatched_portal),"missing_in_portal":len(unmatched_books),"total_itc_available":round(itc,2),"matched_records":matched,"unmatched_portal":unmatched_portal,"unmatched_books":unmatched_books}
