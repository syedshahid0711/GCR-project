"""Database models package."""
from app.models.user import User
from app.models.course import Course
from app.models.assignment import Assignment
from app.models.notification import Notification
from app.models.activity_log import ActivityLog
from app.models.reminder import Reminder
from app.models.ai_output import AIOutput

__all__ = [
    "User",
    "Course",
    "Assignment",
    "Notification",
    "ActivityLog",
    "Reminder",
    "AIOutput",
]
