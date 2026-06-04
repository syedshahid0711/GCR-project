"""Submission REST API routes — assignment CRUD, submission control, state management."""
import os
from datetime import datetime, timezone
from flask import jsonify, request, send_file, current_app
from app.submission import submission_bp
from app.auth.routes import login_required
from app.extensions import db
from app.models.assignment import (
    Assignment, STATE_NEW, STATE_CLASSIFIED, STATE_IN_PROGRESS,
    STATE_WAITING_REVIEW, STATE_SUBMITTED_AI, STATE_SUBMITTED_MANUAL,
    STATE_CANCELLED, STATE_HANDWRITTEN, CATEGORIES, STATES,
)
from app.models.activity_log import ActivityLog, ACTION_SUBMITTED, ACTION_CANCELLED
from app.models.course import Course


@submission_bp.route("/", methods=["GET"])
@login_required
def list_assignments():
    """List all assignments with optional filters."""
    user = request.current_user

    query = Assignment.query.filter_by(user_id=user.id)

    # Filter by state
    state = request.args.get("state")
    if state and state in STATES:
        query = query.filter_by(state=state)

    # Filter by category
    category = request.args.get("category")
    if category and category in CATEGORIES:
        query = query.filter_by(category=category)

    # Filter by course
    course_id = request.args.get("course_id")
    if course_id:
        query = query.filter_by(course_id=course_id)

    # Sort
    sort = request.args.get("sort", "due_date")
    if sort == "due_date":
        query = query.order_by(Assignment.due_date.asc().nullslast())
    elif sort == "created_at":
        query = query.order_by(Assignment.created_at.desc())
    elif sort == "confidence":
        query = query.order_by(Assignment.ai_confidence.desc())

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    per_page = min(per_page, 100)  # Max 100 per page

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "assignments": [a.to_dict() for a in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
        "has_next": paginated.has_next,
    })


@submission_bp.route("/<assignment_id>", methods=["GET"])
@login_required
def get_assignment(assignment_id):
    """Get detailed assignment info."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    data = assignment.to_dict()

    # Include course info
    if assignment.course:
        data["course"] = assignment.course.to_dict()

    # Include AI outputs
    data["ai_outputs"] = [o.to_dict() for o in assignment.ai_outputs.all()]

    # Include logs
    data["activity_logs"] = [
        l.to_dict() for l in assignment.logs.order_by(ActivityLog.created_at.desc()).limit(20).all()
    ]

    # Include reminders
    data["reminders"] = [r.to_dict() for r in assignment.reminders.all()]

    return jsonify(data)


@submission_bp.route("/<assignment_id>/submit", methods=["POST"])
@login_required
def submit_assignment(assignment_id):
    """Trigger submission for an assignment (manual approval)."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.is_submitted:
        return jsonify({"error": "Assignment already submitted"}), 400

    if not assignment.ai_output_path:
        return jsonify({"error": "No AI-generated content to submit"}), 400

    # Attempt submission via Google Classroom API
    from app.automation.submitter import submit_assignment as api_submit
    result = api_submit(assignment, assignment.ai_output_path, user)

    if result["success"]:
        assignment.state = STATE_SUBMITTED_AI
        assignment.submitted_at = datetime.now(timezone.utc)
        assignment.submission_verified = True

        log = ActivityLog(
            user_id=user.id,
            assignment_id=assignment.id,
            action=ACTION_SUBMITTED,
            details={"method": "classroom_api"},
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "message": "Assignment submitted successfully via Google Classroom API",
            "state": assignment.state,
        })
    else:
        return jsonify({
            "error": f"Submission failed: {result.get('error')}",
            "screenshot": result.get("screenshot_path"),
        }), 500


@submission_bp.route("/<assignment_id>/cancel", methods=["POST"])
@login_required
def cancel_assignment(assignment_id):
    """Cancel pending automation for an assignment."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.is_submitted:
        return jsonify({"error": "Cannot cancel — already submitted"}), 400

    assignment.state = STATE_CANCELLED

    # Cancel associated reminders
    from app.models.reminder import Reminder
    Reminder.query.filter_by(assignment_id=assignment.id, is_sent=False).update({"is_sent": True})

    log = ActivityLog(
        user_id=user.id,
        assignment_id=assignment.id,
        action=ACTION_CANCELLED,
        details={"reason": "User cancelled"},
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Assignment automation cancelled", "state": assignment.state})


@submission_bp.route("/<assignment_id>/resubmit", methods=["POST"])
@login_required
def resubmit_assignment(assignment_id):
    """Regenerate and resubmit a returned assignment."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    # Reset state for reprocessing
    assignment.state = STATE_NEW
    assignment.ai_output_path = None
    assignment.ai_output_type = None
    assignment.ai_confidence = 0.0
    assignment.submission_verified = False
    assignment.submitted_at = None

    db.session.commit()

    return jsonify({"message": "Assignment reset for resubmission", "state": assignment.state})


