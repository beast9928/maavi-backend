from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.services.email.email_service import send_compliance_alerts, send_email

alert_router = APIRouter(prefix="/alerts", tags=["Alerts"])

@alert_router.post("/send-compliance")
def trigger_alerts(background_tasks: BackgroundTasks, db: Session=Depends(get_db), current_user=Depends(get_current_user)):
    background_tasks.add_task(send_compliance_alerts, db)
    return {"message": "Compliance alerts queued"}

@alert_router.post("/test-email")
def test_email(current_user=Depends(get_current_user)):
    ok = send_email(current_user.email, "AI Copilot Pro - Test Email", "<h2>Email working!</h2>")
    return {"sent": ok, "to": current_user.email}
