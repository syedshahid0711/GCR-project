"""Google OAuth 2.0 authentication routes.

Flow:
1. Frontend redirects user to GET /api/auth/google
2. Backend redirects to Google consent screen
3. Google redirects back to GET /api/auth/google/callback
4. Backend exchanges code for tokens, creates/updates user
5. Backend sets JWT cookie and redirects to frontend dashboard
"""
import os
import json
import jwt
from datetime import datetime, timedelta, timezone
from flask import redirect, request, jsonify, current_app, make_response
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from cryptography.fernet import Fernet

from app.auth import auth_bp
from app.extensions import db
from app.models.user import User

# Allow HTTP for local development (OAuth requires HTTPS in production)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def _get_fernet():
    """Get Fernet encryption instance for token encryption."""
    key = current_app.config["FERNET_KEY"]
    if not key:
        # Generate a key if not set (dev only)
        key = Fernet.generate_key().decode()
        current_app.logger.warning("No FERNET_KEY set — using generated key (tokens won't persist across restarts)")
    return Fernet(key.encode() if isinstance(key, str) else key)


def _encrypt_token(token):
    """Encrypt an OAuth token for secure storage."""
    if not token:
        return None
    return _get_fernet().encrypt(token.encode()).decode()


def _decrypt_token(encrypted_token):
    """Decrypt a stored OAuth token."""
    if not encrypted_token:
        return None
    try:
        return _get_fernet().decrypt(encrypted_token.encode()).decode()
    except Exception:
        return None


def _create_jwt(user_id):
    """Create a JWT session token."""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def _verify_jwt(token):
    """Verify and decode a JWT session token."""
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """Extract current user from JWT cookie or Authorization header."""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        return None
    user_id = _verify_jwt(token)
    if not user_id:
        return None
    return User.query.get(user_id)


def login_required(f):
    """Decorator to require authentication."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/google")
def google_login():
    """Step 1: Redirect to Google OAuth consent screen."""
    client_config = {
        "web": {
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
            "redirect_uris": [current_app.config["GOOGLE_REDIRECT_URI"]],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=current_app.config["GOOGLE_SCOPES"],
        redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    # Store state in a secure cookie for CSRF protection
    response = make_response(redirect(authorization_url))
    response.set_cookie("oauth_state", state, httponly=True, samesite="Lax", max_age=600)
    return response


@auth_bp.route("/google/callback")
def google_callback():
    """Step 2: Handle OAuth callback, create/update user, set session."""
    state = request.cookies.get("oauth_state")

    client_config = {
        "web": {
            "client_id": current_app.config["GOOGLE_CLIENT_ID"],
            "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
            "redirect_uris": [current_app.config["GOOGLE_REDIRECT_URI"]],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=current_app.config["GOOGLE_SCOPES"],
        state=state,
        redirect_uri=current_app.config["GOOGLE_REDIRECT_URI"],
    )

    # Exchange authorization code for tokens
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Get user info from Google
    oauth2_service = build("oauth2", "v2", credentials=credentials)
    user_info = oauth2_service.userinfo().get().execute()

    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name", email)
    avatar_url = user_info.get("picture")

    # Create or update user
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        db.session.add(user)

    # Update tokens (encrypted)
    user.name = name
    user.avatar_url = avatar_url
    user.access_token = _encrypt_token(credentials.token)
    user.refresh_token = _encrypt_token(credentials.refresh_token) if credentials.refresh_token else user.refresh_token
    user.token_expiry = credentials.expiry

    db.session.commit()

    # Create session JWT
    session_token = _create_jwt(user.id)

    # Redirect to frontend dashboard with session cookie
    frontend_url = current_app.config["FRONTEND_URL"]
    response = make_response(redirect(f"{frontend_url}/dashboard"))
    response.set_cookie(
        "session_token",
        session_token,
        httponly=True,
        samesite="Lax",
        max_age=7 * 24 * 3600,  # 7 days
        secure=False,  # Set to True in production with HTTPS
    )
    response.delete_cookie("oauth_state")
    return response


@auth_bp.route("/me")
@login_required
def get_me():
    """Get current authenticated user profile."""
    return jsonify(request.current_user.to_dict())


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Logout — clear session cookie."""
    response = make_response(jsonify({"message": "Logged out successfully"}))
    response.delete_cookie("session_token")
    return response


@auth_bp.route("/refresh", methods=["POST"])
@login_required
def refresh_token():
    """Refresh the Google access token using the stored refresh token."""
    user = request.current_user
    refresh_tok = _decrypt_token(user.refresh_token)

    if not refresh_tok:
        return jsonify({"error": "No refresh token available. Please re-login."}), 401

    try:
        credentials = Credentials(
            token=None,
            refresh_token=refresh_tok,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=current_app.config["GOOGLE_CLIENT_ID"],
            client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
        )
        credentials.refresh(None)

        user.access_token = _encrypt_token(credentials.token)
        user.token_expiry = credentials.expiry
        db.session.commit()

        return jsonify({"message": "Token refreshed successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to refresh token: {str(e)}"}), 500


def get_user_credentials(user):
    """Helper: Build Google Credentials from stored user tokens.

    Used by other modules (classroom, etc.) to make API calls.
    """
    access_token = _decrypt_token(user.access_token)
    refresh_tok = _decrypt_token(user.refresh_token)

    if not access_token:
        return None

    from flask import current_app
    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_tok,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=current_app.config["GOOGLE_CLIENT_ID"],
        client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
    )

    return credentials
