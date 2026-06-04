"""Reminder model — smart deadline reminders."""
import uuid
from datetime import datetime, timezone
from app.extensions import db


# Reminder types
REMINDER_TWO_DAYS = "TWO_DAYS"
REMINDER_TWELVE_HOURS = "TWELVE_HOURS"
REMINDER_TWO_HOURS = "TWO_HOURS"
REMINDER_THIRTY_MINUTES = "THIRTY_MINUTES"

REMINDER_TYPES = [
    REMINDER_TWO_DAYS,
    REMINDER_TWELVE_HOURS,
    REMINDER_TWO_HOURS,
    REMINDER_THIRTY_MINUTES,
]


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    assignment_id = db.Column(db.String(36), db.ForeignKey("assignments.id"), nullable=False, index=True)

    trigger_at = db.Column(db.DateTime, nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    job_id = db.Column(db.String(255))  # APScheduler job reference

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
            "trigger_at": self.trigger_at.isoformat() if self.trigger_at else None,
            "type": self.type,
            "is_sent": self.is_sent,
        }

    def __repr__(self):
        return f"<Reminder {self.type} at {self.trigger_at}>"
