"""Course model — mirrors Google Classroom courses."""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    google_course_id = db.Column(db.String(255), nullable=False, index=True)
    name = db.Column(db.String(500), nullable=False)
    section = db.Column(db.String(255))
    teacher_name = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    synced_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    assignments = db.relationship("Assignment", backref="course", lazy="dynamic", cascade="all, delete-orphan")

    # Unique constraint: one course per user per google_course_id
    __table_args__ = (
        db.UniqueConstraint("user_id", "google_course_id", name="uq_user_course"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "google_course_id": self.google_course_id,
            "name": self.name,
            "section": self.section,
            "teacher_name": self.teacher_name,
            "is_active": self.is_active,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }

    def __repr__(self):
        return f"<Course {self.name}>"
