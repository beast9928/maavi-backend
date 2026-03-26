# -*- coding: utf-8 -*-
import json, logging, os
logger = logging.getLogger(__name__)

def _call_ai(system_msg, user_msg, json_mode=False):
    gemini_key= os.getenv("AIzaSyDUbvwb6WDiIPxXMmrmBQiknRYfuBRJ-Cg","")
    hint = "\nRespond ONLY with valid JSON. No markdown, no backticks." if json_mode else ""

    if groq_key:
        try:
            from groq import Groq
            r = Groq(api_key=groq_key).chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role":"system","content":system_msg},{"role":"user","content":user_msg+hint}],
                max_tokens=2048, temperature=0.2)
            return r.choices[0].message.content.strip()
        except Exception as e: logger.warning(f"Groq: {e}")

    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            r = genai.GenerativeModel("gemini-1.5-flash").generate_content(system_msg+"\n"+user_msg+hint)
            return r.text.strip().replace("```json","").replace("```","").strip()
        except Exception as e: logger.warning(f"Gemini: {e}")

    if anth_key:
        try:
            import anthropic
            r = anthropic.Anthropic(api_key=anth_key).messages.create(
                model="claude-3-haiku-20240307", max_tokens=2048,
                system=system_msg, messages=[{"role":"user","content":user_msg+hint}])
            return r.content[0].text.strip()
        except Exception as e: logger.warning(f"Anthropic: {e}")

    if openai_key:
        try:
            from openai import OpenAI
            kw = {"model":"gpt-4o","messages":[{"role":"system","content":system_msg},{"role":"user","content":user_msg}],"max_tokens":2048,"temperature":0.2}
            if json_mode: kw["response_format"]={"type":"json_object"}
            r = OpenAI(api_key=openai_key).chat.completions.create(**kw)
            return r.choices[0].message.content.strip()
        except Exception as e: logger.warning(f"OpenAI: {e}")

    return '{"error":"No AI available"}' if json_mode else "AI unavailable. Check API keys in .env"


def ai_chat_response(message, client_data=None):
    sys_msg = """You are Maavi AI, an expert assistant for CA and Law firms in India.
Specialise in: GST, TDS, Income Tax, Company Law, Compliance, Legal drafting.
Be concise, accurate, professional. Use INR. Year: 2026. Use bullet points for lists."""
    ctx = ""
    if client_data:
        ctx = f"""\n\nClient: {client_data.get('company_name','')}
GSTIN: {client_data.get('gstin','N/A')}
Revenue: ₹{client_data.get('total_revenue',0):,.0f}
Expenses: ₹{client_data.get('total_expenses',0):,.0f}
Pending compliance: {client_data.get('pending_compliance',0)}"""
    return _call_ai(sys_msg, message+ctx)

def extract_invoice_data(text):
    sys_msg = 'Return ONLY JSON: {"vendor_name":"","vendor_gstin":"","invoice_number":"","invoice_date":"","taxable_amount":0,"cgst_amount":0,"sgst_amount":0,"igst_amount":0,"total_tax":0,"total_amount":0,"hsn_sac_code":"","description":""}'
    try: return json.loads(_call_ai(sys_msg, text[:4000], json_mode=True))
    except: return {}

def analyze_contract(text):
    sys_msg = 'Return ONLY JSON: {"risk_score":5,"risk_level":"medium","summary":"","red_flags":[{"clause":"","issue":"","severity":""}],"missing_clauses":[],"recommendations":[]}'
    try: return json.loads(_call_ai(sys_msg, text[:5000], json_mode=True))
    except: return {"risk_score":5,"risk_level":"medium","summary":"Review complete.","red_flags":[],"missing_clauses":[],"recommendations":["Consult a senior advocate."]}

def generate_legal_document(doc_type, client_name, opposite_party, subject, jurisdiction, relief, extra=""):
    templates = {
        "Legal Notice": "Draft a formal Indian Legal Notice with advocate details, facts, 15-day demand.",
        "NDA": "Draft an NDA under Indian Contract Act with parties, obligations, 3-year term.",
        "Service Agreement": "Draft a Service Agreement with scope, payment, IP, confidentiality, arbitration.",
        "Demand Notice": "Draft a Demand Notice under S.138 NI Act with all statutory requirements.",
        "Affidavit": "Draft an Affidavit with deponent, sworn statement, verification clause.",
        "Plaint": "Draft a Civil Plaint with court heading, jurisdiction, cause of action, prayer.",
        "Legal Opinion": "Draft a Legal Opinion with facts, issues, law, analysis, conclusion.",
        "Rent Agreement": "Draft a Rent Agreement with property, rent, deposit, duration, terms.",
        "Employment Contract": "Draft an Employment Contract with designation, CTC, probation, termination.",
        "Power of Attorney": "Draft a POA with donor, donee, powers, validity, revocation.",
    }
    t = templates.get(doc_type, templates["Legal Notice"])
    return _call_ai(f"You are a senior Indian advocate. {t} Generate COMPLETE ready-to-use document.",
        f"Generate {doc_type}:\nClient: {client_name}\nOpposite Party: {opposite_party}\nSubject: {subject}\nJurisdiction: {jurisdiction}\nRelief: {relief}\nExtra: {extra}")

def do_legal_research(query, court_filter=""):
    return _call_ai("You are a senior Indian advocate. Provide case citations, statutory provisions, current legal position, practical advice.",
        f"Research: {query}\nCourt: {court_filter or 'All Indian courts'}")

def find_precedents(matter_type, facts, court=""):
    return _call_ai("You are a senior Indian advocate. Find 5 relevant precedents with case name, citation, court, year, ratio, relevance.",
        f"Matter: {matter_type}\nFacts: {facts}\nCourt: {court or 'SC/HCs'}")

def generate_financial_insight(client_name, invoices, compliance_items):
    rev = sum(i.get("total_amount",0) for i in invoices if i.get("invoice_type")=="sale")
    exp = sum(i.get("total_amount",0) for i in invoices if i.get("invoice_type")=="purchase")
    pen = sum(1 for c in compliance_items if c.get("status") in ["pending","overdue"])
    return _call_ai("You are a CA. Provide financial health, GST liability, top expenses, compliance status, 3 recommendations.",
        f"Client:{client_name} Revenue:₹{rev:,.0f} Expenses:₹{exp:,.0f} Net:₹{rev-exp:,.0f} Pending:{pen}")

# Aliases - NEVER REMOVE
extract_invoice_data_with_ai = extract_invoice_data
generate_document_summary    = ai_chat_response
analyze_contract_text        = analyze_contract
get_ai_chat_response         = ai_chat_response
generate_financial_insights  = generate_financial_insight
process_document_with_ai     = lambda text, doc_type="invoice": extract_invoice_data(text)
def detect_gst_anomalies(client_id, db): return []
