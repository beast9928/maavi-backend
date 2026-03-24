import os

# Fix document_service.py - update old function names to new ones
ds = open('app/services/document_service.py', encoding='utf-8').read()
ds = ds.replace('extract_invoice_data_with_ai', 'extract_invoice_data')
ds = ds.replace('generate_document_summary', 'ai_chat_response')
open('app/services/document_service.py', 'w', encoding='utf-8').write(ds)
print("1. document_service.py fixed")

# Add aliases to ai_service.py so old imports still work
ai = open('app/services/ai/ai_service.py', encoding='utf-8').read()
if 'extract_invoice_data_with_ai' not in ai:
    ai += '''

# Aliases for backward compatibility
extract_invoice_data_with_ai = extract_invoice_data
generate_document_summary = ai_chat_response
analyze_contract_text = analyze_contract
'''
    open('app/services/ai/ai_service.py', 'w', encoding='utf-8').write(ai)
    print("2. Aliases added to ai_service.py")
else:
    print("2. Aliases already present")

# Check for any other files importing old names
for root, dirs, files in os.walk('app'):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fname in files:
        if not fname.endswith('.py'):
            continue
        path = os.path.join(root, fname)
        try:
            c = open(path, encoding='utf-8').read()
            changed = False
            if 'extract_invoice_data_with_ai' in c:
                c = c.replace('extract_invoice_data_with_ai', 'extract_invoice_data')
                changed = True
            if 'generate_document_summary' in c and 'ai_chat_response' not in c:
                c = c.replace('generate_document_summary', 'ai_chat_response')
                changed = True
            if 'analyze_contract_text' in c:
                c = c.replace('analyze_contract_text', 'analyze_contract')
                changed = True
            if changed:
                open(path, 'w', encoding='utf-8').write(c)
                print(f"3. Fixed: {path}")
        except:
            pass

print("\nAll imports fixed! Now run: uvicorn main:app --port 8000")