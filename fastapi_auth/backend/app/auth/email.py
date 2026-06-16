import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, token: str) -> None:
    verify_url = f"{settings.BACKEND_URL}/auth/verify-email?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your email"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">
      <h2 style="margin:0 0 16px">Verify your email</h2>
      <p style="color:#444;margin:0 0 24px">
        Click below to activate your account. Link expires in 24 hours.
      </p>
      <a href="{verify_url}"
         style="display:inline-block;padding:12px 28px;background:#000;color:#fff;
                text-decoration:none;border-radius:6px;font-weight:600">
        Verify Email
      </a>
      <p style="color:#999;font-size:13px;margin-top:32px">
        If you didn't register, ignore this email.
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
        logger.info("Verification email sent to %s", to_email)
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", to_email, exc)
