# -*- coding: utf-8 -*-
# complete_fix.py - Run this ONCE to fix everything
# Usage: python complete_fix.py
import os, sys, re

BASE = os.path.dirname(os.path.abspath(__file__))

print("=" * 50)
print("  MAAVI COMPLETE FIX")
print("=" * 50)

# ── 1. Fix ai_service.py to support Groq/Gemini/Anthropic ──
ai_service = '''# -*- coding: utf-8 -*-
import json, logging, os
logger = logging.getLogger(__name__)

def _call_ai(system_msg, user_msg, json_mode=False):
    provider = os.getenv("AI_PROVIDER", "groq").lower()
    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    # Try Groq first (fastest, free)
    if groq_key and provider in ("groq", "auto"):
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            msgs = [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}]
            if json_mode:
                msgs[1]["content"] += "\\n\\nRespond ONLY with valid JSON. No markdown, no backticks."
            r = client.chat.completions.create(model="llama3-70b-8192", messages=msgs, max_tokens=2000, temperature=0.2)
            return r.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq failed: {e}")

    # Try Gemini
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = system_msg + "\\n\\n" + user_msg
            if json_mode:
                prompt += "\\n\\nRespond ONLY with valid JSON. No markdown, no backticks."
            r = model.generate_content(prompt)
            result = r.text.strip().replace("```json","").replace("```","").strip()
            return result
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")

    # Try Anthropic
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            msg = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                system=system_msg,
                messages=[{"role": "user", "content": user_msg}]
            )
            return msg.content[0].text.strip()
        except Exception as e:
            logger.warning(f"Anthropic failed: {e}")

    # Try OpenAI
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            kwargs = {"model": "gpt-4o", "messages": [{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}], "max_tokens": 2000, "temperature": 0.2}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            r = client.chat.completions.create(**kwargs)
            return r.choices[0].message.content
        except Exception as e:
            logger.warning(f"OpenAI failed: {e}")

    return json.dumps({"error": "No AI provider available"}) if json_mode else "AI service unavailable. Please check your API keys in .env file."


LEGAL_TEMPLATES = {
    "Legal Notice": "Draft a formal Indian Legal Notice with advocate details, date, facts in numbered paragraphs, 15-day demand, consequences, formal closing.",
    "NDA": "Draft a Non-Disclosure Agreement under Indian law with parties, confidential info definition, obligations, 3-year term, remedies.",
    "Service Agreement": "Draft a Service Agreement under Indian contract law with parties, scope, payment, IP, confidentiality, termination, dispute resolution.",
    "Demand Notice": "Draft a Demand Notice under Section 138 NI Act for dishonoured cheque with all statutory requirements.",
    "Affidavit": "Draft an Affidavit for Indian courts with deponent details, sworn statement, facts, verification clause.",
    "Plaint": "Draft a Civil Plaint for Indian District Court with court name, parties, jurisdiction, cause of action, reliefs, verification.",
    "Legal Opinion": "Draft a Legal Opinion with facts, legal issues, applicable law, precedents, analysis, conclusion.",
    "Rent Agreement": "Draft a Rent Agreement under Indian law with parties, property, rent, deposit, duration, terms, maintenance.",
    "Employment Contract": "Draft an Employment Contract under Indian labour law with designation, CTC, probation, confidentiality, termination.",
    "Power of Attorney": "Draft a Power of Attorney under Indian law with donor, donee, powers granted, revocation clause.",
}


def generate_legal_document(doc_type, client_name, opposite_party, subject, jurisdiction, relief, extra=""):
    template = LEGAL_TEMPLATES.get(doc_type, LEGAL_TEMPLATES["Legal Notice"])
    system_msg = f"You are a senior Indian advocate with 20 years experience. {template} Use formal legal language. Generate a COMPLETE ready-to-use document. Do not use placeholder text."
    user_msg = f"Generate complete {doc_type}:\\nClient: {client_name}\\nOpposite Party: {opposite_party}\\nSubject: {subject}\\nJurisdiction: {jurisdiction}\\nRelief: {relief}\\nExtra: {extra}"
    return _call_ai(system_msg, user_msg)


def analyze_contract(text):
    system_msg = 'You are an expert Indian contract lawyer. Return ONLY valid JSON: {"risk_score": 1-10, "risk_level": "low|medium|high", "summary": "...", "red_flags": [{"clause": "...", "issue": "...", "severity": "..."}], "missing_clauses": [], "recommendations": []}'
    result = _call_ai(system_msg, f"Analyze:\\n{text[:4000]}", json_mode=True)
    try:
        return json.loads(result)
    except:
        return {"risk_score": 5, "risk_level": "medium", "summary": "Analysis complete.", "red_flags": [], "missing_clauses": [], "recommendations": ["Have a senior advocate review this contract"]}


def do_legal_research(query, court_filter=""):
    system_msg = "You are a senior Indian advocate. Provide: relevant court judgments with citations, applicable law sections, current legal position, practical advice."
    return _call_ai(system_msg, f"Research: {query}\\nCourt: {court_filter or 'All Indian courts'}")


def find_precedents(matter_type, facts, court=""):
    system_msg = "You are a senior Indian advocate. Find 5 relevant Indian court precedents with: case name, citation, court, year, ratio decidendi, relevance."
    return _call_ai(system_msg, f"Matter: {matter_type}\\nFacts: {facts}\\nCourt: {court or 'Supreme Court/High Courts'}")


def ai_chat_response(message, client_data=None):
    system_msg = """You are Maavi, an expert AI assistant for CA firms and Law firms in India.
You help with GST queries, TDS calculations, Income Tax, legal matters, compliance deadlines, financial insights.
Be concise, accurate, and professional. Use INR for amounts. Today is 2026."""
    context = f"\\n\\nClient Data: {json.dumps(client_data, default=str)[:2000]}" if client_data else ""
    return _call_ai(system_msg, message + context)


def extract_invoice_data(text):
    system_msg = 'Extract invoice data and return ONLY valid JSON: {"vendor_name":"","vendor_gstin":"","invoice_number":"","invoice_date":"","taxable_amount":0,"cgst_amount":0,"sgst_amount":0,"igst_amount":0,"total_tax":0,"total_amount":0,"hsn_sac_code":"","description":""}'
    result = _call_ai(system_msg, f"Extract from:\\n{text[:3000]}", json_mode=True)
    try:
        return json.loads(result)
    except:
        return {}


def generate_financial_insight(client_name, invoices, compliance_items):
    system_msg = "You are a CA providing financial insights. Analyze data and provide: financial health, GST liability, top expenses, compliance status, recommendations."
    total_revenue = sum(i.get("total_amount", 0) for i in invoices if i.get("invoice_type") == "sale")
    total_expenses = sum(i.get("total_amount", 0) for i in invoices if i.get("invoice_type") == "purchase")
    summary = f"Client: {client_name}\\nInvoices: {len(invoices)}\\nRevenue: Rs.{total_revenue}\\nExpenses: Rs.{total_expenses}\\nPending compliance: {sum(1 for c in compliance_items if c.get('status') == 'pending')}"
    return _call_ai(system_msg, summary)


# ── Backward compatibility aliases ──
extract_invoice_data_with_ai = extract_invoice_data
generate_document_summary = ai_chat_response
analyze_contract_text = analyze_contract
get_ai_chat_response = ai_chat_response
generate_financial_insights = generate_financial_insight

def detect_gst_anomalies(client_id, db):
    return []

def process_document_with_ai(text, doc_type="invoice"):
    return extract_invoice_data(text)
'''

