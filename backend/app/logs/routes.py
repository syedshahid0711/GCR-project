"""Activity logs REST API routes."""
from flask import jsonify, request
from app.logs import logs_bp
from app.auth.routes import login_required
from app.models.activity_log import ActivityLog, ACTIONS


@logs_bp.route("/", methods=["GET"])
@login_required
def list_logs():
    """List activity logs for the current user."""
    user = request.current_user

    query = ActivityLog.query.filter_by(user_id=user.id)

    # Filter by action type
    action = request.args.get("action")
    if action and action in ACTIONS:
        query = query.filter_by(action=action)

    # Filter by assignment
    assignment_id = request.args.get("assignment_id")
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 30, type=int)
    per_page = min(per_page, 100)

    query = query.order_by(ActivityLog.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "logs": [log.to_dict() for log in paginated.items],
        "total": paginated.total,
        "page": paginated.page,
        "pages": paginated.pages,
        "has_next": paginated.has_next,
    })


@logs_bp.route("/timeline", methods=["GET"])
@login_required
def get_timeline():
    """Get recent activity timeline for the dashboard (last 20 entries)."""
    user = request.current_user

    logs = ActivityLog.query.filter_by(user_id=user.id).order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()

    return jsonify([log.to_dict() for log in logs])
