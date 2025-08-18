import os
from typing import List, Optional
import aiosmtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()

async def send_email(to: List[str], subject: str, text: Optional[str] = None, html: Optional[str] = None):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    mail_from = os.getenv("MAIL_FROM", user or "no-reply@example.com")
    debug = os.getenv("SMTP_DEBUG", "false").lower() in ("1", "true", "yes")

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

    async def send_via(port_num: int):
        if debug:
            print(f"[SMTP] sending via host={host} port={port_num} user={user}")
        if port_num == 465:
            client = aiosmtplib.SMTP(hostname=host, port=port_num, use_tls=True)
            await client.connect()
            await client.login(user, password)
            resp = await client.send_message(msg)
            await client.quit()
            return resp
        else:
            return await aiosmtplib.send(
                msg,
                hostname=host,
                port=port_num,
                start_tls=True,
                username=user,
                password=password,
            )

    try:
        response = await send_via(port)
    except aiosmtplib.errors.SMTPAuthenticationError as auth_err:
        alt_port = 465 if port != 465 else 587
        if debug:
            print(f"[SMTP] auth failed on {port} ({auth_err}); retrying {alt_port}")
        response = await send_via(alt_port)
    return {"messageId": msg.get("Message-ID", ""), "response": str(response)}
