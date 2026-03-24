# alerts_enhanced_routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime, timedelta
from app.db.database import get_db
from app.core.security import get_current_user
from app.models import Client, ComplianceItem
import smtplib, os, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

alerts_enhanced_router = APIRouter(prefix="/alerts", tags=["Alerts"])

# ── Email sender ──────────────────────────────────────────────────────────────
def send_email_alert(to_email: str, subject: str, body_html: str) -> dict:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        return {"status": "skipped", "reason": "SMTP not configured in .env"}

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = smtp_user
        msg["To"]      = to_email
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return {"status": "sent", "to": to_email}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# ── WhatsApp via Twilio ────────────────────────────────────────────────────────
def send_whatsapp_alert(to_phone: str, message: str) -> dict:
    account_sid = os.getenv("TWILIO_SID", "")
    auth_token  = os.getenv("TWILIO_TOKEN", "")
    from_phone  = os.getenv("TWILIO_WHATSAPP", "whatsapp:+14155238886")

    if not account_sid or not auth_token:
        return {"status": "skipped", "reason": "Twilio not configured in .env"}

    try:
        from twilio.rest import Client as TwilioClient
        client = TwilioClient(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_phone,
            to=f"whatsapp:{to_phone}"
        )
        return {"status": "sent", "sid": msg.sid}
    except ImportError:
        return {"status": "skipped", "reason": "pip install twilio"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def make_compliance_email(client_name: str, items: list) -> str:
    rows = ""
    for item in items:
        days  = item.get("days_left", "?")
        color = "#dc2626" if isinstance(days, int) and days <= 3 else \
                "#d97706" if isinstance(days, int) and days <= 7 else "#059669"
        rows += f"""
        <tr>
          <td style='padding:8px 12px;border-bottom:1px solid #f0f0f0'>{item.get('title','')}</td>
          <td style='padding:8px 12px;border-bottom:1px solid #f0f0f0'>{item.get('due_date','')}</td>
          <td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;color:{color};font-weight:600'>{days} days</td>
        </tr>"""
    return f"""
    <html><body style='font-family:Arial,sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto'>
    <div style='background:#1e3a5f;color:white;padding:24px;border-radius:8px 8px 0 0'>
      <h2 style='margin:0'>Compliance Alert</h2>
      <p style='margin:4px 0 0;opacity:0.8'>AI CA Copilot — {datetime.now().strftime('%d %b %Y')}</p>
    </div>
    <div style='background:#f8fafc;padding:24px'>
      <p>Dear <strong>{client_name}</strong>,</p>
      <p>The following compliance deadlines are approaching:</p>
      <table style='width:100%;border-collapse:collapse;background:white;border-radius:8px;overflow:hidden'>
        <tr style='background:#f1f5f9'>
          <th style='padding:10px 12px;text-align:left'>Filing</th>
          <th style='padding:10px 12px;text-align:left'>Due Date</th>
          <th style='padding:10px 12px;text-align:left'>Days Left</th>
        </tr>
        {rows}
      </table>
      <p style='margin-top:16px;font-size:13px;color:#64748b'>
        Please ensure timely filing to avoid penalties. Contact your CA for assistance.
      </p>
    </div>
    </body></html>"""

# ── Routes ─────────────────────────────────────────────────────────────────────
class AlertRequest(BaseModel):
    client_id:   int
    to_email:    Optional[str] = None
    to_phone:    Optional[str] = None
    days_ahead:  int = 7

class BulkAlertRequest(BaseModel):
    days_ahead:   int = 7
    send_email:   bool = True
    send_whatsapp: bool = False

@alerts_enhanced_router.post("/send")
def send_alert(req: AlertRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == req.client_id, Client.ca_user_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    today    = date.today()
    deadline = today + timedelta(days=req.days_ahead)
    items    = db.query(ComplianceItem).filter(
        ComplianceItem.client_id == req.client_id,
        ComplianceItem.due_date <= deadline,
        ComplianceItem.status != "completed"
    ).all() if hasattr(ComplianceItem, 'due_date') else []

    alert_items = [{"title": c.title, "due_date": str(c.due_date) if c.due_date else "", "days_left": (c.due_date - today).days if c.due_date else "?"} for c in items]
    results = {}

    if req.to_email:
        html = make_compliance_email(client.company_name, alert_items)
        results["email"] = send_email_alert(req.to_email, f"Compliance Alert — {client.company_name}", html)

    if req.to_phone:
        msg_lines = [f"*Compliance Alert — {client.company_name}*\n"]
        for item in alert_items:
            msg_lines.append(f"• {item['title']}: {item['due_date']} ({item['days_left']} days)")
        msg_lines.append("\nPlease file on time to avoid penalties.")
        results["whatsapp"] = send_whatsapp_alert(req.to_phone, "\n".join(msg_lines))

    return {"client": client.company_name, "items_count": len(alert_items), "results": results}

@alerts_enhanced_router.get("/preview-email/{client_id}")
def preview_email(client_id: int, days_ahead: int = 30, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    client = db.query(Client).filter(Client.id == client_id, Client.ca_user_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    sample_items = [
        {"title": "GSTR-1 Filing",    "due_date": str(date.today() + timedelta(days=5)),  "days_left": 5},
        {"title": "TDS Deposit",      "due_date": str(date.today() + timedelta(days=3)),  "days_left": 3},
        {"title": "Advance Tax Q3",   "due_date": str(date.today() + timedelta(days=15)), "days_left": 15},
    ]
    html = make_compliance_email(client.company_name, sample_items)
    return {"html": html, "client": client.company_name}

@alerts_enhanced_router.get("/setup-guide")
def setup_guide(current_user=Depends(get_current_user)):
    return {
        "email_setup": {
            "steps": [
                "Add to .env: SMTP_HOST=smtp.gmail.com",
                "Add to .env: SMTP_PORT=587",
                "Add to .env: SMTP_USER=your@gmail.com",
                "Add to .env: SMTP_PASS=your-app-password",
                "Gmail: Enable 2FA, then create App Password at myaccount.google.com/apppasswords",
            ],
            "providers": {"Gmail": "smtp.gmail.com:587", "Outlook": "smtp-mail.outlook.com:587", "Zoho": "smtp.zoho.in:587"}
        },
        "whatsapp_setup": {
            "steps": [
                "Sign up at twilio.com (free trial available)",
                "Add to .env: TWILIO_SID=your_account_sid",
                "Add to .env: TWILIO_TOKEN=your_auth_token",
                "Add to .env: TWILIO_WHATSAPP=whatsapp:+14155238886",
                "pip install twilio",
                "Join Twilio sandbox: send 'join <keyword>' to +14155238886",
            ]
        }
    }
