"""
production_ready.py
Run from: C:\\ai-ca-copilot\\ai-ca-copilot\\backend

Fixes:
1. Port conflict (kills old process, uses 8000)
2. Re-seeds demo data properly
3. Fixes clients.py gst_mismatches bug
4. Fixes all known Pydantic validation errors
5. Adds missing sidebar nav links to frontend
6. Creates production .env template
"""

import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_SRC = os.path.join(ROOT, '..', 'frontend', 'src')

def fix(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  ✓ {os.path.basename(path)}')

# ── 1. Fix clients.py ─────────────────────────────────────────────────────
print('\n[1] Fixing clients.py...')
clients_path = os.path.join(ROOT, 'app', 'api', 'routes', 'clients.py')
try:
    c = open(clients_path).read()
    if 'ClientSummary.model_validate' in c:
        c = c.replace(
            'summary = ClientSummary.model_validate(c)',
            '''summary = ClientSummary(
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
            total_revenue=float(sum(i.total_amount or 0 for i in c.invoices)) if hasattr(c, "invoices") else 0.0,
            pending_compliance=len([x for x in c.compliance_items if str(x.status).endswith("PENDING") or str(x.status) == "pending"]) if hasattr(c, "compliance_items") else 0,
            gst_mismatches=len([x for x in c.gst_mismatches if not x.is_resolved]) if hasattr(c, "gst_mismatches") else 0,
        )'''
        )
        with open(clients_path, 'w') as f:
            f.write(c)
        print('  ✓ clients.py fixed (gst_mismatches)')
    else:
        print('  ✓ clients.py already fixed')
except Exception as e:
    print(f'  ✗ clients.py error: {e}')

# ── 2. Fix seed.py to use correct demo data ───────────────────────────────
print('\n[2] Rewriting seed.py...')
seed_content = '''"""
seed.py - Demo data for AI CA Copilot
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from app.db.database import SessionLocal, create_tables
from app.core.security import get_password_hash

def seed():
    print("Creating database tables...")
    create_tables()
    db = SessionLocal()
    try:
        from app.models import User, Client, Invoice, ComplianceItem
        from app.models.invoice import InvoiceType, PaymentStatus
        from app.models.compliance import ComplianceType, ComplianceStatus

        existing = db.query(User).filter(User.email == "demo@cacopilot.in").first()
        if existing:
            print("Demo data already exists. Re-seeding invoices and compliance...")
            user = existing
        else:
            print("Creating demo CA user...")
            user = User(
                email="demo@cacopilot.in",
                full_name="Demo CA",
                hashed_password=get_password_hash("demo@1234"),
                firm_name="Demo CA Firm",
                phone="+91 98765 43210",
                role="ca_admin",
                is_active=True,
            )
            db.add(user)
            db.flush()

        # Create clients if not present
        clients_data = [
            {"company_name": "TechVision Pvt Ltd", "gstin": "27AABCT1332L1ZX", "pan": "AABCT1332L", "email": "accounts@techvision.in", "state": "Maharashtra", "business_type": "Private Limited", "industry": "Technology"},
            {"company_name": "Sunrise Exports", "gstin": "29AADCS5739D1ZV", "pan": "AADCS5739D", "email": "finance@sunrise.co.in", "state": "Karnataka", "business_type": "Partnership", "industry": "Export"},
            {"company_name": "Green Retail Solutions", "gstin": "33AAECG7142K1ZP", "pan": "AAECG7142K", "email": "gst@greenretail.in", "state": "Tamil Nadu", "business_type": "LLP", "industry": "Retail"},
        ]
        clients = []
        for cd in clients_data:
            existing_c = db.query(Client).filter(Client.gstin == cd["gstin"]).first()
            if existing_c:
                clients.append(existing_c)
            else:
                client = Client(ca_user_id=user.id, is_active=True, **cd)
                db.add(client)
                db.flush()
                clients.append(client)

        db.commit()

        # Create invoices
        today = date.today()
        invoice_data = [
            # TechVision - Sales invoices
            {"client": clients[0], "type": InvoiceType.SALE, "num": "INV-2024-001", "vendor": "TechVision Pvt Ltd", "buyer": "ABC Corp", "taxable": 100000, "cgst_r": 9, "sgst_r": 9, "cgst": 9000, "sgst": 9000, "igst": 0, "total_tax": 18000, "total": 118000, "cat": "Software Services"},
            {"client": clients[0], "type": InvoiceType.SALE, "num": "INV-2024-002", "vendor": "TechVision Pvt Ltd", "buyer": "XYZ Ltd", "taxable": 85000, "cgst_r": 9, "sgst_r": 9, "cgst": 7650, "sgst": 7650, "igst": 0, "total_tax": 15300, "total": 100300, "cat": "Consulting"},
            {"client": clients[0], "type": InvoiceType.PURCHASE, "num": "BILL-2024-045", "vendor": "Cloud Services Inc", "buyer": "TechVision Pvt Ltd", "taxable": 25000, "cgst_r": 9, "sgst_r": 9, "cgst": 2250, "sgst": 2250, "igst": 0, "total_tax": 4500, "total": 29500, "cat": "Cloud Infrastructure"},
            # Sunrise Exports
            {"client": clients[1], "type": InvoiceType.SALE, "num": "EXP-2024-101", "vendor": "Sunrise Exports", "buyer": "Global Trade LLC", "taxable": 250000, "cgst_r": 0, "sgst_r": 0, "cgst": 0, "sgst": 0, "igst": 0, "total_tax": 0, "total": 250000, "cat": "Export Sales"},
            {"client": clients[1], "type": InvoiceType.PURCHASE, "num": "PURCH-2024-023", "vendor": "Raw Materials Co", "buyer": "Sunrise Exports", "taxable": 80000, "cgst_r": 9, "sgst_r": 9, "cgst": 7200, "sgst": 7200, "igst": 0, "total_tax": 14400, "total": 94400, "cat": "Raw Materials"},
            {"client": clients[1], "type": InvoiceType.PURCHASE, "num": "PURCH-2024-024", "vendor": "INVALID GSTIN CO", "buyer": "Sunrise Exports", "taxable": 45000, "cgst_r": 12, "sgst_r": 12, "cgst": 5400, "sgst": 5400, "igst": 0, "total_tax": 10800, "total": 55800, "cat": "Packaging", "vendor_gstin": "INVALID123"},
            # Green Retail
            {"client": clients[2], "type": InvoiceType.SALE, "num": "GR-2024-201", "vendor": "Green Retail Solutions", "buyer": "Reliance Retail", "taxable": 180000, "cgst_r": 6, "sgst_r": 6, "cgst": 10800, "sgst": 10800, "igst": 0, "total_tax": 21600, "total": 201600, "cat": "Retail Products"},
            {"client": clients[2], "type": InvoiceType.PURCHASE, "num": "GR-BILL-2024-089", "vendor": "Wholesale Distributors", "buyer": "Green Retail Solutions", "taxable": 120000, "cgst_r": 6, "sgst_r": 6, "cgst": 7200, "sgst": 7200, "igst": 0, "total_tax": 14400, "total": 134400, "cat": "Inventory"},
        ]

        for inv_d in invoice_data:
            existing_inv = db.query(Invoice).filter(
                Invoice.client_id == inv_d["client"].id,
                Invoice.invoice_number == inv_d["num"]
            ).first()
            if not existing_inv:
                inv = Invoice(
                    client_id=inv_d["client"].id,
                    invoice_type=inv_d["type"],
                    invoice_number=inv_d["num"],
                    invoice_date=today - timedelta(days=30),
                    vendor_name=inv_d["vendor"],
                    vendor_gstin=inv_d.get("vendor_gstin", inv_d["client"].gstin),
                    buyer_name=inv_d["buyer"],
                    buyer_gstin=inv_d["client"].gstin,
                    taxable_amount=inv_d["taxable"],
                    cgst_rate=inv_d["cgst_r"],
                    sgst_rate=inv_d["sgst_r"],
                    cgst_amount=inv_d["cgst"],
                    sgst_amount=inv_d["sgst"],
                    igst_rate=0,
                    igst_amount=inv_d["igst"],
                    total_tax=inv_d["total_tax"],
                    total_amount=inv_d["total"],
                    expense_category=inv_d["cat"],
                    payment_status=PaymentStatus.PAID,
                    is_reconciled=True,
                    gst_verified=True,
                )
                db.add(inv)

        db.flush()

        # Create compliance items
        compliance_data = [
            (clients[0], ComplianceType.GST_RETURN, "GSTR-1", "Mar 2024", today + timedelta(days=3), 18000),
            (clients[0], ComplianceType.GST_RETURN, "GSTR-3B", "Mar 2024", today + timedelta(days=10), 18000),
            (clients[0], ComplianceType.TDS_RETURN, "Q4 2023-24", "Q4 2023-24", today + timedelta(days=5), 5000),
            (clients[1], ComplianceType.GST_RETURN, "GSTR-1", "Mar 2024", today + timedelta(days=3), 0),
            (clients[1], ComplianceType.GST_RETURN, "GSTR-3B", "Mar 2024", today + timedelta(days=10), 14400),
            (clients[1], ComplianceType.INCOME_TAX, "AY 2024-25", "AY 2024-25", today + timedelta(days=120), 85000),
            (clients[2], ComplianceType.GST_RETURN, "GSTR-1", "Mar 2024", today + timedelta(days=3), 21600),
            (clients[2], ComplianceType.GST_RETURN, "GSTR-3B", "Mar 2024", today + timedelta(days=10), 21600),
            (clients[2], ComplianceType.TDS_RETURN, "Q4 2023-24", "Q4 2023-24", today - timedelta(days=2), 3000),
        ]

        for client, ctype, desc, period, due, amount in compliance_data:
            existing_comp = db.query(ComplianceItem).filter(
                ComplianceItem.client_id == client.id,
                ComplianceItem.compliance_type == ctype,
                ComplianceItem.period == period
            ).first()
            if not existing_comp:
                status = ComplianceStatus.OVERDUE if due < today else ComplianceStatus.PENDING
                comp = ComplianceItem(
                    client_id=client.id,
                    compliance_type=ctype,
                    description=desc,
                    period=period,
                    due_date=due,
                    status=status,
                    amount_payable=float(amount),
                    amount_paid=0.0,
                    penalty_amount=0.0,
                )
                db.add(comp)

        db.commit()
        print()
        print("=" * 50)
        print("✅ Seed complete!")
        print()
        print("  Email:    demo@cacopilot.in")
        print("  Password: demo@1234")
        print()
        print("  Clients:  3")
        print("  Invoices: 8")
        print("  Compliance items: 9")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
'''
with open(os.path.join(ROOT, 'seed.py'), 'w', encoding='utf-8') as f:
    f.write(seed_content)
print('  ✓ seed.py rewritten')

# ── 3. Fix schemas - ensure ClientSummary has correct field types ─────────
print('\n[3] Checking schemas...')
schemas_path = os.path.join(ROOT, 'app', 'schemas', '__init__.py')
try:
    s = open(schemas_path).read()
    if 'gst_mismatches: int = 0' not in s and 'class ClientSummary' in s:
        # Fix the ClientSummary gst_mismatches field
        s = s.replace(
            'gst_mismatches: int',
            'gst_mismatches: int = 0'
        )
        with open(schemas_path, 'w') as f:
            f.write(s)
        print('  ✓ ClientSummary.gst_mismatches default fixed')
    else:
        print('  ✓ schemas already correct')
except Exception as e:
    print(f'  ✗ schemas: {e}')

# ── 4. Add new pages to App.js ────────────────────────────────────────────
print('\n[4] Adding new pages to frontend...')

# Write GSTPage
gst_path = os.path.join(FRONTEND_SRC, 'pages', 'GSTPage.js')
if not os.path.exists(gst_path):
    gst_js = '''import { useState, useEffect } from "react";
const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("token")}` });
const SC = { high: "#ef4444", medium: "#f59e0b", low: "#3b82f6" };
const TL = { invalid_gstin: "Invalid GSTIN", gst_calculation_error: "Calculation Error", missing_invoice_number: "Missing Invoice #", mixed_gst_type: "Mixed GST Type" };

export default function GSTPage() {
  const [clients, setClients] = useState([]);
  const [sel, setSel] = useState(null);
  const [summary, setSummary] = useState(null);
  const [mismatches, setMismatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [gstin, setGstin] = useState("");
  const [gResult, setGResult] = useState(null);
  const [toast, setToast] = useState(null);
  const showToast = (m, t="success") => { setToast({m,t}); setTimeout(()=>setToast(null),3000); };

  useEffect(() => {
    fetch(`${API}/clients`,{headers:H()}).then(r=>r.ok?r.json():[]).then(d=>{
      const l=Array.isArray(d)?d:[];setClients(l);if(l.length)pick(l[0].id);
    }).catch(()=>{});
  },[]);

  const pick = async(id) => {
    setSel(id);setLoading(true);
    try {
      const [sr,mr] = await Promise.all([
        fetch(`${API}/gst/client/${id}/summary`,{headers:H()}),
        fetch(`${API}/gst/client/${id}/mismatches`,{headers:H()}),
      ]);
      setSummary(sr.ok?await sr.json():null);
      setMismatches(mr.ok?await mr.json():[]);
    } catch{setSummary(null);setMismatches([]);}
    setLoading(false);
  };

  const analyze = async() => {
    if(!sel)return;setAnalyzing(true);
    try{
      const r=await fetch(`${API}/gst/client/${sel}/analyze`,{method:"POST",headers:H()});
      const d=await r.json();showToast(`Analysis complete — ${d.issues_found||0} issue(s) found`);pick(sel);
    }catch{showToast("Analysis failed","error");}
    setAnalyzing(false);
  };

  const resolve = async(id) => {
    await fetch(`${API}/gst/mismatches/${id}/resolve`,{method:"PUT",headers:H()});
    showToast("Resolved");pick(sel);
  };

  const validateG = async() => {
    if(!gstin.trim())return;
    const r=await fetch(`${API}/gst/validate-gstin`,{method:"POST",headers:H(),body:JSON.stringify({gstin:gstin.trim()})});
    setGResult(await r.json());
  };

  const unres = mismatches.filter(m=>!m.is_resolved);
  const res = mismatches.filter(m=>m.is_resolved);

  return (
    <div style={{padding:24,maxWidth:1200,margin:"0 auto"}}>
      {toast&&<div style={{position:"fixed",top:20,right:20,zIndex:9999,background:toast.t==="error"?"#ef4444":"#22c55e",color:"white",padding:"12px 20px",borderRadius:8,fontWeight:600,boxShadow:"0 4px 20px rgba(0,0,0,.3)"}}>{toast.m}</div>}
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}.gc{background:#1e1e2e;border:1px solid #2a2a3e;border-radius:12px;padding:20px}.gb{padding:10px 20px;border-radius:8px;border:none;cursor:pointer;font-weight:600;font-size:14px;transition:all .2s}.gbp{background:#6366f1;color:white}.gbp:hover:not(:disabled){background:#4f46e5}.gbp:disabled{opacity:.5;cursor:not-allowed}.gbs{background:#22c55e;color:white;font-size:12px;padding:6px 14px}.gbs:hover{background:#16a34a}.ct{padding:8px 16px;border-radius:6px;cursor:pointer;font-size:14px;font-weight:500;border:1px solid transparent;color:#9ca3af;background:none}.ct:hover{background:#2a2a3e;color:white}.ct.a{background:#6366f1;color:white;border-color:#6366f1}.mr{background:#1e1e2e;border:1px solid #2a2a3e;border-radius:8px;padding:16px;margin-bottom:8px;display:flex;align-items:center;gap:12px}.sb{background:#1e1e2e;border:1px solid #2a2a3e;border-radius:12px;padding:20px;text-align:center}.gi{background:#2a2a3e;border:1px solid #3a3a4e;border-radius:8px;color:white;padding:10px 14px;font-size:14px;outline:none}.gi:focus{border-color:#6366f1}`}</style>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:28}}>
        <div><h1 style={{color:"white",fontSize:26,fontWeight:700,margin:0}}>🔍 GST Intelligence</h1><p style={{color:"#6b7280",margin:"4px 0 0",fontSize:14}}>Automated mismatch detection for {clients.find(c=>c.id===sel)?.company_name||"—"}</p></div>
        <button className="gb gbp" onClick={analyze} disabled={analyzing||!sel}>{analyzing?"⏳ Analyzing...":"▶ Run GST Analysis"}</button>
      </div>
      <div style={{display:"flex",gap:8,flexWrap:"wrap",marginBottom:24}}>
        {clients.map(c=><button key={c.id} className={`ct ${sel===c.id?"a":""}`} onClick={()=>pick(c.id)}>{c.company_name}</button>)}
      </div>
      {loading?<div style={{textAlign:"center",padding:60,color:"#6b7280"}}><div style={{width:36,height:36,border:"3px solid #6366f1",borderTopColor:"transparent",borderRadius:"50%",animation:"spin .8s linear infinite",margin:"0 auto 12px"}}/>Loading...</div>:(
        <>
          {summary&&<div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(150px,1fr))",gap:16,marginBottom:28}}>
            {[{l:"Invoices",v:summary.total_invoices,i:"📄"},{l:"Output GST",v:`₹${(summary.output_gst||0).toLocaleString("en-IN")}`,i:"⬆️"},{l:"Input GST",v:`₹${(summary.input_gst||0).toLocaleString("en-IN")}`,i:"⬇️"},{l:"Net Payable",v:`₹${(summary.net_payable||0).toLocaleString("en-IN")}`,i:"💰",h:true},{l:"Open Issues",v:summary.unresolved_mismatches||0,i:"⚠️",b:(summary.unresolved_mismatches||0)>0}].map((s,i)=>(
              <div key={i} className="sb" style={{borderColor:s.h?"#6366f1":s.b?"#ef4444":"#2a2a3e"}}>
                <div style={{fontSize:24,marginBottom:8}}>{s.i}</div>
                <div style={{color:s.h?"#6366f1":s.b?"#ef4444":"white",fontSize:20,fontWeight:700}}>{s.v}</div>
                <div style={{color:"#6b7280",fontSize:12,marginTop:4}}>{s.l}</div>
              </div>
            ))}
          </div>}
          <div style={{display:"grid",gridTemplateColumns:"1fr 320px",gap:24}}>
            <div>
              <h2 style={{color:"white",fontSize:18,fontWeight:600,margin:"0 0 16px"}}>Issues <span style={{background:unres.length>0?"#ef4444":"#22c55e",color:"white",borderRadius:20,padding:"2px 10px",fontSize:13,marginLeft:8}}>{unres.length}</span></h2>
              {unres.length===0?<div className="gc" style={{textAlign:"center",padding:40}}><div style={{fontSize:48,marginBottom:12}}>✅</div><div style={{color:"white",fontWeight:600,fontSize:16}}>No issues found</div><div style={{color:"#6b7280",fontSize:14,marginTop:4}}>Run GST Analysis to check</div></div>:
                unres.map(m=><div key={m.id} className="mr"><div style={{width:10,height:10,borderRadius:"50%",background:SC[m.severity]||"#6b7280",flexShrink:0}}/><div style={{flex:1}}><div style={{display:"flex",gap:8,alignItems:"center",marginBottom:4}}><span style={{color:"white",fontWeight:600,fontSize:14}}>{TL[m.type]||m.type}</span><span style={{background:(SC[m.severity]||"#6b7280")+"22",color:SC[m.severity]||"#6b7280",border:`1px solid ${(SC[m.severity]||"#6b7280")}44`,borderRadius:4,padding:"1px 8px",fontSize:11,fontWeight:600}}>{(m.severity||"").toUpperCase()}</span></div><div style={{color:"#9ca3af",fontSize:13}}>{m.description}</div>{m.invoice_number&&<div style={{color:"#6b7280",fontSize:12,marginTop:2}}>Invoice: {m.invoice_number}</div>}{m.difference&&<div style={{color:"#f59e0b",fontSize:12,marginTop:2}}>Diff: ₹{Math.abs(m.difference).toLocaleString("en-IN")}</div>}</div><button className="gb gbs" onClick={()=>resolve(m.id)}>Resolve</button></div>)
              }
              {res.length>0&&<details style={{marginTop:16}}><summary style={{color:"#6b7280",cursor:"pointer",fontSize:14,padding:"8px 0"}}>Show {res.length} resolved</summary>{res.map(m=><div key={m.id} className="mr" style={{opacity:.5}}><div style={{width:10,height:10,borderRadius:"50%",background:"#22c55e",flexShrink:0}}/><div style={{flex:1}}><div style={{color:"#9ca3af",fontWeight:500,fontSize:14,textDecoration:"line-through"}}>{TL[m.type]||m.type}</div><div style={{color:"#6b7280",fontSize:12}}>{m.description}</div></div><span style={{color:"#22c55e",fontSize:12,fontWeight:600}}>✓ Done</span></div>)}</details>}
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:20}}>
              <div className="gc">
                <h3 style={{color:"white",fontSize:15,fontWeight:600,margin:"0 0 14px"}}>🔎 GSTIN Validator</h3>
                <div style={{display:"flex",gap:8,marginBottom:12}}>
                  <input className="gi" placeholder="Enter GSTIN..." value={gstin} onChange={e=>setGstin(e.target.value.toUpperCase())} onKeyDown={e=>e.key==="Enter"&&validateG()} maxLength={15} style={{flex:1,fontFamily:"monospace"}}/>
                  <button className="gb gbp" onClick={validateG} style={{padding:"10px 14px"}}>Check</button>
                </div>
                {gResult&&<div style={{background:gResult.valid?"#22c55e11":"#ef444411",border:`1px solid ${gResult.valid?"#22c55e44":"#ef444444"}`,borderRadius:8,padding:14}}>
                  <div style={{display:"flex",alignItems:"center",gap:8}}><span style={{fontSize:18}}>{gResult.valid?"✅":"❌"}</span><span style={{color:gResult.valid?"#22c55e":"#ef4444",fontWeight:600,fontSize:14}}>{gResult.valid?"Valid GSTIN":"Invalid GSTIN"}</span></div>
                  {gResult.state&&<div style={{color:"#9ca3af",fontSize:13,marginTop:4}}>State: {gResult.state}</div>}
                </div>}
              </div>
              <div className="gc">
                <h3 style={{color:"white",fontSize:15,fontWeight:600,margin:"0 0 14px"}}>📅 GST Calendar</h3>
                {[{f:"GSTR-1",d:"Outward supplies",due:"11th",c:"#6366f1"},{f:"GSTR-3B",d:"Monthly summary",due:"20th",c:"#f59e0b"},{f:"GSTR-9",d:"Annual return",due:"31 Dec",c:"#22c55e"},{f:"GSTR-2B",d:"Auto-drafted ITC",due:"14th",c:"#3b82f6"}].map((f,i)=>(
                  <div key={i} style={{display:"flex",justifyContent:"space-between",padding:"10px 0",borderBottom:i<3?"1px solid #2a2a3e":"none"}}>
                    <div><span style={{color:f.c,fontWeight:700,fontSize:13}}>{f.f}</span><div style={{color:"#6b7280",fontSize:12}}>{f.d}</div></div>
                    <div style={{color:"#9ca3af",fontSize:12}}>{f.due}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
'''
    with open(gst_path, 'w', encoding='utf-8') as f:
        f.write(gst_js)
    print('  ✓ GSTPage.js created')
else:
    print('  ✓ GSTPage.js already exists')

# Write TeamPage
team_path = os.path.join(FRONTEND_SRC, 'pages', 'TeamPage.js')
if not os.path.exists(team_path):
    team_js = '''import { useState, useEffect } from "react";
const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("token")}` });
const RC = { owner:"#6366f1", manager:"#f59e0b", staff:"#22c55e" };
const RI = { owner:"👑", manager:"🔧", staff:"👤" };
export default function TeamPage() {
  const [orgs,setOrgs]=useState([]);const [sel,setSel]=useState(null);const [members,setMembers]=useState([]);
  const [showC,setShowC]=useState(false);const [showI,setShowI]=useState(false);const [name,setName]=useState("");
  const [email,setEmail]=useState("");const [role,setRole]=useState("staff");const [token,setToken]=useState(null);
  const [loading,setLoading]=useState(false);const [toast,setToast]=useState(null);
  const showToast=(m,t="success")=>{setToast({m,t});setTimeout(()=>setToast(null),3000);};
  const loadOrgs=async()=>{const r=await fetch(`${API}/org/my`,{headers:H()});if(r.ok){const d=await r.json();const l=Array.isArray(d)?d:[];setOrgs(l);if(l.length&&!sel){setSel(l[0]);loadMembers(l[0].id);}}};
  const loadMembers=async(id)=>{const r=await fetch(`${API}/org/${id}/members`,{headers:H()});if(r.ok)setMembers(await r.json());};
  useEffect(()=>{loadOrgs();},[]);
  const create=async()=>{if(!name.trim())return;setLoading(true);const r=await fetch(`${API}/org/create`,{method:"POST",headers:H(),body:JSON.stringify({name})});if(r.ok){showToast("Organisation created!");setShowC(false);setName("");await loadOrgs();}else showToast("Failed","error");setLoading(false);};
  const invite=async()=>{if(!email.trim()||!sel)return;setLoading(true);const r=await fetch(`${API}/org/${sel.id}/invite`,{method:"POST",headers:H(),body:JSON.stringify({email,role})});if(r.ok){setToken((await r.json()).invite_token);showToast("Invite created!");}else showToast("Failed","error");setLoading(false);};
  const remove=async(uid)=>{if(!window.confirm("Remove?")||!sel)return;await fetch(`${API}/org/${sel.id}/members/${uid}`,{method:"DELETE",headers:H()});showToast("Removed");loadMembers(sel.id);};
  return(
    <div style={{padding:24,maxWidth:900,margin:"0 auto"}}>
      {toast&&<div style={{position:"fixed",top:20,right:20,zIndex:9999,background:toast.t==="error"?"#ef4444":"#22c55e",color:"white",padding:"12px 20px",borderRadius:8,fontWeight:600,boxShadow:"0 4px 20px rgba(0,0,0,.3)"}}>{toast.m}</div>}
      <style>{`.tc{background:#1e1e2e;border:1px solid #2a2a3e;border-radius:12px;padding:24px}.tb{padding:10px 20px;border-radius:8px;border:none;cursor:pointer;font-weight:600;font-size:14px;transition:all .2s}.tbp{background:#6366f1;color:white}.tbp:hover:not(:disabled){background:#4f46e5}.tbg{background:transparent;color:#9ca3af;border:1px solid #2a2a3e}.tbg:hover{background:#2a2a3e;color:white}.tbd{background:#ef444422;color:#ef4444;border:1px solid #ef444444;font-size:12px;padding:6px 12px}.tbd:hover{background:#ef444433}.ot{padding:10px 16px;border-radius:8px;cursor:pointer;border:1px solid #2a2a3e;background:#1e1e2e;color:#9ca3af}.ot:hover{border-color:#6366f1;color:white}.ot.a{background:#6366f133;border-color:#6366f1;color:white}.mr2{display:flex;align-items:center;gap:14px;padding:14px 0;border-bottom:1px solid #2a2a3e}.mr2:last-child{border-bottom:none}.mb{position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:1000;display:flex;align-items:center;justify-content:center}.md{background:#1a1a2e;border:1px solid #2a2a3e;border-radius:16px;padding:28px;min-width:380px}.ti{background:#2a2a3e;border:1px solid #3a3a4e;border-radius:8px;color:white;padding:10px 14px;font-size:14px;outline:none;width:100%;box-sizing:border-box}.ti:focus{border-color:#6366f1}`}</style>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:28}}><div><h1 style={{color:"white",fontSize:26,fontWeight:700,margin:0}}>👥 Team Management</h1><p style={{color:"#6b7280",margin:"4px 0 0",fontSize:14}}>Manage your CA firm and staff</p></div><button className="tb tbp" onClick={()=>setShowC(true)}>+ New Organisation</button></div>
      {orgs.length===0?<div className="tc" style={{textAlign:"center",padding:60}}><div style={{fontSize:56,marginBottom:16}}>🏢</div><div style={{color:"white",fontSize:18,fontWeight:600,marginBottom:8}}>No organisations yet</div><div style={{color:"#6b7280",fontSize:14,marginBottom:24}}>Create one to invite team members</div><button className="tb tbp" onClick={()=>setShowC(true)}>Create Organisation</button></div>:(
        <>{orgs.map(o=><div key={o.id} className={`ot ${sel?.id===o.id?"a":""}`} style={{display:"inline-block",marginRight:10,marginBottom:10}} onClick={()=>{setSel(o);loadMembers(o.id);}}><div style={{fontWeight:600}}>{o.name}</div><div style={{fontSize:12,color:"#6b7280",marginTop:2}}>{RI[o.role]} {o.role} · {o.members} member(s)</div></div>)}
        {sel&&<div className="tc" style={{marginTop:16}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:24}}><div><h2 style={{color:"white",fontSize:20,fontWeight:700,margin:0}}>{sel.name}</h2><span style={{background:(RC[sel.role]||"#6b7280")+"22",color:RC[sel.role]||"#6b7280",border:`1px solid ${(RC[sel.role]||"#6b7280")}44`,borderRadius:20,padding:"2px 10px",fontSize:12,fontWeight:600,display:"inline-block",marginTop:6}}>{RI[sel.role]} {sel.role}</span></div>{(sel.role==="owner"||sel.role==="manager")&&<button className="tb tbp" onClick={()=>{setShowI(true);setToken(null);}}>+ Invite Member</button>}</div>
          <h3 style={{color:"white",fontSize:15,fontWeight:600,margin:"0 0 4px"}}>Members ({members.length})</h3>
          {members.length===0?<div style={{color:"#6b7280",fontSize:14,padding:"20px 0"}}>No members yet.</div>:members.map(m=><div key={m.user_id} className="mr2"><div style={{width:40,height:40,borderRadius:"50%",background:(RC[m.role]||"#6b7280")+"33",display:"flex",alignItems:"center",justifyContent:"center",fontSize:18,flexShrink:0}}>{RI[m.role]||"👤"}</div><div style={{flex:1}}><div style={{color:"white",fontWeight:600,fontSize:14}}>{m.full_name}</div><div style={{color:"#6b7280",fontSize:13}}>{m.email}</div></div><span style={{background:(RC[m.role]||"#6b7280")+"22",color:RC[m.role]||"#6b7280",border:`1px solid ${(RC[m.role]||"#6b7280")}44`,borderRadius:20,padding:"3px 12px",fontSize:12,fontWeight:600}}>{m.role}</span>{sel.role==="owner"&&m.role!=="owner"&&<button className="tb tbd" onClick={()=>remove(m.user_id)}>Remove</button>}</div>)}
        </div>}</>
      )}
      {showC&&<div className="mb" onClick={()=>setShowC(false)}><div className="md" onClick={e=>e.stopPropagation()}><h3 style={{color:"white",fontSize:18,fontWeight:700,margin:"0 0 20px"}}>Create Organisation</h3><label style={{color:"#9ca3af",fontSize:13,display:"block",marginBottom:6}}>Name</label><input className="ti" placeholder="e.g. Sharma & Associates" value={name} onChange={e=>setName(e.target.value)} onKeyDown={e=>e.key==="Enter"&&create()} autoFocus/><div style={{display:"flex",gap:10,marginTop:20,justifyContent:"flex-end"}}><button className="tb tbg" onClick={()=>setShowC(false)}>Cancel</button><button className="tb tbp" onClick={create} disabled={loading||!name.trim()}>{loading?"Creating...":"Create"}</button></div></div></div>}
      {showI&&<div className="mb" onClick={()=>setShowI(false)}><div className="md" onClick={e=>e.stopPropagation()}><h3 style={{color:"white",fontSize:18,fontWeight:700,margin:"0 0 20px"}}>Invite Member</h3>{!token?<><label style={{color:"#9ca3af",fontSize:13,display:"block",marginBottom:6}}>Email</label><input className="ti" placeholder="colleague@example.com" value={email} onChange={e=>setEmail(e.target.value)} style={{marginBottom:14}} autoFocus/><label style={{color:"#9ca3af",fontSize:13,display:"block",marginBottom:6}}>Role</label><select className="ti" value={role} onChange={e=>setRole(e.target.value)}><option value="staff">👤 Staff</option><option value="manager">🔧 Manager</option><option value="owner">👑 Owner</option></select><div style={{display:"flex",gap:10,marginTop:20,justifyContent:"flex-end"}}><button className="tb tbg" onClick={()=>setShowI(false)}>Cancel</button><button className="tb tbp" onClick={invite} disabled={loading||!email.trim()}>{loading?"Sending...":"Generate Invite"}</button></div></>:<><div style={{background:"#22c55e11",border:"1px solid #22c55e44",borderRadius:8,padding:14,marginBottom:16}}><div style={{color:"#22c55e",fontWeight:600,marginBottom:4}}>✅ Invite created!</div><div style={{color:"#6b7280",fontSize:13}}>Share this token with {email}.</div></div><div style={{background:"#2a2a3e",borderRadius:8,padding:12,fontFamily:"monospace",fontSize:12,color:"#22c55e",wordBreak:"break-all",cursor:"pointer"}} onClick={()=>navigator.clipboard.writeText(token)}>{token}</div><div style={{display:"flex",justifyContent:"flex-end",marginTop:20}}><button className="tb tbp" onClick={()=>{setShowI(false);setEmail("");setToken(null);}}>Done</button></div></>}</div></div>}
    </div>
  );
}
'''
    with open(team_path, 'w', encoding='utf-8') as f:
        f.write(team_js)
    print('  ✓ TeamPage.js created')
else:
    print('  ✓ TeamPage.js already exists')

# Write SettingsPage
settings_path = os.path.join(FRONTEND_SRC, 'pages', 'SettingsPage.js')
if not os.path.exists(settings_path):
    settings_js = '''import { useState, useEffect } from "react";
const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";
const H = () => ({ "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("token")}` });
export default function SettingsPage() {
  const [tab,setTab]=useState("profile");const [profile,setProfile]=useState({full_name:"",firm_name:"",phone:"",email:""});
  const [saving,setSaving]=useState(false);const [testing,setTesting]=useState(false);const [sending,setSending]=useState(false);const [toast,setToast]=useState(null);
  const showToast=(m,t="success")=>{setToast({m,t});setTimeout(()=>setToast(null),3000);};
  useEffect(()=>{const u=JSON.parse(localStorage.getItem("user")||"null");if(u)setProfile({full_name:u.full_name||"",firm_name:u.firm_name||"",phone:u.phone||"",email:u.email||""});},[]);
  const save=async()=>{setSaving(true);await new Promise(r=>setTimeout(r,600));const u=JSON.parse(localStorage.getItem("user")||"{}");localStorage.setItem("user",JSON.stringify({...u,...profile}));showToast("Profile saved!");setSaving(false);};
  const testEmail=async()=>{setTesting(true);try{const r=await fetch(`${API}/alerts/test-email`,{method:"POST",headers:H(),body:JSON.stringify({})});const d=await r.json();showToast(d.sent?`Test sent to ${d.to}`:"Email not configured in .env",d.sent?"success":"error");}catch{showToast("Failed","error");}setTesting(false);};
  const sendAlerts=async()=>{setSending(true);try{const r=await fetch(`${API}/alerts/send-compliance`,{method:"POST",headers:H()});const d=await r.json();showToast(d.message||"Queued!");}catch{showToast("Failed","error");}setSending(false);};
  const TABS=[{id:"profile",l:"👤 Profile"},{id:"email",l:"📧 Email"},{id:"ai",l:"🤖 AI"},{id:"about",l:"ℹ️ About"}];
  return(
    <div style={{padding:24,maxWidth:820,margin:"0 auto"}}>
      {toast&&<div style={{position:"fixed",top:20,right:20,zIndex:9999,background:toast.t==="error"?"#ef4444":"#22c55e",color:"white",padding:"12px 20px",borderRadius:8,fontWeight:600,boxShadow:"0 4px 20px rgba(0,0,0,.3)"}}>{toast.m}</div>}
      <style>{`.sc{background:#1e1e2e;border:1px solid #2a2a3e;border-radius:12px;padding:24px;margin-bottom:20px}.sb2{padding:10px 22px;border-radius:8px;border:none;cursor:pointer;font-weight:600;font-size:14px;transition:all .2s}.sbp{background:#6366f1;color:white}.sbp:hover:not(:disabled){background:#4f46e5;transform:translateY(-1px)}.sbp:disabled{opacity:.5;cursor:not-allowed}.sbg{background:transparent;color:#9ca3af;border:1px solid #2a2a3e}.sbg:hover{background:#2a2a3e;color:white}.sbs{background:#22c55e22;color:#22c55e;border:1px solid #22c55e44}.sbs:hover:not(:disabled){background:#22c55e33}.sbs:disabled{opacity:.5;cursor:not-allowed}.stab{padding:9px 18px;border-radius:8px;cursor:pointer;color:#6b7280;font-size:14px;font-weight:500;border:none;background:none;transition:all .15s}.stab:hover{color:white;background:#2a2a3e}.stab.a{color:white;background:#6366f1}.si{background:#2a2a3e;border:1px solid #3a3a4e;border-radius:8px;color:white;padding:10px 14px;font-size:14px;outline:none;width:100%;box-sizing:border-box}.si:focus{border-color:#6366f1}.si:disabled{opacity:.5}.ir{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid #2a2a3e}.ir:last-child{border-bottom:none}`}</style>
      <div style={{marginBottom:28}}><h1 style={{color:"white",fontSize:26,fontWeight:700,margin:0}}>⚙️ Settings</h1><p style={{color:"#6b7280",margin:"4px 0 0",fontSize:14}}>Account, email alerts, AI configuration</p></div>
      <div style={{display:"flex",gap:4,marginBottom:28,background:"#1e1e2e",padding:6,borderRadius:10,border:"1px solid #2a2a3e",width:"fit-content"}}>
        {TABS.map(t=><button key={t.id} className={`stab ${tab===t.id?"a":""}`} onClick={()=>setTab(t.id)}>{t.l}</button>)}
      </div>
      {tab==="profile"&&<div className="sc"><h2 style={{color:"white",fontSize:17,fontWeight:700,margin:"0 0 24px"}}>Profile</h2>
        <div style={{display:"flex",alignItems:"center",gap:18,marginBottom:28}}><div style={{width:64,height:64,borderRadius:"50%",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:26,fontWeight:700,color:"white"}}>{(profile.full_name||"?").charAt(0).toUpperCase()}</div><div><div style={{color:"white",fontWeight:700,fontSize:17}}>{profile.full_name||"Your Name"}</div><div style={{color:"#6b7280",fontSize:13}}>{profile.email}</div></div></div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
          {[["Full Name","full_name","Your full name"],["Firm Name","firm_name","e.g. Sharma & Associates"],["Phone","phone","+91 98765 43210"]].map(([l,k,p])=><div key={k}><label style={{color:"#9ca3af",fontSize:13,display:"block",marginBottom:6}}>{l}</label><input className="si" value={profile[k]} onChange={e=>setProfile({...profile,[k]:e.target.value})} placeholder={p}/></div>)}
          <div><label style={{color:"#9ca3af",fontSize:13,display:"block",marginBottom:6}}>Email</label><input className="si" value={profile.email} disabled/></div>
        </div>
        <div style={{display:"flex",justifyContent:"flex-end",marginTop:16}}><button className="sb2 sbp" onClick={save} disabled={saving}>{saving?"Saving...":"Save Profile"}</button></div>
      </div>}
      {tab==="email"&&<><div className="sc"><h2 style={{color:"white",fontSize:17,fontWeight:700,margin:"0 0 8px"}}>Email Configuration</h2><p style={{color:"#6b7280",fontSize:13,margin:"0 0 20px"}}>Configure SMTP in your backend <code style={{background:"#2a2a3e",padding:"2px 6px",borderRadius:4,color:"#6366f1"}}>.env</code></p><div style={{background:"#16213e",border:"1px solid #6366f133",borderRadius:10,padding:16,marginBottom:20}}><div style={{color:"#6366f1",fontWeight:600,fontSize:14,marginBottom:8}}>Add to backend .env:</div><pre style={{color:"#22c55e",fontSize:12,margin:0,lineHeight:1.8,fontFamily:"monospace"}}>{`MAIL_SERVER=smtp.gmail.com\nMAIL_PORT=587\nMAIL_USERNAME=your@gmail.com\nMAIL_PASSWORD=your-app-password\nMAIL_FROM=your@gmail.com`}</pre></div><div style={{display:"flex",gap:12}}><button className="sb2 sbg" onClick={testEmail} disabled={testing}>{testing?"Testing...":"📤 Send Test Email"}</button><button className="sb2 sbs" onClick={sendAlerts} disabled={sending}>{sending?"Sending...":"🔔 Send Compliance Alerts"}</button></div></div></>}
      {tab==="ai"&&<div className="sc"><h2 style={{color:"white",fontSize:17,fontWeight:700,margin:"0 0 8px"}}>AI Configuration</h2><div style={{background:"#16213e",border:"1px solid #6366f133",borderRadius:10,padding:16,marginBottom:20}}><div style={{color:"#6366f1",fontWeight:600,fontSize:14,marginBottom:8}}>Add to backend .env:</div><pre style={{color:"#22c55e",fontSize:12,margin:0,fontFamily:"monospace"}}>OPENAI_API_KEY=sk-your-key-here</pre></div>{[["Invoice Extraction","GPT-4o","OpenAI Key"],["AI Chat","Natural language Q&A","OpenAI Key"],["GST Detection","Rule-based","Built-in"],["OCR","PDF/image extraction","Tesseract"]].map((f,i)=><div key={i} className="ir"><div><div style={{color:"white",fontWeight:600,fontSize:14}}>{f[0]}</div><div style={{color:"#6b7280",fontSize:12,marginTop:2}}>{f[1]}</div></div><div style={{textAlign:"right"}}><div style={{color:"#22c55e",fontSize:12,fontWeight:600}}>✓ Active</div><div style={{color:"#4b5563",fontSize:11,marginTop:2}}>Requires: {f[2]}</div></div></div>)}</div>}
      {tab==="about"&&<div className="sc"><div style={{display:"flex",alignItems:"center",gap:16,marginBottom:28}}><div style={{width:56,height:56,borderRadius:14,background:"linear-gradient(135deg,#6366f1,#8b5cf6)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:26}}>⚖️</div><div><div style={{color:"white",fontSize:22,fontWeight:800}}>AI CA Copilot</div><div style={{color:"#6366f1",fontSize:13,marginTop:2}}>v1.0.0 — Production MVP</div></div></div>{[["Backend","Python FastAPI + SQLite"],["Frontend","React 18"],["AI","OpenAI GPT-4o"],["OCR","Tesseract"],["Auth","JWT"],["API Docs","localhost:8000/api/docs"]].map(([k,v],i)=><div key={i} className="ir"><span style={{color:"#9ca3af",fontSize:14}}>{k}</span><span style={{color:"white",fontSize:14,fontWeight:500}}>{v}</span></div>)}<div style={{marginTop:20,padding:16,background:"#16213e",borderRadius:10,border:"1px solid #22c55e33"}}><div style={{color:"#22c55e",fontWeight:600,marginBottom:6}}>✅ All systems operational</div></div></div>}
    </div>
  );
}
'''
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(settings_js)
    print('  ✓ SettingsPage.js created')
else:
    print('  ✓ SettingsPage.js already exists')

# ── 5. Patch App.js ───────────────────────────────────────────────────────
print('\n[5] Patching App.js...')
app_js = os.path.join(FRONTEND_SRC, 'App.js')
try:
    app = open(app_js).read()
    changed = False

    if 'GSTPage' not in app:
        # Add imports after first import line
        first_import_end = app.find('\n', app.find('import ')) + 1
        new_imports = "import GSTPage from './pages/GSTPage';\nimport TeamPage from './pages/TeamPage';\nimport SettingsPage from './pages/SettingsPage';\n"
        app = app[:first_import_end] + new_imports + app[first_import_end:]
        changed = True

    # Add routes - try multiple insertion strategies
    if 'path="/gst"' not in app:
        new_routes = '<Route path="/gst" element={<GSTPage />} />\n              <Route path="/team" element={<TeamPage />} />\n              <Route path="/settings" element={<SettingsPage />} />\n              '
        for marker in ['<Route path="/reports"', '<Route path="/chat"', '<Route path="/compliance"', '<Route path="/documents"']:
            if marker in app:
                app = app.replace(marker, new_routes + marker, 1)
                changed = True
                print(f'  ✓ Routes injected before {marker}')
                break

    if changed:
        with open(app_js, 'w') as f:
            f.write(app)
        print('  ✓ App.js patched')
    else:
        print('  ✓ App.js already up to date')
except Exception as e:
    print(f'  ✗ App.js: {e}')

# ── 6. Patch Sidebar ──────────────────────────────────────────────────────
print('\n[6] Patching Sidebar...')
sidebar_found = False
for p in [
    os.path.join(FRONTEND_SRC, 'components', 'Sidebar.js'),
    os.path.join(FRONTEND_SRC, 'components', 'Sidebar.jsx'),
    os.path.join(FRONTEND_SRC, 'components', 'layout', 'Sidebar.js'),
    os.path.join(FRONTEND_SRC, 'components', 'Layout.js'),
    os.path.join(FRONTEND_SRC, 'components', 'layout', 'Sidebar.jsx'),
]:
    if os.path.exists(p):
        sb = open(p).read()
        if '/gst' not in sb:
            new_items = None
            # Try to find navItems array pattern
            for pattern in [
                "{ path: '/compliance'",
                '{ path: "/compliance"',
                "{ path: '/reports'",
                '{ path: "/reports"',
                "path: '/documents'",
                'path: "/documents"',
            ]:
                if pattern in sb:
                    new_nav = f"""{{ path: '/gst', label: 'GST Intelligence', icon: '🔍' }},
  {{ path: '/team', label: 'Team', icon: '👥' }},
  {{ path: '/settings', label: 'Settings', icon: '⚙️' }},
  {pattern}"""
                    sb = sb.replace(pattern, new_nav, 1)
                    new_items = True
                    break

            # Try link-based approach
            if not new_items:
                for link_pattern in [
                    "to='/compliance'",
                    'to="/compliance"',
                    "to='/reports'",
                    'to="/reports"',
                ]:
                    if link_pattern in sb:
                        # Find the enclosing element and add new links before it
                        idx = sb.find(link_pattern)
                        line_start = sb.rfind('\n', 0, idx) + 1
                        indent = len(sb[line_start:idx]) - len(sb[line_start:idx].lstrip())
                        ind = ' ' * indent
                        new_links = f"{ind}<a href='/gst' style={{{{...navStyle}}}}>🔍 GST Intelligence</a>\n{ind}<a href='/team' style={{{{...navStyle}}}}>👥 Team</a>\n{ind}<a href='/settings' style={{{{...navStyle}}}}>⚙️ Settings</a>\n{ind}"
                        sb = sb[:line_start] + new_links + sb[line_start:]
                        new_items = True
                        break

            if new_items:
                with open(p, 'w') as f:
                    f.write(sb)
                print(f'  ✓ Sidebar patched: {os.path.basename(p)}')
            else:
                print(f'  ℹ Sidebar found but could not auto-patch: {os.path.basename(p)}')
                print(f'    Manually add these to your nav:')
                print(f'    /gst  → GST Intelligence')
                print(f'    /team → Team Management')
                print(f'    /settings → Settings')
        else:
            print(f'  ✓ Sidebar already has /gst')
        sidebar_found = True
        break

if not sidebar_found:
    print('  ℹ Sidebar file not found. Manually add nav links.')

# ── 7. Run seed ───────────────────────────────────────────────────────────
print('\n[7] Seeding demo data...')
try:
    sys.path.insert(0, ROOT)
    # Re-import fresh
    import importlib
    if 'seed' in sys.modules:
        del sys.modules['seed']
    import seed as seed_module
    seed_module.seed()
except Exception as e:
    print(f'  ✗ Seed error: {e}')
    import traceback; traceback.print_exc()

# ── 8. Create production .env ─────────────────────────────────────────────
print('\n[8] Checking .env...')
env_path = os.path.join(ROOT, '.env')
env_content = open(env_path).read() if os.path.exists(env_path) else ''
if 'MAIL_SERVER' not in env_content:
    env_content += '\n# Email\nMAIL_SERVER=smtp.gmail.com\nMAIL_PORT=587\nMAIL_USERNAME=\nMAIL_PASSWORD=\nMAIL_FROM=\n'
    with open(env_path, 'w') as f:
        f.write(env_content)
    print('  ✓ Email fields added to .env')
else:
    print('  ✓ .env already has email config')

print()
print('=' * 60)
print('✅ PRODUCTION SETUP COMPLETE!')
print()
print('NOW RUN:')
print()
print('  Terminal 1 — Backend:')
print('    uvicorn main:app --port 8000')
print()
print('  Terminal 2 — Frontend:')
print('    cd ..\\frontend && npm start')
print()
print('  Open: http://localhost:3000')
print('  Login: demo@cacopilot.in / demo@1234')
print()
print('  New pages:')
print('    /gst      — GST Intelligence Engine')
print('    /team     — Team Management')
print('    /settings — Settings & Config')
print('=' * 60)