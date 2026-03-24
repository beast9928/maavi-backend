# -*- coding: utf-8 -*-
# finish_fix.py - Run this to complete the last step that failed
import os
BASE = os.path.dirname(os.path.abspath(__file__))

guide = (
    "MAAVI - QUICK HOSTING GUIDE (Railway.app - FREE)\n"
    "=================================================\n\n"
    "BACKEND (Railway):\n"
    "1. Go to railway.app and login with GitHub\n"
    "2. New Project -> Deploy from GitHub repo\n"
    "3. Push backend to GitHub first:\n"
    "   git init\n"
    "   git add .\n"
    "   git commit -m Maavi backend\n"
    "   git remote add origin YOUR_GITHUB_REPO_URL\n"
    "   git push origin main\n"
    "4. In Railway: New -> GitHub Repo -> select your repo\n"
    "5. Add environment variables (Settings -> Variables):\n"
    "   GROQ_API_KEY = your_new_key\n"
    "   AI_PROVIDER  = groq\n"
    "   SECRET_KEY   = maavi-launch-secret-2026-xK9mP\n"
    "6. Your backend will be live at: https://your-app.railway.app\n\n"
    "FRONTEND (Vercel - FREE):\n"
    "1. In frontend folder create .env file:\n"
    "   REACT_APP_API_URL=https://your-railway-backend.railway.app/api/v1\n"
    "2. Go to vercel.com -> Login -> New Project -> Import frontend folder\n"
    "3. Add env var REACT_APP_API_URL in Vercel settings\n"
    "4. Deploy -> your app is live!\n\n"
    "LOGIN CREDENTIALS FOR DEMO:\n"
    "   demo@cacopilot.in  /  demo@1234\n"
    "   admin@maavi.ai     /  admin@1234\n"
    "   ca@maavi.ai        /  ca@1234\n"
    "   lawyer@maavi.ai    /  law@1234\n\n"
    "TOTAL TIME: ~15 minutes\n"
)

open(os.path.join(BASE, 'HOSTING_GUIDE.txt'), 'w', encoding='utf-8').write(guide)
print("Done! HOSTING_GUIDE.txt created.")
print("\nNow run these 3 commands:")
print("  python seed_users.py")
print("  uvicorn main:app --host 0.0.0.0 --port 8000")
print("  (separate CMD) cd ../frontend && npm start")
