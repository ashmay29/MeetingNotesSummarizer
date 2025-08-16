import os
from typing import List, Optional
import smtplib
from email.message import EmailMessage


async def send_email(to: List[str], subject: str, text: Optional[str] = None, html: Optional[str] = None):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    mail_from = os.getenv("MAIL_FROM", user or "no-reply@example.com")

    if not host or not user or not password:
        raise RuntimeError("SMTP not configured. Please set SMTP_HOST, SMTP_USER, SMTP_PASS in .env")

    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject

    if html:
        msg.set_content(text or "")
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(text or "")

    response = smtplib.send(
        msg,
        hostname=host,
        port=port,
        start_tls=port != 465,
        username=user,
        password=password,
    )
    # aiosmtplib returns a dict-like response tuple (code, message)
    return {"messageId": msg.get("Message-ID", ""), "response": str(response)}
