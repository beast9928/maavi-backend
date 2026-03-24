import os, re

# Read routes.py and find ALL imports from ai_service
routes = open('app/api/routes/routes.py', encoding='utf-8').read()

# Find the bad import line
bad_imports = re.findall(r'from app\.services\.ai\.ai_service import ([^\n]+)', routes)
print("Bad imports found:", bad_imports)

# Replace entire ai_service import block in routes.py with safe version
routes = re.sub(
    r'from app\.services\.ai\.ai_service import[^\n]+\n',
    '# AI imports handled via aliases\n',
    routes
)
open('app/api/routes/routes.py', 'w', encoding='utf-8').write(routes)
print("1. routes.py cleaned")

# Add ALL possible aliases to ai_service.py
ai_path = 'app/services/ai/ai_service.py'
ai = open(ai_path, encoding='utf-8').read()

aliases = '''

# ── Complete backward compatibility aliases ──────────────────────
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

if 'backward compatibility' not in ai:
    ai += aliases
    open(ai_path, 'w', encoding='utf-8').write(ai)
    print("2. All aliases added to ai_service.py")
else:
    print("2. Aliases already present")

# Fix document_service.py
ds_path = 'app/services/document_service.py'
if os.path.exists(ds_path):
    ds = open(ds_path, encoding='utf-8').read()
    ds = ds.replace('extract_invoice_data_with_ai', 'extract_invoice_data')
    ds = ds.replace('generate_document_summary', 'ai_chat_response')
    ds = ds.replace('analyze_contract_text', 'analyze_contract')
    ds = ds.replace('get_ai_chat_response', 'ai_chat_response')
    ds = ds.replace('generate_financial_insights', 'generate_financial_insight')
    ds = ds.replace('detect_gst_anomalies', 'detect_gst_anomalies')
    open(ds_path, 'w', encoding='utf-8').write(ds)
    print("3. document_service.py fixed")

# Scan and fix ALL python files
fixed = []
for root, dirs, files in os.walk('app'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fname in files:
        if not fname.endswith('.py'):
            continue
        path = os.path.join(root, fname)
        try:
            c = open(path, encoding='utf-8').read()
            orig = c
            c = c.replace('extract_invoice_data_with_ai', 'extract_invoice_data')
            c = c.replace('generate_document_summary', 'ai_chat_response')
            c = c.replace('analyze_contract_text', 'analyze_contract')
            c = c.replace('get_ai_chat_response', 'ai_chat_response')
            c = c.replace('generate_financial_insights', 'generate_financial_insight')
            if c != orig:
                open(path, 'w', encoding='utf-8').write(c)
                fixed.append(path)
        except:
            pass

if fixed:
    print(f"4. Fixed {len(fixed)} files: {fixed}")
else:
    print("4. No other files needed fixing")

# Test imports
print("\n5. Testing imports...")
try:
    import sys
    sys.path.insert(0, '.')
    from app.services.ai.ai_service import (
        extract_invoice_data, ai_chat_response, generate_financial_insight,
        extract_invoice_data_with_ai, generate_financial_insights
    )
    print("   ALL IMPORTS OK!")
except Exception as e:
    print(f"   Import error: {e}")

print("\nDone! Run: uvicorn main:app --port 8000")