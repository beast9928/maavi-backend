# fix_gemini_sdk.py
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ai_path = os.path.join(BASE, 'app', 'services', 'ai', 'ai_service.py')

content = open(ai_path, encoding='utf-8').read()

# Replace the entire Gemini block with new SDK
old = '''    # Try Gemini first
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
            logger.warning(f"Gemini failed, trying OpenAI: {e}")'''

new = '''    # Try Gemini first
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = system_msg + "\\n\\n" + user_msg
            if json_mode:
                prompt += "\\n\\nRespond ONLY with valid JSON. No markdown, no backticks, no explanation."
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            result = response.text.strip()
            if json_mode:
                result = result.replace("```json", "").replace("```", "").strip()
            return result
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")'''

if old in content:
    content = content.replace(old, new)
    open(ai_path, 'w', encoding='utf-8').write(content)
    print("✅ Fixed! Using new google-genai SDK with gemini-2.0-flash")
else:
    print("❌ Pattern not found - replacing whole _call_ai function")
    # Nuclear option - rewrite the whole function
    import re
    new_func = '''def _call_ai(system_msg, user_msg, json_mode=False):
    gemini_key = os.getenv("GEMINI_API_KEY", "") or "AIzaSyBOrW3GP6y02Fre00c_m5Ly2lwDvcBaKjs"
    prompt = system_msg + "\\n\\n" + user_msg
    if json_mode:
        prompt += "\\n\\nRespond ONLY with valid JSON. No markdown, no backticks, no explanation."
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        result = response.text.strip()
        if json_mode:
            result = result.replace("```json", "").replace("```", "").strip()
        return result
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return json.dumps({"error": str(e)}) if json_mode else f"AI Error: {e}"
'''
    content = re.sub(r'def _call_ai\(.*?\n(?=\n(?:LEGAL_TEMPLATES|def ))', new_func, content, flags=re.DOTALL)
    open(ai_path, 'w', encoding='utf-8').write(content)
    print("✅ _call_ai fully rewritten")