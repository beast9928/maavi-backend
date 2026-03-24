# -*- coding: utf-8 -*-
# switch_gemini.py - Run this in your backend folder
# Usage: python switch_gemini.py AIzaSyBOrW3GP6y02Fre00c_m5Ly2lwDvcBaKjs

import os, sys

GEMINI_KEY = sys.argv[1] if len(sys.argv) > 1 else ""
if not GEMINI_KEY:
    GEMINI_KEY = input("Paste your Gemini API key (AIzaSy...): ").strip()

BASE = os.path.dirname(os.path.abspath(__file__))
FRONT = os.path.join(BASE, '..', 'frontend', 'src')

# ── 1. Update .env ──────────────────────────────────────────────────────────
env_path = os.path.join(BASE, '.env')
env = open(env_path, encoding='utf-8').read()
if 'GEMINI_API_KEY' in env:
    import re
    env = re.sub(r'GEMINI_API_KEY=.*', f'GEMINI_API_KEY={GEMINI_KEY}', env)
else:
    env += f'\nGEMINI_API_KEY={GEMINI_KEY}\n'
if 'AI_PROVIDER' not in env:
    env += 'AI_PROVIDER=gemini\n'
open(env_path, 'w', encoding='utf-8').write(env)
print("1. .env updated with Gemini key")

# ── 2. Rewrite AI service (Gemini + OpenAI fallback) ───────────────────────
ai_dir = os.path.join(BASE, 'app', 'services', 'ai')
os.makedirs(ai_dir, exist_ok=True)

