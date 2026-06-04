"""User model — stores Google OAuth profile and encrypted tokens."""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(500))

    # Encrypted OAuth tokens
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expiry = db.Column(db.DateTime)

    # User settings (JSON)
    settings = db.Column(db.JSON, default=lambda: {
        "auto_submit": True,
        "confidence_threshold": 50,
        "reminder_frequency": "standard",  # standard | aggressive | minimal
        "approval_mode": False,
        "notifications": {
            "browser": True,
            "email": False,
            "telegram": False,
        },
        "course_filters": {},  # {course_id: True/False}
    })

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    courses = db.relationship("Course", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    activity_logs = db.relationship("ActivityLog", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    reminders = db.relationship("Reminder", backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        """Serialize user for API response (never expose tokens)."""
        return {
            "id": self.id,
            "google_id": self.google_id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.email}>"
