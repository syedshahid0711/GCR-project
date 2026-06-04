"""AI module — classification and generation using Google Gemini."""
from flask import Blueprint

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

from app.ai.routes import *  # noqa: E402, F401, F403
