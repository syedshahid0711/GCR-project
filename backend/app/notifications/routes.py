"""Notification REST API routes."""
from flask import jsonify, request
from app.notifications import notifications_bp
from app.auth.routes import login_required
from app.extensions import db
from app.models.notification import Notification


@notifications_bp.route("/", methods=["GET"])
@login_required
def list_notifications():
    """List notifications for the current user."""
    user = request.current_user

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    unread_only = request.args.get("unread_only", "false").lower() == "true"

    query = Notification.query.filter_by(user_id=user.id, channel="BROWSER")
    if unread_only:
        query = query.filter_by(is_read=False)

    query = query.order_by(Notification.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    unread_count = Notification.query.filter_by(user_id=user.id, channel="BROWSER", is_read=False).count()

    return jsonify({
        "notifications": [n.to_dict() for n in paginated.items],
        "total": paginated.total,
        "unread_count": unread_count,
        "page": paginated.page,
        "pages": paginated.pages,
    })


@notifications_bp.route("/<notification_id>/read", methods=["PATCH"])
@login_required
def mark_read(notification_id):
    """Mark a notification as read."""
    user = request.current_user
    notif = Notification.query.filter_by(id=notification_id, user_id=user.id).first()

    if not notif:
        return jsonify({"error": "Notification not found"}), 404

    notif.is_read = True
    db.session.commit()

    return jsonify({"message": "Marked as read"})


@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    user = request.current_user
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()

    return jsonify({"message": "All notifications marked as read"})
