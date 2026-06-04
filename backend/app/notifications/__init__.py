"""Notifications module."""
from flask import Blueprint

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")

from app.notifications.routes import *  # noqa: E402, F401, F403
