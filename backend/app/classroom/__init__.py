"""Classroom module — Google Classroom API integration."""
from flask import Blueprint

classroom_bp = Blueprint("classroom", __name__, url_prefix="/api/classroom")

from app.classroom.routes import *  # noqa: E402, F401, F403