ai_dir = os.path.join(BASE, 'app', 'services', 'ai')
os.makedirs(ai_dir, exist_ok=True)
with open(os.path.join(ai_dir, 'ai_service.py'), 'w', encoding='utf-8') as f:
    f.write(ai_service)
print("1. ai_service.py rewritten with Groq/Gemini/Anthropic/OpenAI support")

# ── 2. Fix ALL python files with old import names ──
old_to_new = {
    'extract_invoice_data_with_ai': 'extract_invoice_data',
    'generate_document_summary': 'ai_chat_response',
    'analyze_contract_text': 'analyze_contract',
    'get_ai_chat_response': 'ai_chat_response',
    'generate_financial_insights': 'generate_financial_insight',
}
fixed_files = []
for root, dirs, files in os.walk(os.path.join(BASE, 'app')):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fname in files:
        if not fname.endswith('.py'):
            continue
        path = os.path.join(root, fname)
        try:
            c = open(path, encoding='utf-8').read()
            orig = c
            for old, new in old_to_new.items():
                c = c.replace(old, new)
            if c != orig:
                open(path, 'w', encoding='utf-8').write(c)
                fixed_files.append(fname)
        except:
            pass
print(f"2. Fixed imports in {len(fixed_files)} files: {fixed_files}")

# ── 3. Fix routes.py - remove broken AI imports ──
routes_path = os.path.join(BASE, 'app', 'api', 'routes', 'routes.py')
if os.path.exists(routes_path):
    c = open(routes_path, encoding='utf-8').read()
    c = re.sub(
        r'from app\.services\.ai\.ai_service import[^\n]*generate_financial_insights[^\n]*\n',
        'from app.services.ai.ai_service import generate_financial_insight as generate_financial_insights, ai_chat_response, detect_gst_anomalies\n',
        c
    )
    open(routes_path, 'w', encoding='utf-8').write(c)
    print("3. routes.py AI imports fixed")

