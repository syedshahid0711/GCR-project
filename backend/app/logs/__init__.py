"""Logs module — activity log viewing."""
from flask import Blueprint

logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")

from app.logs.routes import *  # noqa: E402, F401, F403