@submission_bp.route("/<assignment_id>/state", methods=["PATCH"])
@login_required
def update_state(assignment_id):
    """Manually update assignment state."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    data = request.get_json()
    new_state = data.get("state")

    if new_state not in STATES:
        return jsonify({"error": f"Invalid state: {new_state}"}), 400

    assignment.state = new_state
    db.session.commit()

    return jsonify({"message": "State updated", "state": assignment.state})


@submission_bp.route("/stats", methods=["GET"])
@login_required
def get_stats():
    """Get dashboard statistics."""
    user = request.current_user

    total = Assignment.query.filter_by(user_id=user.id).count()
    pending = Assignment.query.filter(
        Assignment.user_id == user.id,
        Assignment.state.in_([STATE_NEW, STATE_CLASSIFIED, STATE_IN_PROGRESS, STATE_WAITING_REVIEW]),
    ).count()
    handwritten = Assignment.query.filter_by(user_id=user.id, state=STATE_HANDWRITTEN).count()
    submitted_ai = Assignment.query.filter_by(user_id=user.id, state=STATE_SUBMITTED_AI).count()
    submitted_manual = Assignment.query.filter_by(user_id=user.id, state=STATE_SUBMITTED_MANUAL).count()
    cancelled = Assignment.query.filter_by(user_id=user.id, state=STATE_CANCELLED).count()

    # Upcoming deadlines (next 7 days)
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    upcoming = Assignment.query.filter(
        Assignment.user_id == user.id,
        Assignment.due_date.isnot(None),
        Assignment.due_date > now,
        Assignment.due_date < now + timedelta(days=7),
        ~Assignment.state.in_([STATE_SUBMITTED_AI, STATE_SUBMITTED_MANUAL, STATE_CANCELLED]),
    ).count()

    # Low confidence alerts
    settings = user.settings or {}
    threshold = settings.get("confidence_threshold", 50)
    low_confidence = Assignment.query.filter(
        Assignment.user_id == user.id,
        Assignment.ai_confidence > 0,
        Assignment.ai_confidence < threshold,
        Assignment.state == STATE_WAITING_REVIEW,
    ).count()

    return jsonify({
        "total": total,
        "pending": pending,
        "handwritten_pending": handwritten,
        "submitted_by_ai": submitted_ai,
        "submitted_manually": submitted_manual,
        "cancelled": cancelled,
        "upcoming_deadlines": upcoming,
        "low_confidence_alerts": low_confidence,
    })


@submission_bp.route("/browser-session-status", methods=["GET"])
@login_required
def browser_session_status():
    """Check if the user has a valid saved browser session (state.json)."""
    from app.automation.submitter import is_logged_in
    return jsonify({
        "logged_in": is_logged_in()
    })


@submission_bp.route("/setup-browser-login", methods=["POST"])
@login_required
def setup_browser_login():
    """Launch a headed browser for manual login and save session.
    
    The browser launches as a DETACHED process — this endpoint returns
    immediately.  The frontend should poll /browser-session-status to
    detect when the user has finished logging in.
    """
    from app.automation.submitter import launch_login_browser
    result = launch_login_browser()
    if result.get("launched"):
        return jsonify({
            "message": "Browser window launched! Log in to Google Classroom, then close the window.",
            "success": True,
            "launched": True,
        }), 202
    else:
        return jsonify({"error": result.get("error", "Unknown error"), "success": False}), 400


@submission_bp.route("/import-cookies", methods=["POST"])
@login_required
def import_cookies():
    """Import cookies exported from a browser extension and save as state.json."""
    import os
    import json
    data = request.get_json()
    
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid cookie format. Please paste a valid JSON array of cookies."}), 400

    from app.automation.submitter import get_state_path
    state_path = get_state_path()
    
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    playwright_cookies = []
    for c in data:
        same_site = c.get("sameSite", "Lax")
        if same_site == "no_restriction":
            same_site = "None"
        elif same_site == "unspecified":
            same_site = "Lax"
        else:
            same_site = same_site.capitalize() if same_site else "Lax"
            if same_site not in ("Lax", "Strict", "None"):
                same_site = "Lax"

        cookie_secure = c.get("secure", False)
        if same_site == "None":
            cookie_secure = True

        pw_cookie = {
            "name": c.get("name"),
            "value": c.get("value"),
            "domain": c.get("domain"),
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": cookie_secure,
            "sameSite": same_site
        }
        
        if "expirationDate" in c:
            pw_cookie["expires"] = int(c["expirationDate"])
            
        playwright_cookies.append(pw_cookie)

    state_data = {
        "cookies": playwright_cookies,
        "origins": []
    }

    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
        
        return jsonify({"message": "Cookies imported successfully!", "success": True})
    except Exception as e:
        return jsonify({"error": f"Failed to save cookies: {str(e)}", "success": False}), 500


@submission_bp.route("/<assignment_id>/download", methods=["GET"])
@login_required
def download_assignment_file(assignment_id):
    """Download the AI-generated output file for an assignment."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if not assignment.ai_output_path:
        return jsonify({"error": "No AI-generated file available"}), 404

    # Resolve to an absolute path
    file_path = assignment.ai_output_path
    if not os.path.isabs(file_path):
        file_path = os.path.join(
            current_app.config.get("UPLOAD_FOLDER", "uploads"),
            os.path.basename(file_path),
        )

    # Security: ensure the resolved path is within the uploads folder
    upload_folder = os.path.realpath(current_app.config.get("UPLOAD_FOLDER", "uploads"))
    real_path = os.path.realpath(file_path)
    if not real_path.startswith(upload_folder):
        return jsonify({"error": "Invalid file path"}), 403

    if not os.path.exists(real_path):
        return jsonify({"error": "File not found on disk"}), 404

    # Map file type to MIME
    mime_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "txt": "text/plain",
        "code": "text/plain",
    }
    file_type = assignment.ai_output_type or "txt"
    mime_type = mime_map.get(file_type, "application/octet-stream")

    return send_file(
        real_path,
        mimetype=mime_type,
        as_attachment=False,
        download_name=os.path.basename(real_path),
    )
