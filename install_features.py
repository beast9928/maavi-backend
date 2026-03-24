# install_features.py
# Copies all new route files and registers them in main.py
# Run from: C:\ai-ca-copilot\ai-ca-copilot\backend\
import os, shutil, sys

BASE   = os.path.dirname(os.path.abspath(__file__))
ROUTES = os.path.join(BASE, 'app', 'api', 'routes')
os.makedirs(ROUTES, exist_ok=True)

# ── Step 1: Copy all new route files ─────────────────────────────────────────
FILES = [
    "ocr_routes.py",
    "tds_routes.py",
    "itr_routes.py",
    "compliance_calendar_routes.py",
    "client_portal_routes.py",
    "alerts_enhanced_routes.py",
]

print("=== Step 1: Copying route files ===")
for fname in FILES:
    src = os.path.join(BASE, fname)
    dst = os.path.join(ROUTES, fname)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  ✅ {fname}")
    else:
        print(f"  ❌ {fname} NOT FOUND in {BASE} — download it first!")

# ── Step 2: Install required packages ────────────────────────────────────────
print("\n=== Step 2: Installing packages ===")
packages = ["pdfplumber", "python-multipart"]
for pkg in packages:
    ret = os.system(f'"{sys.executable}" -m pip install {pkg} -q')
    print(f"  {'✅' if ret == 0 else '⚠️ '} {pkg}")

# ── Step 3: Rewrite main.py cleanly ──────────────────────────────────────────
print("\n=== Step 3: Updating main.py ===")
main_path = os.path.join(BASE, 'main.py')
main_content = '''"""
AI CA Copilot - FastAPI Application Entry Point
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.database import create_tables

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def try_include(app, module_path, router_name, prefix="/api/v1"):
    try:
        import importlib
        mod    = importlib.import_module(module_path)
        router = getattr(mod, router_name)
        app.include_router(router, prefix=prefix)
        logger.info(f"Loaded: {router_name}")
    except Exception as e:
        logger.warning(f"Skipped {router_name}: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Accounting & Compliance Platform for Indian CA Firms",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core routes
    try_include(app, "app.api.routes.auth",      "router",      "/api/v1")
    try_include(app, "app.api.routes.clients",   "router",      "/api/v1")
    try_include(app, "app.api.routes.documents", "router",      "/api/v1")
    try_include(app, "app.api.routes.routes",    "invoice_router",    "/api/v1")
    try_include(app, "app.api.routes.routes",    "compliance_router", "/api/v1")
    try_include(app, "app.api.routes.routes",    "analytics_router",  "/api/v1")
    try_include(app, "app.api.routes.routes",    "chat_router",       "/api/v1")

    # Feature routes
    try_include(app, "app.api.routes.gst_routes",                  "gst_router")
    try_include(app, "app.api.routes.org_routes",                   "org_router")
    try_include(app, "app.api.routes.alert_routes",                 "alert_router")
    try_include(app, "app.api.routes.law_routes",                   "law_router")
    try_include(app, "app.api.routes.extra_routes",                 "extra_router")
    try_include(app, "app.api.routes.legal_draft_routes",           "draft_router")
    try_include(app, "app.api.routes.legal_research_routes",        "research_router")
    try_include(app, "app.api.routes.financial_routes",             "financial_router")
    try_include(app, "app.api.routes.dashboard_routes",             "dashboard_router")
    try_include(app, "app.api.routes.chat_routes",                  "chat_router")

    # NEW FEATURES
    try_include(app, "app.api.routes.ocr_routes",                   "ocr_router")
    try_include(app, "app.api.routes.tds_routes",                   "tds_router")
    try_include(app, "app.api.routes.itr_routes",                   "itr_router")
    try_include(app, "app.api.routes.compliance_calendar_routes",   "calendar_router")
    try_include(app, "app.api.routes.client_portal_routes",         "portal_router")
    try_include(app, "app.api.routes.alerts_enhanced_routes",       "alerts_enhanced_router")

    if os.path.exists(settings.UPLOAD_DIR):
        app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    @app.on_event("startup")
    async def startup():
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        create_tables()
        logger.info("Database tables created/verified")

    @app.get("/api/health")
    def health_check():
        return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''
open(main_path, 'w', encoding='utf-8').write(main_content)
print("  ✅ main.py rewritten cleanly")

print("""
==========================================
✅ All 6 features installed!

New endpoints added:
  POST /api/v1/ocr/scan-invoice          ← Upload invoice PDF/image
  GET  /api/v1/tds/sections              ← TDS section reference
  POST /api/v1/tds/calculate             ← Calculate TDS amount
  POST /api/v1/tds/entries               ← Create TDS entry
  GET  /api/v1/tds/summary               ← TDS summary
  GET  /api/v1/itr/forms                 ← ITR form guide
  POST /api/v1/itr/calculate-tax         ← Tax calculator
  POST /api/v1/itr/recommend-form        ← Which ITR to file
  GET  /api/v1/calendar/upcoming         ← Upcoming due dates
  GET  /api/v1/calendar/statutory-dates  ← All statutory dates
  POST /api/v1/calendar/events           ← Add custom event
  POST /api/v1/portal/setup              ← Create client portal
  POST /api/v1/portal/login              ← Client login
  GET  /api/v1/portal/dashboard/{id}     ← Client dashboard
  POST /api/v1/alerts/send               ← Send email/WhatsApp
  GET  /api/v1/alerts/setup-guide        ← Alert setup guide

Now run:
  taskkill /F /IM python.exe
  uvicorn main:app --port 8000

Then: http://127.0.0.1:8000/api/docs
==========================================
""")
