# switch_to_groq.py
import os, sys, re

KEY = sys.argv[1] if len(sys.argv) > 1 else input("Paste Groq API key (gsk_...): ").strip()
BASE = os.path.dirname(os.path.abspath(__file__))

# Update .env
env_path = os.path.join(BASE, '.env')
env = open(env_path, encoding='utf-8').read()
env = re.sub(r'GROQ_API_KEY=.*\n?', '', env)
env = env.rstrip() + f'\nGROQ_API_KEY={KEY}\nAI_PROVIDER=groq\n'
open(env_path, 'w', encoding='utf-8').write(env)
print("1. .env updated")

# Rewrite ai_service.py
ai_path = os.path.join(BASE, 'app', 'services', 'ai', 'ai_service.py')
ai_service = f'''# -*- coding: utf-8 -*-
import json, logging, os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".env"))
logger = logging.getLogger(__name__)

GROQ_KEY = "{KEY}"

def _call_ai(system_msg, user_msg, json_mode=False):
    key = os.getenv("GROQ_API_KEY", "") or GROQ_KEY
    try:
        from groq import Groq
        client = Groq(api_key=key)
        prompt = user_msg
        if json_mode:
            prompt += "\\n\\nRespond ONLY with valid JSON. No markdown, no backticks."
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {{"role": "system", "content": system_msg}},
                {{"role": "user", "content": prompt}}
            ],
            max_tokens=2048,
            temperature=0.2
        )
        result = response.choices[0].message.content.strip()
        if json_mode:
            result = result.replace("```json", "").replace("```", "").strip()
        return result
    except Exception as e:
        logger.error(f"Groq error: {{e}}")
        err = f"AI Error: {{str(e)}}"
        return json.dumps({{"error": err}}) if json_mode else err


LEGAL_TEMPLATES = {{
    "Legal Notice": "Draft a formal Indian Legal Notice with advocate letterhead, facts, 15-day demand, consequences.",
    "NDA": "Draft an NDA under Indian law with parties, confidential info definition, obligations, 3-year term.",
    "Service Agreement": "Draft a Service Agreement under Indian contract law with scope, payment, IP, termination.",
    "Demand Notice": "Draft a Demand Notice under Section 138 NI Act for dishonoured cheque.",
    "Affidavit": "Draft an Affidavit for Indian courts with deponent details, facts, verification clause.",
    "Rent Agreement": "Draft a Rent Agreement under Indian law with parties, property, rent, deposit, duration.",
    "Employment Contract": "Draft an Employment Contract under Indian labour law with CTC, probation, confidentiality.",
    "Power of Attorney": "Draft a Power of Attorney under Indian law with donor, donee, powers, revocation.",
}}

def generate_legal_document(doc_type, client_name, opposite_party, subject, jurisdiction, relief, extra=""):
    template = LEGAL_TEMPLATES.get(doc_type, LEGAL_TEMPLATES["Legal Notice"])
    system_msg = f"You are a senior Indian advocate. {{template}} Generate COMPLETE ready-to-use document."
    user_msg = f"Generate {{doc_type}}: Client: {{client_name}}, Opposite: {{opposite_party}}, Subject: {{subject}}, Jurisdiction: {{jurisdiction}}, Relief: {{relief}}, Details: {{extra}}"
    return _call_ai(system_msg, user_msg)

def analyze_contract(text):
    system_msg = """Analyze this Indian contract. Return ONLY valid JSON:
{{"risk_score":5,"risk_level":"medium","summary":"","red_flags":[],"missing_clauses":[],"recommendations":[]}}"""
    result = _call_ai(system_msg, f"Analyze:\\n{{text[:4000]}}", json_mode=True)
    try:
        return json.loads(result)
    except:
        return {{"risk_score":5,"risk_level":"medium","summary":"Review manually.","red_flags":[],"missing_clauses":[],"recommendations":[]}}

def do_legal_research(query, court_filter=""):
    system_msg = "You are a senior Indian advocate. Provide legal research with case citations, applicable Acts, current legal position, practical advice."
    return _call_ai(system_msg, f"Query: {{query}}\\nCourt: {{court_filter or 'All Indian courts'}}")

def find_precedents(matter_type, facts, court=""):
    system_msg = "You are a senior Indian advocate. Find 5 relevant Indian court precedents with citations, principles, and relevance."
    return _call_ai(system_msg, f"Matter: {{matter_type}}\\nFacts: {{facts}}\\nCourt: {{court or 'Supreme Court'}}")

def ai_chat_response(message, client_data=None):
    system_msg = "You are Maavi, AI assistant for CA and Law firms in India. Help with GST, TDS, Income Tax, compliance, legal matters. Be concise and professional. Use INR."
    context = f"\\n\\nClient: {{json.dumps(client_data, default=str)[:2000]}}" if client_data else ""
    return _call_ai(system_msg, message + context)

def extract_invoice_data(text):
    system_msg = \'\'\'Return ONLY JSON: {{"vendor_name":"","vendor_gstin":"","invoice_number":"","invoice_date":"","taxable_amount":0,"cgst_amount":0,"sgst_amount":0,"igst_amount":0,"total_tax":0,"total_amount":0,"hsn_sac_code":"","description":""}}\'\'\'
    result = _call_ai(system_msg, f"Extract:\\n{{text[:3000]}}", json_mode=True)
    try:
        return json.loads(result)
    except:
        return {{}}

def generate_financial_insight(client_name, invoices, compliance_items):
    system_msg = "You are a CA. Provide financial health assessment, GST summary, expense categories, compliance status, recommendations."
    summary = f"Client: {{client_name}}\\nInvoices: {{len(invoices)}}\\nRevenue: {{sum(i.get('total_amount',0) for i in invoices if i.get('invoice_type')=='sale')}}\\nExpenses: {{sum(i.get('total_amount',0) for i in invoices if i.get('invoice_type')=='purchase')}}\\nPending: {{sum(1 for c in compliance_items if c.get('status')=='pending')}}"
    return _call_ai(system_msg, summary)

# Aliases
def chat_with_financial_data(message, client_id=None, db=None): return ai_chat_response(message)
generate_financial_insights  = generate_financial_insight
extract_invoice_data_with_ai = extract_invoice_data
generate_document_summary    = ai_chat_response
analyze_contract_text        = analyze_contract
get_ai_chat_response         = ai_chat_response
def detect_gst_anomalies(client_id, db): return []
'''

open(ai_path, 'w', encoding='utf-8').write(ai_service)
print("2. ai_service.py rewritten with Groq")

# Test
print("\n3. Testing Groq...")
try:
    from groq import Groq
    client = Groq(api_key=KEY)
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say: Maavi AI is ready!"}],
        max_tokens=20
    )
    print(f"   SUCCESS: {r.choices[0].message.content.strip()}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\nDone! Now run: taskkill /F /IM python.exe && uvicorn main:app --port 8000")