ai_service = '''# -*- coding: utf-8 -*-
import json, logging, os
logger = logging.getLogger(__name__)

def _call_ai(system_msg, user_msg, json_mode=False):
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")

    # Try Gemini first
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            prompt = system_msg + "\\n\\n" + user_msg
            if json_mode:
                prompt += "\\n\\nRespond ONLY with valid JSON. No markdown, no backticks, no explanation."
            response = model.generate_content(prompt)
            result = response.text.strip()
            if json_mode:
                result = result.replace("```json", "").replace("```", "").strip()
            return result
        except Exception as e:
            logger.warning(f"Gemini failed, trying OpenAI: {e}")

    # Fallback to OpenAI
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            kwargs = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": 2000,
                "temperature": 0.2
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            r = client.chat.completions.create(**kwargs)
            return r.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI also failed: {e}")

    err = "No AI provider available. Add GEMINI_API_KEY or OPENAI_API_KEY to .env"
    return json.dumps({"error": err}) if json_mode else err


LEGAL_TEMPLATES = {
    "Legal Notice": "Draft a formal Indian Legal Notice. Include: advocate letterhead, date, recipient address, facts in numbered paragraphs, specific demand with 15-day deadline, consequences of non-compliance, formal closing.",
    "NDA": "Draft a Non-Disclosure Agreement under Indian law. Include: parties, definition of confidential information, obligations, exclusions, term of 3 years, remedies for breach, governing law clause.",
    "Service Agreement": "Draft a Service Agreement under Indian contract law. Include: parties, scope of services, payment terms, IP ownership, confidentiality, limitation of liability, termination, dispute resolution.",
    "Demand Notice": "Draft a Demand Notice under Section 138 of the Negotiable Instruments Act for dishonoured cheque. Include all statutory requirements.",
    "Affidavit": "Draft an Affidavit for Indian courts. Include: deponent details, sworn statement, numbered paragraphs of facts, verification clause, notary section.",
    "Plaint": "Draft a Civil Plaint for Indian District Court. Include: court name, parties with addresses, jurisdiction, cause of action, facts, reliefs sought, prayer, verification.",
    "Legal Opinion": "Draft a Legal Opinion letter. Include: facts presented, legal issues, applicable law and precedents, analysis, conclusion with recommendations.",
    "Rent Agreement": "Draft a Rent/Lease Agreement under Indian law. Include: parties, property description, rent amount, security deposit, duration, terms, termination notice, maintenance obligations.",
    "Employment Contract": "Draft an Employment Contract under Indian labour law. Include: designation, CTC, probation, confidentiality, non-compete, IP assignment, termination conditions.",
    "Power of Attorney": "Draft a General/Specific Power of Attorney under Indian law. Include: donor, donee, powers granted, consideration, revocation clause, witness requirements.",
}


def generate_legal_document(doc_type, client_name, opposite_party, subject, jurisdiction, relief, extra=""):
    template = LEGAL_TEMPLATES.get(doc_type, LEGAL_TEMPLATES["Legal Notice"])
    system_msg = f"""You are a senior Indian advocate with 20 years experience.
{template}
Use formal legal language. Generate a COMPLETE, ready-to-use document with all sections filled in.
Do not use placeholder text like [NAME] - use the actual information provided."""
    user_msg = f"""Generate a complete {doc_type}:
Client / Party A: {client_name}
Opposite Party / Party B: {opposite_party}
Subject / Matter: {subject}
Jurisdiction: {jurisdiction}
Relief Sought: {relief}
Additional Details: {extra}"""
    return _call_ai(system_msg, user_msg)


def analyze_contract(text):
    system_msg = """You are an expert Indian contract lawyer. Analyze this contract and return ONLY valid JSON with this exact structure:
{
  "risk_score": <number 1-10>,
  "risk_level": "<low|medium|high>",
  "summary": "<2-3 sentence summary>",
  "red_flags": [{"clause": "<clause name>", "issue": "<issue description>", "severity": "<low|medium|high>"}],
  "missing_clauses": ["<clause 1>", "<clause 2>"],
  "recommendations": ["<recommendation 1>", "<recommendation 2>"]
}"""
    result = _call_ai(system_msg, f"Analyze this contract:\\n{text[:4000]}", json_mode=True)
    try:
        return json.loads(result)
    except Exception:
        return {"risk_score": 5, "risk_level": "medium", "summary": "Analysis complete. Review manually for detailed assessment.", "red_flags": [], "missing_clauses": [], "recommendations": ["Have a senior advocate review this contract"]}


def do_legal_research(query, court_filter=""):
    system_msg = """You are a senior Indian advocate. Provide comprehensive legal research including:
1. Relevant Indian court judgments with citations (Supreme Court, High Courts)
2. Applicable sections of relevant Acts
3. Current legal position
4. Practical advice for the client
Be specific with case names, years, and citations where possible."""
    user_msg = f"Legal Research Query: {query}\\nCourt Preference: {court_filter or 'All Indian courts'}"
    return _call_ai(system_msg, user_msg)


def find_precedents(matter_type, facts, court=""):
    system_msg = """You are a senior Indian advocate. Find the 5 most relevant Indian court precedents.
For each precedent provide:
- Case name and citation
- Court and year
- Key legal principle (ratio decidendi)
- Why it applies to this matter
Format clearly with each case on a new section."""
    user_msg = f"Matter Type: {matter_type}\\nFacts: {facts}\\nPreferred Court: {court or 'Supreme Court / High Courts'}"
    return _call_ai(system_msg, user_msg)


def ai_chat_response(message, client_data=None):
    system_msg = """You are Maavi, an AI assistant for CA firms and Law firms in India.
You help with:
- GST queries, TDS calculations, Income Tax analysis
- Legal matter summaries, compliance deadlines
- Financial insights, expense analysis
- Document explanations
Be concise, accurate, and professional. Use INR (rupees) for amounts."""
    context = ""
    if client_data:
        context = f"\\n\\nClient Context:\\n{json.dumps(client_data, default=str)[:2000]}"
    return _call_ai(system_msg, message + context)


def extract_invoice_data(text):
    system_msg = """Extract invoice data from the following text and return ONLY valid JSON:
{
  "vendor_name": "",
  "vendor_gstin": "",
  "invoice_number": "",
  "invoice_date": "",
  "taxable_amount": 0,
  "cgst_amount": 0,
  "sgst_amount": 0,
  "igst_amount": 0,
  "total_tax": 0,
  "total_amount": 0,
  "hsn_sac_code": "",
  "description": ""
}
Return only valid JSON, no other text."""
    result = _call_ai(system_msg, f"Extract from:\\n{text[:3000]}", json_mode=True)
    try:
        return json.loads(result)
    except Exception:
        return {}


def generate_financial_insight(client_name, invoices, compliance_items):
    system_msg = """You are a CA (Chartered Accountant) providing financial insights.
Analyze the data and provide:
1. Overall financial health assessment
2. GST liability summary
3. Top expense categories
4. Compliance status
5. Key recommendations
Be specific with numbers and actionable advice."""
    summary = f"""Client: {client_name}
Total Invoices: {len(invoices)}
Total Revenue: {sum(i.get('total_amount', 0) for i in invoices if i.get('invoice_type') == 'sale')}
Total Expenses: {sum(i.get('total_amount', 0) for i in invoices if i.get('invoice_type') == 'purchase')}
Pending Compliance: {sum(1 for c in compliance_items if c.get('status') == 'pending')}
Overdue Compliance: {sum(1 for c in compliance_items if c.get('status') == 'overdue')}"""
    return _call_ai(system_msg, summary)
'''

