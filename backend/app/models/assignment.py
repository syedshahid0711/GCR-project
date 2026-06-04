"""Assignment model — core entity tracking every classroom post through its lifecycle."""
import uuid
from datetime import datetime, timezone
from app.extensions import db


# ──── Classification categories ────
CATEGORY_DIGITAL = "DIGITAL_ASSIGNMENT"
CATEGORY_HANDWRITTEN = "HANDWRITTEN_ASSIGNMENT"
CATEGORY_ANNOUNCEMENT = "GENERAL_ANNOUNCEMENT"
CATEGORY_DEADLINE = "DEADLINE_UPDATE"
CATEGORY_RESCHEDULE = "CLASS_RESCHEDULE"
CATEGORY_EXAM = "EXAM_NOTICE"
CATEGORY_UNKNOWN = "UNKNOWN"

CATEGORIES = [
    CATEGORY_DIGITAL,
    CATEGORY_HANDWRITTEN,
    CATEGORY_ANNOUNCEMENT,
    CATEGORY_DEADLINE,
    CATEGORY_RESCHEDULE,
    CATEGORY_EXAM,
    CATEGORY_UNKNOWN,
]

# ──── Assignment states ────
STATE_NEW = "NEW"
STATE_CLASSIFIED = "CLASSIFIED"
STATE_IN_PROGRESS = "IN_PROGRESS"
STATE_WAITING_REVIEW = "WAITING_FOR_REVIEW"
STATE_SUBMITTED_AI = "SUBMITTED_BY_AI"
STATE_SUBMITTED_MANUAL = "SUBMITTED_MANUALLY"
STATE_CANCELLED = "CANCELLED"
STATE_OVERDUE = "OVERDUE"
STATE_HANDWRITTEN = "HANDWRITTEN_PENDING"

STATES = [
    STATE_NEW,
    STATE_CLASSIFIED,
    STATE_IN_PROGRESS,
    STATE_WAITING_REVIEW,
    STATE_SUBMITTED_AI,
    STATE_SUBMITTED_MANUAL,
    STATE_CANCELLED,
    STATE_OVERDUE,
    STATE_HANDWRITTEN,
]


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, index=True)
    course_id = db.Column(db.String(36), db.ForeignKey("courses.id"), nullable=False, index=True)
    google_coursework_id = db.Column(db.String(255), nullable=False, index=True)

    title = db.Column(db.String(1000), nullable=False)
    description = db.Column(db.Text)

    # Classification
    category = db.Column(db.String(50), default=CATEGORY_UNKNOWN)
    state = db.Column(db.String(50), default=STATE_NEW, index=True)

    # Deadline
    due_date = db.Column(db.DateTime)
    max_points = db.Column(db.Float)

    # Attachments (JSON array: [{name, url, mime_type}])
    attachments = db.Column(db.JSON, default=list)

    # Extracted content from attachments/OCR
    extracted_text = db.Column(db.Text)

    # AI analysis
    ai_confidence = db.Column(db.Float, default=0.0)
    ai_output_path = db.Column(db.String(500))
    ai_output_type = db.Column(db.String(20))  # pdf, docx, pptx, txt, code

    # Submission tracking
    submission_verified = db.Column(db.Boolean, default=False)
    google_submission_id = db.Column(db.String(255))
    submitted_at = db.Column(db.DateTime)

    # Duplicate detection
    duplicate_of = db.Column(db.String(36), db.ForeignKey("assignments.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Unique per user
    __table_args__ = (
        db.UniqueConstraint("user_id", "google_coursework_id", name="uq_user_coursework"),
    )

    # Relationships
    ai_outputs = db.relationship("AIOutput", backref="assignment", lazy="dynamic", cascade="all, delete-orphan")
    reminders = db.relationship("Reminder", backref="assignment", lazy="dynamic", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="assignment", lazy="dynamic")
    logs = db.relationship("ActivityLog", backref="assignment", lazy="dynamic")

    @property
    def is_overdue(self):
        """Check if assignment is past due."""
        if self.due_date and self.state not in (STATE_SUBMITTED_AI, STATE_SUBMITTED_MANUAL, STATE_CANCELLED):
            due = self.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) > due
        return False

    @property
    def is_submitted(self):
        """Check if assignment has been submitted (by AI or manually)."""
        return self.state in (STATE_SUBMITTED_AI, STATE_SUBMITTED_MANUAL)

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "google_coursework_id": self.google_coursework_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "state": self.state,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "max_points": self.max_points,
            "attachments": self.attachments,
            "ai_confidence": self.ai_confidence,
            "ai_output_path": self.ai_output_path,
            "ai_output_type": self.ai_output_type,
            "submission_verified": self.submission_verified,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "is_overdue": self.is_overdue,
            "is_submitted": self.is_submitted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Assignment {self.title[:50]}>"
