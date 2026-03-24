import smtplib, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta
from app.core.config import settings
logger = logging.getLogger(__name__)

def send_email(to_email, subject, body):
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        logger.warning("Email not configured")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as s:
            s.ehlo(); s.starttls()
            s.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            s.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return False

def send_compliance_alerts(db):
    from app.models import ComplianceItem, ComplianceStatus, Client, User
    today = date.today()
    sent = 0
    for client in db.query(Client).filter(Client.is_active==True).all():
        ca = db.query(User).filter(User.id==client.ca_user_id).first()
        if not ca or not ca.email: continue
        items = db.query(ComplianceItem).filter(ComplianceItem.client_id==client.id,ComplianceItem.status.in_([ComplianceStatus.PENDING,ComplianceStatus.OVERDUE]),ComplianceItem.due_date<=today+timedelta(days=7),ComplianceItem.reminder_sent==False).all()
        if not items: continue
        body = f"<h2>Compliance Alert for {client.company_name}</h2><p>{len(items)} deadline(s) due within 7 days. Please login to AI Copilot Pro to take action.</p>"
        if send_email(ca.email, f"Compliance Alert - {client.company_name}", body):
            for item in items: item.reminder_sent = True
            db.commit()
            sent += 1
    return {"sent": sent}
