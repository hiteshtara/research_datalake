import smtplib
from email.mime.text import MIMEText
import logging

def send_notification(cfg, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = cfg["email"]["sender"]
    msg["To"] = ", ".join(cfg["email"]["recipients"])

    try:
        with smtplib.SMTP(cfg["email"]["smtp_host"], cfg["email"]["smtp_port"]) as s:
            s.send_message(msg)
        logging.info(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Email send failed: {e}")
