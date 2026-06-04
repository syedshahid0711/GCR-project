"""Notification service — sends browser, email, and Telegram notifications.

All notification channels are FREE:
- Browser: Web Push API (built-in)
- Email: Gmail SMTP (free with Google account)
- Telegram: Telegram Bot API (free)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from flask import current_app

from app.extensions import db
from app.models.notification import (
    Notification,
    CHANNEL_BROWSER, CHANNEL_EMAIL, CHANNEL_TELEGRAM,
)


def create_notification(user, title, message, notif_type, assignment_id=None):
    """Create and send notification through configured channels.

    Args:
        user: User model object
        title: Notification title
        message: Notification body
        notif_type: Notification type constant
        assignment_id: Optional linked assignment ID

    Returns:
        List of created Notification objects
    """
    settings = user.settings or {}
    notif_settings = settings.get("notifications", {})
    created = []

    # Always create browser notification
    browser_notif = Notification(
        user_id=user.id,
        assignment_id=assignment_id,
        type=notif_type,
        title=title,
        message=message,
        channel=CHANNEL_BROWSER,
    )
    db.session.add(browser_notif)
    created.append(browser_notif)

    # Email notification
    if notif_settings.get("email", False):
        try:
            _send_email(user.email, title, message)
            email_notif = Notification(
                user_id=user.id,
                assignment_id=assignment_id,
                type=notif_type,
                title=title,
                message=message,
                channel=CHANNEL_EMAIL,
            )
            db.session.add(email_notif)
            created.append(email_notif)
        except Exception as e:
            current_app.logger.error(f"Email notification failed: {e}")

    # Telegram notification
    if notif_settings.get("telegram", False):
        try:
            telegram_chat_id = settings.get("telegram_chat_id")
            if telegram_chat_id:
                _send_telegram(telegram_chat_id, title, message)
                tg_notif = Notification(
                    user_id=user.id,
                    assignment_id=assignment_id,
                    type=notif_type,
                    title=title,
                    message=message,
                    channel=CHANNEL_TELEGRAM,
                )
                db.session.add(tg_notif)
                created.append(tg_notif)
        except Exception as e:
            current_app.logger.error(f"Telegram notification failed: {e}")

    db.session.commit()
    return created


def _send_email(to_email, subject, body):
    """Send email via Gmail SMTP (free)."""
    smtp_host = current_app.config.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = current_app.config.get("SMTP_PORT", 587)
    smtp_user = current_app.config.get("SMTP_USER")
    smtp_password = current_app.config.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        current_app.logger.warning("SMTP credentials not configured — skipping email")
        return

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = f"[EduAI] {subject}"

    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f23; color: #e0e0e0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: rgba(30,30,60,0.9); border-radius: 12px; padding: 24px; border: 1px solid rgba(100,100,255,0.2);">
            <h2 style="color: #818cf8; margin-top: 0;">🎓 EduAI Assistant</h2>
            <h3 style="color: #c4b5fd;">{subject}</h3>
            <p style="color: #d1d5db; line-height: 1.6;">{body}</p>
            <hr style="border-color: rgba(100,100,255,0.2);">
            <p style="font-size: 12px; color: #6b7280;">This is an automated notification from EduAI Assistant.</p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)


def _send_telegram(chat_id, title, message):
    """Send Telegram message via Bot API (free)."""
    bot_token = current_app.config.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        return

    text = f"🎓 *EduAI Assistant*\n\n*{title}*\n{message}"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }, timeout=10)
