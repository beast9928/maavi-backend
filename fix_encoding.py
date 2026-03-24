files = [
    'app/api/routes/law_routes.py',
    'app/services/ai/legal_ai.py',
    'app/models/law.py',
]
for f in files:
    try:
        content = open(f, 'rb').read()
        text = content.decode('utf-8', errors='replace')
        text = text.replace('\x97', '-').replace('\x96', '-').replace('\x93', '"').replace('\x94', '"')
        open(f, 'w', encoding='utf-8').write(text)
        print(f'Fixed: {f}')
    except Exception as e:
        print(f'Error {f}: {e}')
print('Done')