"""Flask Application Factory — creates and configures the app."""
import os
from flask import Flask, jsonify

from app.config import config_map
from app.extensions import db, migrate, cors, scheduler as scheduler_ext


def create_app(config_name=None):
    """Create and configure the Flask application.

    Args:
        config_name: 'development' or 'production'. Defaults to FLASK_ENV.

    Returns:
        Configured Flask app instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials=True, origins=[
        app.config.get("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:3000",
        "http://localhost:5173",
    ])

    # Ensure upload directory exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Create database tables
    with app.app_context():
        # Import all models so SQLAlchemy knows about them
        from app.models import User, Course, Assignment, Notification, ActivityLog, Reminder, AIOutput  # noqa: F401
        db.create_all()

    # Initialize scheduler
    scheduler_ext.init_app(app)

    # Register background jobs
    from app.scheduler.jobs import register_jobs
    register_jobs(app)

    # Start scheduler safely
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler_ext.start()
        app.logger.info("Background scheduler started successfully.")

    return app


def _register_blueprints(app):
    """Register all Flask blueprints (API modules)."""
    from app.auth import auth_bp
    from app.classroom import classroom_bp
    from app.ai import ai_bp
    from app.submission import submission_bp
    from app.notifications import notifications_bp
    from app.logs import logs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(classroom_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(logs_bp)

    # Settings routes (inline — small module)
    from flask import Blueprint, request
    from app.auth.routes import login_required

    settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

    @settings_bp.route("/", methods=["GET"])
    @login_required
    def get_settings():
        user = request.current_user
        return jsonify(user.settings or {})

    @settings_bp.route("/", methods=["PATCH"])
    @login_required
    def update_settings():
        user = request.current_user
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        current_settings = user.settings or {}
        # Deep merge settings
        for key, value in data.items():
            if isinstance(value, dict) and isinstance(current_settings.get(key), dict):
                current_settings[key].update(value)
            else:
                current_settings[key] = value

        user.settings = current_settings
        # Force SQLAlchemy to detect the change on JSON column
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "settings")
        db.session.commit()

        return jsonify({"message": "Settings updated", "settings": user.settings})

    app.register_blueprint(settings_bp)

    # Health check
    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "ok", "service": "EduAI Assistant API"})

    # Seed endpoint (development only)
    @app.route("/api/seed", methods=["POST"])
    def seed_data():
        if app.config.get("DEBUG"):
            from app.database.seed import seed_demo_data
            result = seed_demo_data()
            if result:
                return jsonify({"message": "Demo data seeded successfully"})
            return jsonify({"message": "Demo data already exists"})
        return jsonify({"error": "Not available in production"}), 403


def _register_error_handlers(app):
    """Register global error handlers."""

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Access forbidden"}), 403
