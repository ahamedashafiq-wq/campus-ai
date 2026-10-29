from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

log = logging.getLogger(__name__)


def email_status() -> dict:
    s = get_settings()
    configured = s.email_provider == "smtp" and bool(s.smtp_host)
    return {"provider": s.email_provider, "configured": configured}


def send_email(to_address: str, subject: str, body: str) -> dict:
    s = get_settings()
    if s.email_provider != "smtp" or not s.smtp_host:
        log.info("Email skipped (provider disabled) to=%s subject=%s", to_address, subject)
        return {"sent": False, "reason": "email_provider_disabled"}
    msg = EmailMessage()
    msg["From"] = s.smtp_from
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            if s.smtp_username:
                smtp.login(s.smtp_username, s.smtp_password)
            smtp.send_message(msg)
        return {"sent": True}
    except OSError as exc:
        log.warning("Email send failed: %s", exc)
        return {"sent": False, "reason": "smtp_error"}
