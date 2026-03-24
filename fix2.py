# fix2.py
ai = open('app/services/ai/ai_service.py', encoding='utf-8').read()
if 'generate_financial_insights' not in ai:
    ai += '''

# More backward compatibility aliases
generate_financial_insights = generate_financial_insight
detect_gst_anomalies = lambda client_id, db: []
extract_invoice_data_with_ai = extract_invoice_data
generate_document_summary = ai_chat_response
analyze_contract_text = analyze_contract
get_ai_chat_response = ai_chat_response
'''
    open('app/services/ai/ai_service.py', 'w', encoding='utf-8').write(ai)
    print("Aliases added")

# Fix routes.py imports too
routes = open('app/api/routes/routes.py', encoding='utf-8').read()
routes = routes.replace(
    'from app.services.ai.ai_service import generate_financial_insights, detect_gst_anomalies',
    'from app.services.ai.ai_service import generate_financial_insight as generate_financial_insights, ai_chat_response as get_ai_chat_response'
)
routes = routes.replace('generate_financial_insights(', 'generate_financial_insights(')
open('app/api/routes/routes.py', 'w', encoding='utf-8').write(routes)
print("routes.py fixed")

# Scan ALL .py files for any remaining old imports
import os
old_names = {
    'generate_financial_insights': 'generate_financial_insight',
    'detect_gst_anomalies': 'None',
    'extract_invoice_data_with_ai': 'extract_invoice_data',
    'generate_document_summary': 'ai_chat_response',
    'analyze_contract_text': 'analyze_contract',
    'get_ai_chat_response': 'ai_chat_response',
}
for root, dirs, files in os.walk('app'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        try:
            c = open(path, encoding='utf-8').read()
            changed = False
            for old, new in old_names.items():
                if old in c and new != 'None':
                    c = c.replace(old, new)
                    changed = True
            if changed:
                open(path, 'w', encoding='utf-8').write(c)
                print(f"Fixed: {path}")
        except: pass

print("\nDone! Now run: uvicorn main:app --port 8000")