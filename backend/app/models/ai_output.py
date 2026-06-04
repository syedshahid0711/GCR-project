"""AI Output model — tracks every AI-generated file."""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class AIOutput(db.Model):
    __tablename__ = "ai_outputs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assignment_id = db.Column(db.String(36), db.ForeignKey("assignments.id"), nullable=False, index=True)

    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # pdf, docx, pptx, txt, py, etc.
    file_size = db.Column(db.Integer)
    content_hash = db.Column(db.String(64))  # SHA-256 for duplicate detection

    confidence = db.Column(db.Float, default=0.0)
    prompt_used = db.Column(db.Text)
    model_used = db.Column(db.String(100), default="gemini-2.0-flash")
    generation_time = db.Column(db.Float)  # seconds

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
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "generation_time": self.generation_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<AIOutput {self.file_type} for assignment {self.assignment_id}>"
