"""Auth module — Google OAuth 2.0 routes."""
from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

from app.auth.routes import *  # noqa: E402, F401, F403
