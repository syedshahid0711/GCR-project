"""Notification model — browser, email, and Telegram notifications."""
import uuid
from datetime import datetime, timezone
from app.extensions import db


# Notification types
NOTIF_REMINDER = "REMINDER"
NOTIF_CONFIDENCE = "CONFIDENCE_ALERT"
NOTIF_SUCCESS = "SUBMISSION_SUCCESS"
NOTIF_FAILED = "SUBMISSION_FAILED"
NOTIF_RESUBMIT = "RESUBMISSION_NEEDED"
NOTIF_MANUAL = "MANUAL_DETECTED"
NOTIF_RETURNED = "ASSIGNMENT_RETURNED"

NOTIFICATION_TYPES = [
    NOTIF_REMINDER, NOTIF_CONFIDENCE, NOTIF_SUCCESS,
    NOTIF_FAILED, NOTIF_RESUBMIT, NOTIF_MANUAL, NOTIF_RETURNED,
]

# Notification channels
CHANNEL_BROWSER = "BROWSER"
CHANNEL_EMAIL = "EMAIL"
CHANNEL_TELEGRAM = "TELEGRAM"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    assignment_id = db.Column(db.String(36), db.ForeignKey("assignments.id"), nullable=True)

    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    message = db.Column(db.Text, nullable=False)
    channel = db.Column(db.String(20), default=CHANNEL_BROWSER)
    is_read = db.Column(db.Boolean, default=False, index=True)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "channel": self.channel,
            "is_read": self.is_read,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Notification {self.type}: {self.title[:30]}>"
