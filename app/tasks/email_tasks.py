"""Celery email tasks — OTP, password reset."""

from app.tasks.celery_app import celery_app
from app.utils.email import send_email
from app.core.config import get_settings

settings = get_settings()


@celery_app.task(
    name="app.tasks.email_tasks.send_otp_email",
    bind=True,
    max_retries=3,
)
def send_otp_email(self, to_email: str, username: str, otp: str):
    try:
        verify_link = (
            f"{settings.FRONTEND_URL}/verify-email?token={otp}&email={to_email}"
        )
        subject = "Verify your ShlokVault account"
        body = (
            f"Hi {username},\n\n"
            f"Click the link below to verify your account (expires in 10 minutes):\n\n"
            f"    {verify_link}\n\n"
            f"Or paste this code on the verification page:\n\n"
            f"    {otp}\n\n"
            f"— ShlokVault Team"
        )
        send_email(to_email, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(
    name="app.tasks.email_tasks.send_password_reset_email",
    bind=True,
    max_retries=3,
)
def send_password_reset_email(
    self, to_email: str, username: str, reset_token: str, base_url: str
):
    try:
        subject = "Reset your ShlokVault password"
        reset_link = f"{base_url}/reset-password?token={reset_token}"
        body = (
            f"Hi {username},\n\n"
            f"Click the link below to reset your password (expires in 30 minutes):\n\n"
            f"    {reset_link}\n\n"
            f"If you didn't request this, ignore this email.\n\n"
            f"— ShlokVault Team"
        )
        send_email(to_email, subject, body)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
