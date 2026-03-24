# -*- coding: utf-8 -*-
"""
Maavi - Rebrand + Deployment Prep Script
Renames AI CA Copilot to Maavi AI Copilot Pro everywhere
"""
import os, json, subprocess, sys

BACK = os.path.dirname(os.path.abspath(__file__))
FRONT = os.path.join(BACK, '..', 'frontend')
FRONT_SRC = os.path.join(FRONT, 'src')

print("=" * 55)
print("  MAAVI - REBRAND + DEPLOYMENT PREP")
print("=" * 55)

# ── 1. Update package.json ────────────────────────────────────────────────
print("\n[1] Updating package.json...")
pkg_path = os.path.join(FRONT, 'package.json')
pkg = json.load(open(pkg_path))
pkg['name'] = 'maavi-ai-copilot-pro'
pkg['description'] = 'Maavi AI Copilot Pro - AI-powered platform for CA and Law firms'
json.dump(pkg, open(pkg_path, 'w'), indent=2)
print("   package.json updated")

# ── 2. Update index.html title ────────────────────────────────────────────
print("\n[2] Updating browser title...")
public_html = os.path.join(FRONT, 'public', 'index.html')
if os.path.exists(public_html):
    c = open(public_html, encoding='utf-8').read()
    c = c.replace('<title>React App</title>', '<title>Maavi - AI Copilot Pro</title>')
    c = c.replace('<title>AI CA Copilot</title>', '<title>Maavi - AI Copilot Pro</title>')
    open(public_html, 'w', encoding='utf-8').write(c)
    print("   index.html title updated")

# ── 3. Update AppLayout - app name ────────────────────────────────────────
print("\n[3] Updating app name in sidebar...")
layout = os.path.join(FRONT_SRC, 'components', 'layout', 'AppLayout.jsx')
c = open(layout, encoding='utf-8').read()
c = c.replace('AI CA Copilot', 'Maavi').replace('ai-ca-copilot', 'maavi').replace('AI Ca Copilot', 'Maavi')
open(layout, 'w', encoding='utf-8').write(c)
print("   Sidebar name updated to Maavi")

# ── 4. Update Login page ──────────────────────────────────────────────────
print("\n[4] Updating login page branding...")
login = os.path.join(FRONT_SRC, 'pages', 'LoginPage.jsx')
if os.path.exists(login):
    c = open(login, encoding='utf-8').read()
    c = c.replace('AI CA Copilot', 'Maavi').replace('Accounting Intelligence Platform', 'AI Copilot Pro for CA & Law Firms').replace('CA Copilot', 'Maavi')
    open(login, 'w', encoding='utf-8').write(c)
    print("   Login page updated")

# ── 5. Update backend app name ────────────────────────────────────────────
print("\n[5] Updating backend app name...")
config = os.path.join(BACK, 'app', 'core', 'config.py')
if os.path.exists(config):
    c = open(config, encoding='utf-8').read()
    c = c.replace('AI CA Copilot', 'Maavi AI Copilot Pro').replace('ai-ca-copilot', 'maavi')
    open(config, 'w', encoding='utf-8').write(c)
    print("   Backend config updated")

# ── 6. Create requirements.txt ────────────────────────────────────────────
print("\n[6] Generating requirements.txt...")
result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True)
reqs = result.stdout
# Filter out problematic packages
filtered = '\n'.join(line for line in reqs.split('\n') if line and not any(x in line.lower() for x in ['paddleocr', 'paddlepaddle', 'pywin32', 'pywinpty']))
open(os.path.join(BACK, 'requirements.txt'), 'w').write(filtered)
print("   requirements.txt generated")

# ── 7. Create .gitignore ──────────────────────────────────────────────────
print("\n[7] Creating .gitignore...")
gitignore = """# Python
__pycache__/
*.py[cod]
venv/
.env
*.db
uploads/

# Node
node_modules/
build/
.env.local

# IDE
.vscode/
.idea/
*.swp
"""
open(os.path.join(BACK, '..', '.gitignore'), 'w').write(gitignore)
print("   .gitignore created")

# ── 8. Create Render deployment config ───────────────────────────────────
print("\n[8] Creating render.yaml for deployment...")
render_yaml = """services:
  - type: web
    name: maavi-backend
    env: python
    rootDir: ai-ca-copilot/backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SECRET_KEY
        value: supersecretkey12345678901234567890
      - key: DEBUG
        value: "False"
      - key: UPLOAD_DIR
        value: ./uploads
      - key: MAX_FILE_SIZE_MB
        value: "50"
"""
open(os.path.join(BACK, '..', 'render.yaml'), 'w').write(render_yaml)
print("   render.yaml created")

# ── 9. Create vercel.json ─────────────────────────────────────────────────
print("\n[9] Creating vercel.json for frontend...")
vercel_json = """{
  "rewrites": [
    { "source": "/(.*)", "destination": "/" }
  ]
}
"""
open(os.path.join(FRONT, 'vercel.json'), 'w').write(vercel_json)
print("   vercel.json created")

# ── 10. Create startup batch file ─────────────────────────────────────────
print("\n[10] Creating start_maavi.bat for easy local startup...")
bat = """@echo off
echo Starting Maavi AI Copilot Pro...
echo.
start cmd /k "cd /d C:\\ai-ca-copilot\\ai-ca-copilot\\backend && venv\\Scripts\\activate && uvicorn main:app --port 8000"
timeout /t 3
start cmd /k "cd /d C:\\ai-ca-copilot\\ai-ca-copilot\\frontend && npm start"
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Opening browser...
timeout /t 8
start http://localhost:3000
"""
open(os.path.join(BACK, '..', 'start_maavi.bat'), 'w').write(bat)
print("   start_maavi.bat created")

print("\n" + "=" * 55)
print("  REBRAND + PREP COMPLETE!")
print("=" * 55)
print("""
What was done:
  ✓ App renamed to Maavi everywhere
  ✓ Browser title updated
  ✓ requirements.txt generated
  ✓ .gitignore created
  ✓ render.yaml for backend deployment
  ✓ vercel.json for frontend deployment
  ✓ start_maavi.bat for easy local startup

Next steps to go LIVE today:
  1. Add OpenAI billing at platform.openai.com/billing
  2. Create GitHub account and push code
  3. Deploy backend on render.com (free)
  4. Deploy frontend on vercel.com (free)
  5. Share URL with trial firms

To start locally just double-click:
  C:\\ai-ca-copilot\\ai-ca-copilot\\start_maavi.bat
""")