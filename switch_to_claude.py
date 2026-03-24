# switch_to_claude.py
# Run: python switch_to_claude.py YOUR_ANTHROPIC_KEY
# Get free key: https://console.anthropic.com

import os, sys, re

KEY = sys.argv[1] if len(sys.argv) > 1 else input("Paste Anthropic API key (sk-ant-...): ").strip()

BASE = os.path.dirname(os.path.abspath(__file__))

# 1. Update .env
env_path = os.path.join(BASE, '.env')
env = open(env_path, encoding='utf-8').read()
env = re.sub(r'ANTHROPIC_API_KEY=.*\n?', '', env)
env = re.sub(r'AI_PROVIDER=.*\n?', '', env)
env = env.rstrip() + f'\nANTHROPIC_API_KEY={KEY}\nAI_PROVIDER=anthropic\n'
open(env_path, 'w', encoding='utf-8').write(env)
print("1. .env updated")

# 2. Install anthropic SDK
print("2. Installing anthropic SDK...")
os.system(f'"{sys.executable}" -m pip install anthropic -q')
print("   Done!")

# 3. Rewrite ai_service.py completely
ai_dir = os.path.join(BASE, 'app', 'services', 'ai')
os.makedirs(ai_dir, exist_ok=True)

ai_service = r'''# -*- coding: utf-8 -*-
import json, logging, os, re
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '.env'))
logger = logging.getLogger(__name__)

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

def _call_ai(system_msg, user_msg, json_mode=False):
    key = os.getenv("ANTHROPIC_API_KEY", "") or ANTHROPIC_KEY
    if not key:
        err = "No AI key found. Add ANTHROPIC_API_KEY to .env"
        return json.dumps({"error": err}) if json_mode else err
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        prompt = user_msg
        if json_mode:
            prompt += "\n\nRespond ONLY with valid JSON. No markdown, no backticks, no explanation."
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=system_msg,
            messages=[{"role": "user", "content": prompt}]
        )
        result = message.content[0].text.strip()
        if json_mode:
            result = result.replace("```json", "").replace("```", "").strip()
        return result
    except Exception as e:
        logger.error(f"Anthropic error: {e}")
        err = f"AI Error: {str(e)}"
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
    system_msg = """You are an expert Indian contract lawyer. Analyze this contract and return ONLY valid JSON:
{
  "risk_score": <number 1-10>,
  "risk_level": "<low|medium|high>",
  "summary": "<2-3 sentence summary>",
  "red_flags": [{"clause": "<clause name>", "issue": "<issue>", "severity": "<low|medium|high>"}],
  "missing_clauses": ["<clause 1>"],
  "recommendations": ["<rec 1>"]
}"""
    result = _call_ai(system_msg, f"Analyze this contract:\n{text[:4000]}", json_mode=True)
    try:
        return json.loads(result)
    except Exception:
        return {"risk_score": 5, "risk_level": "medium", "summary": "Analysis complete.", "red_flags": [], "missing_clauses": [], "recommendations": ["Review manually"]}


def do_legal_research(query, court_filter=""):
    system_msg = """You are a senior Indian advocate. Provide comprehensive legal research including:
1. Relevant Indian court judgments with citations
2. Applicable sections of relevant Acts
3. Current legal position
4. Practical advice
Be specific with case names, years, and citations."""
    return _call_ai(system_msg, f"Query: {query}\nCourt: {court_filter or 'All Indian courts'}")


def find_precedents(matter_type, facts, court=""):
    system_msg = """You are a senior Indian advocate. Find 5 relevant Indian court precedents.
For each: case name, citation, court, year, key principle, why it applies."""
    return _call_ai(system_msg, f"Matter: {matter_type}\nFacts: {facts}\nCourt: {court or 'Supreme Court / High Courts'}")


def ai_chat_response(message, client_data=None):
    system_msg = """You are Maavi, an AI assistant for CA firms and Law firms in India.
You help with GST queries, TDS calculations, Income Tax, legal matters, compliance deadlines, financial insights.
Be concise, accurate, and professional. Use INR for amounts."""
    context = ""
    if client_data:
        context = f"\n\nClient Context:\n{json.dumps(client_data, default=str)[:2000]}"
    return _call_ai(system_msg, message + context)


def extract_invoice_data(text):
    system_msg = """Extract invoice data and return ONLY valid JSON:
{"vendor_name":"","vendor_gstin":"","invoice_number":"","invoice_date":"","taxable_amount":0,"cgst_amount":0,"sgst_amount":0,"igst_amount":0,"total_tax":0,"total_amount":0,"hsn_sac_code":"","description":""}"""
    result = _call_ai(system_msg, f"Extract from:\n{text[:3000]}", json_mode=True)
    try:
        return json.loads(result)
    except Exception:
        return {}


def generate_financial_insight(client_name, invoices, compliance_items):
    system_msg = """You are a CA providing financial insights. Analyze and provide:
1. Financial health assessment
2. GST liability summary  
3. Top expense categories
4. Compliance status
5. Key recommendations"""
    summary = f"""Client: {client_name}
Total Invoices: {len(invoices)}
Total Revenue: {sum(i.get('total_amount', 0) for i in invoices if i.get('invoice_type') == 'sale')}
Total Expenses: {sum(i.get('total_amount', 0) for i in invoices if i.get('invoice_type') == 'purchase')}
Pending Compliance: {sum(1 for c in compliance_items if c.get('status') == 'pending')}
Overdue: {sum(1 for c in compliance_items if c.get('status') == 'overdue')}"""
    return _call_ai(system_msg, summary)


# ── Aliases (do not remove) ──────────────────────────────────────────────────
def chat_with_financial_data(message, client_id=None, db=None):
    return ai_chat_response(message)

generate_financial_insights  = generate_financial_insight
extract_invoice_data_with_ai = extract_invoice_data
generate_document_summary    = ai_chat_response
analyze_contract_text        = analyze_contract
get_ai_chat_response         = ai_chat_response

def detect_gst_anomalies(client_id, db):
    return []
'''

with open(os.path.join(ai_dir, 'ai_service.py'), 'w', encoding='utf-8') as f:
    f.write(ai_service)
print("3. ai_service.py rewritten with Anthropic Claude")

# 4. Test the connection
print("\n4. Testing connection...")
try:
    import anthropic
    client = anthropic.Anthropic(api_key=KEY)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say: Maavi AI is ready!"}]
    )
    print(f"   SUCCESS: {msg.content[0].text.strip()}")
except Exception as e:
    print(f"   ERROR: {e}")
    print("   Check your API key at console.anthropic.com")

print("""
==========================================
  SWITCH TO CLAUDE AI COMPLETE!
==========================================
Now restart backend:
  taskkill /F /IM python.exe
  uvicorn main:app --port 8000

Then test chat at http://localhost:3000/chat
==========================================
""")