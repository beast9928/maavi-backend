env = open('.env', encoding='utf-8').read()

# Get the keys
import re
gemini = re.search(r'GEMINI_API_KEY=(.+)', env)
anthropic = re.search(r'ANTHROPIC_API_KEY=(.+)', env)
groq = re.search(r'GROQ_API_KEY=(.+)', env)
db = re.search(r'DATABASE_URL=(.+)', env)
secret = re.search(r'SECRET_KEY=(.+)', env)
openai = re.search(r'OPENAI_API_KEY=(.+)', env)

# Write clean .env with one AI_PROVIDER
new_env = f"""DATABASE_URL={db.group(1) if db else 'sqlite:///./ai_ca_copilot.db'}
SECRET_KEY={secret.group(1) if secret else 'supersecretkey12345678901234567890'}
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50

# AI Provider (groq is fastest and free)
AI_PROVIDER=groq
GROQ_API_KEY={groq.group(1) if groq else ''}
GEMINI_API_KEY={gemini.group(1) if gemini else ''}
ANTHROPIC_API_KEY={anthropic.group(1) if anthropic else ''}
OPENAI_API_KEY={openai.group(1) if openai else ''}

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@maavi.ai
"""

open('.env', 'w', encoding='utf-8').write(new_env)
print("✅ .env cleaned - using Groq as primary AI provider")
print("Now run: python fix_all.py && uvicorn main:app --port 8000")