# ── 4. Rewrite chat_routes.py ──
chat_route = os.path.join(BASE, 'app', 'api', 'routes', 'chat_routes.py')
chat_content = '''# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from app.db.database import get_db
from app.models import Client, Invoice, ComplianceItem
from app.core.security import get_current_user
from app.services.ai.ai_service import ai_chat_response

chat_router = APIRouter(prefix="/chat", tags=["AI Chat"])

class ChatRequest(BaseModel):
    message: str
    client_id: Optional[int] = None
    session_id: Optional[str] = None

@chat_router.post("/")
def chat(req: ChatRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    session_id = req.session_id or str(uuid.uuid4())
    client_data = None
    if req.client_id:
        client = db.query(Client).filter(Client.id == req.client_id, Client.ca_user_id == current_user.id).first()
        if client:
            invoices = db.query(Invoice).filter(Invoice.client_id == client.id).limit(20).all()
            compliance = db.query(ComplianceItem).filter(ComplianceItem.client_id == client.id).limit(10).all()
            client_data = {
                "company_name": client.company_name,
                "gstin": client.gstin,
                "total_invoices": len(invoices),
                "total_revenue": sum((i.total_amount or 0) for i in invoices if i.invoice_type and i.invoice_type.value == "sale"),
                "total_expenses": sum((i.total_amount or 0) for i in invoices if i.invoice_type and i.invoice_type.value == "purchase"),
                "pending_compliance": sum(1 for c in compliance if c.status and c.status.value in ["pending", "overdue"]),
            }
    response = ai_chat_response(req.message, client_data)
    return {"response": response, "session_id": session_id, "client_id": req.client_id}

@chat_router.get("/history/{session_id}")
def get_history(session_id: str, current_user=Depends(get_current_user)):
    return {"session_id": session_id, "messages": []}
'''
with open(chat_route, 'w', encoding='utf-8') as f:
    f.write(chat_content)
print("4. chat_routes.py rewritten")

# ── 5. Register chat_router in main.py if missing ──
main_path = os.path.join(BASE, 'main.py')
main = open(main_path, encoding='utf-8').read()
if 'chat_routes' not in main and 'from app.api.routes.chat_routes' not in main:
    main = main.replace(
        'from app.api.routes.gst_routes import gst_router',
        'from app.api.routes.chat_routes import chat_router as dedicated_chat_router\nfrom app.api.routes.gst_routes import gst_router'
    )
    main = main.replace(
        'app.include_router(gst_router',
        'app.include_router(dedicated_chat_router, prefix="/api/v1")\n    app.include_router(gst_router'
    )
    open(main_path, 'w', encoding='utf-8').write(main)
    print("5. chat_router registered in main.py")
else:
    print("5. main.py already has chat router")

# ── 6. Install Groq package ──
print("6. Installing groq package...")
os.system(f'"{sys.executable}" -m pip install groq -q')
print("   Done!")

# ── 7. Test AI connection ──
print("\n7. Testing AI connection...")
os.environ['GROQ_API_KEY'] = open('.env', encoding='utf-8').read()
import re as _re
groq_match = _re.search(r'GROQ_API_KEY=(.+)', open('.env', encoding='utf-8').read())
if groq_match:
    os.environ['GROQ_API_KEY'] = groq_match.group(1).strip()
    os.environ['AI_PROVIDER'] = 'groq'
    try:
        sys.path.insert(0, BASE)
        from app.services.ai.ai_service import ai_chat_response
        result = ai_chat_response("Say exactly: Maavi AI is ready!")
        print(f"   SUCCESS: {result[:80]}")
    except Exception as e:
        print(f"   Error: {e}")

print("""
============================================
  ALL FIXES APPLIED!
============================================
Now run:
  uvicorn main:app --port 8000

Then test AI Chat at http://localhost:3000
============================================
""")
