"""Submission module — assignment submission management and control."""
from flask import Blueprint

submission_bp = Blueprint("submission", __name__, url_prefix="/api/assignments")

from app.submission.routes import *  # noqa: E402, F401, F403
