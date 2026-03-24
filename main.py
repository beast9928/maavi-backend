"""
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
