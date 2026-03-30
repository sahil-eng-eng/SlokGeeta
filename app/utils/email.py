"""Email sending utility via SMTP. Called from Celery tasks only."""

import emails
from app.core.config import get_settings

settings = get_settings()


def send_email(to: str, subject: str, html_body: str) -> None:
    message = emails.Message(
        subject=subject,
        html=html_body,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    message.send(
        to=to,
        smtp={
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "tls": True,
        },
    )
