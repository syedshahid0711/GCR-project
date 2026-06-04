"""Activity log model — tracks every action in the system."""
import uuid
from datetime import datetime, timezone
from app.extensions import db


# Action types
ACTION_DETECTED = "DETECTED"
ACTION_CLASSIFIED = "CLASSIFIED"
ACTION_AI_GENERATED = "AI_GENERATED"
ACTION_UPLOADED = "UPLOADED"
ACTION_SUBMITTED = "SUBMITTED"
ACTION_CANCELLED = "CANCELLED"
ACTION_MANUALLY_SUBMITTED = "MANUALLY_SUBMITTED"
ACTION_REMINDER_SENT = "REMINDER_SENT"
ACTION_REVIEW_REQUESTED = "REVIEW_REQUESTED"
ACTION_RESUBMITTED = "RESUBMITTED"
ACTION_VERIFICATION_PASSED = "VERIFICATION_PASSED"
ACTION_VERIFICATION_FAILED = "VERIFICATION_FAILED"

ACTIONS = [
    ACTION_DETECTED, ACTION_CLASSIFIED, ACTION_AI_GENERATED,
    ACTION_UPLOADED, ACTION_SUBMITTED, ACTION_CANCELLED,
    ACTION_MANUALLY_SUBMITTED, ACTION_REMINDER_SENT,
    ACTION_REVIEW_REQUESTED, ACTION_RESUBMITTED,
    ACTION_VERIFICATION_PASSED, ACTION_VERIFICATION_FAILED,
]


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    assignment_id = db.Column(db.String(36), db.ForeignKey("assignments.id"), nullable=True, index=True)

    action = db.Column(db.String(50), nullable=False, index=True)
    details = db.Column(db.JSON, default=dict)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "assignment_id": self.assignment_id,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<ActivityLog {self.action}>"