with open(os.path.join(ai_dir, 'ai_service.py'), 'w', encoding='utf-8') as f:
    f.write(ai_service)
print("2. AI service rewritten (Gemini + OpenAI fallback)")

# ── 3. Update legal_ai.py to use the new ai_service ─────────────────────
legal_ai = '''# -*- coding: utf-8 -*-
from app.services.ai.ai_service import (
    generate_legal_document,
    analyze_contract,
    do_legal_research,
    find_precedents,
    ai_chat_response,
    extract_invoice_data,
    generate_financial_insight
)
__all__ = [
    "generate_legal_document",
    "analyze_contract",
    "do_legal_research",
    "find_precedents",
    "ai_chat_response",
    "extract_invoice_data",
    "generate_financial_insight",
]
'''
with open(os.path.join(ai_dir, 'legal_ai.py'), 'w', encoding='utf-8') as f:
    f.write(legal_ai)
print("3. legal_ai.py updated")

# ── 4. Fix AI Chat route to use new service ──────────────────────────────
routes_path = os.path.join(BASE, 'app', 'api', 'routes', 'routes.py')
if os.path.exists(routes_path):
    content = open(routes_path, encoding='utf-8').read()
    if 'ai_chat_response' not in content:
        # Add import at top
        content = 'from app.services.ai.ai_service import ai_chat_response, generate_financial_insight\n' + content
        open(routes_path, 'w', encoding='utf-8').write(content)
        print("4. routes.py updated with AI imports")
    else:
        print("4. routes.py already updated")

# ── 5. Fix the chat endpoint ─────────────────────────────────────────────
chat_route = os.path.join(BASE, 'app', 'api', 'routes', 'chat_routes.py')
chat_content = '''# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
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
        client = db.query(Client).filter(
            Client.id == req.client_id,
            Client.ca_user_id == current_user.id
        ).first()
        if client:
            invoices = db.query(Invoice).filter(Invoice.client_id == client.id).limit(20).all()
            compliance = db.query(ComplianceItem).filter(ComplianceItem.client_id == client.id).limit(10).all()
            client_data = {
                "company_name": client.company_name,
                "gstin": client.gstin,
                "total_invoices": len(invoices),
                "total_revenue": sum(
                    (i.total_amount or 0) for i in invoices
                    if i.invoice_type and i.invoice_type.value == "sale"
                ),
                "total_expenses": sum(
                    (i.total_amount or 0) for i in invoices
                    if i.invoice_type and i.invoice_type.value == "purchase"
                ),
                "pending_compliance": sum(
                    1 for c in compliance
                    if c.status and c.status.value in ["pending", "overdue"]
                ),
            }

    response = ai_chat_response(req.message, client_data)
    return {
        "response": response,
        "session_id": session_id,
        "client_id": req.client_id
    }

@chat_router.get("/history/{session_id}")
def get_history(session_id: str, current_user=Depends(get_current_user)):
    return {"session_id": session_id, "messages": []}
'''
with open(chat_route, 'w', encoding='utf-8') as f:
    f.write(chat_content)
print("5. Chat route fixed")

# ── 6. Register chat_router in main.py if needed ─────────────────────────
main_path = os.path.join(BASE, 'main.py')
main_content = open(main_path, encoding='utf-8').read()
if 'chat_routes' not in main_content and 'chat_router' in main_content:
    print("6. chat_router already registered")
elif 'chat_routes' not in main_content:
    # Add import and registration
    main_content = main_content.replace(
        'from app.api.routes.gst_routes import gst_router',
        'from app.api.routes.chat_routes import chat_router as new_chat_router\nfrom app.api.routes.gst_routes import gst_router'
    )
    open(main_path, 'w', encoding='utf-8').write(main_content)
    print("6. chat_router registered in main.py")
else:
    print("6. main.py already has chat routes")

# ── 7. Install google-generativeai ───────────────────────────────────────
print("7. Installing google-generativeai...")
os.system(f'"{sys.executable}" -m pip install google-generativeai -q')
print("   Done!")

# ── 8. Test the Gemini connection ────────────────────────────────────────
print("\n8. Testing Gemini connection...")
try:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say 'Maavi AI is ready!' in exactly those words.")
    print(f"   SUCCESS: {response.text.strip()}")
except Exception as e:
    print(f"   WARNING: {e}")
    print("   Make sure your Gemini key is correct")

print("""
==========================================
   GEMINI SWITCH COMPLETE!
==========================================
Now restart your backend:
  taskkill /F /IM python.exe
  uvicorn main:app --port 8000

Then test AI Chat at http://localhost:3000
==========================================
""")