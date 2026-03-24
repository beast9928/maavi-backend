# hardfix.py
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ai_path = os.path.join(BASE, 'app', 'services', 'ai', 'ai_service.py')

content = open(ai_path, encoding='utf-8').read()

# Replace the _call_ai function's key reading with hardcoded fallback
old = 'gemini_key = os.getenv("GEMINI_API_KEY", "")'
new = '''gemini_key = os.getenv("GEMINI_API_KEY", "") or "AIzaSyBOrW3GP6y02Fre00c_m5Ly2lwDvcBaKjs"'''

if old in content:
    content = content.replace(old, new)
    open(ai_path, 'w', encoding='utf-8').write(content)
    print("FIXED - key hardcoded as fallback")
else:
    print("Pattern not found - showing first 500 chars of _call_ai:")
    idx = content.find('def _call_ai')
    print(content[idx:idx+500])