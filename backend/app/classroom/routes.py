"""Google Classroom REST API routes."""
from flask import jsonify, request
from app.classroom import classroom_bp
from app.classroom.service import (
    sync_courses,
    sync_coursework,
    detect_manual_submissions,
    check_returned_assignments,
)
from app.auth.routes import login_required
from app.models.course import Course


@classroom_bp.route("/courses")
@login_required
def list_courses():
    """List all synced courses for the current user."""
    user = request.current_user
    courses = Course.query.filter_by(user_id=user.id, is_active=True).all()
    return jsonify([c.to_dict() for c in courses])


@classroom_bp.route("/courses/<course_id>/work")
@login_required
def list_coursework(course_id):
    """List all assignments for a specific course."""
    user = request.current_user
    course = Course.query.filter_by(id=course_id, user_id=user.id).first()
    if not course:
        return jsonify({"error": "Course not found"}), 404

    from app.models.assignment import Assignment
    assignments = Assignment.query.filter_by(
        user_id=user.id,
        course_id=course.id,
    ).order_by(Assignment.due_date.asc()).all()

    return jsonify([a.to_dict() for a in assignments])


@classroom_bp.route("/sync", methods=["POST"])
@login_required
def trigger_sync():
    """Trigger a full sync of courses and coursework from Google Classroom."""
    user = request.current_user

    try:
        # Sync courses
        courses = sync_courses(user)

        # Sync coursework for each course
        total_new = 0
        for course in courses:
            # Check user course filters
            settings = user.settings or {}
            course_filters = settings.get("course_filters", {})
            if course_filters.get(course.id) is False:
                continue

            new_assignments = sync_coursework(user, course)
            total_new += len(new_assignments)

            # Also detect manual submissions
            detect_manual_submissions(user, course)

            # Check for returned assignments
            check_returned_assignments(user, course)

        return jsonify({
            "message": "Sync completed",
            "courses_synced": len(courses),
            "new_assignments": total_new,
        })

    except Exception as e:
        return jsonify({"error": f"Sync failed: {str(e)}"}), 500


@classroom_bp.route("/announcements")
@login_required
def list_announcements():
    """List announcements classified as non-actionable."""
    user = request.current_user
    from app.models.assignment import Assignment, CATEGORY_ANNOUNCEMENT, CATEGORY_RESCHEDULE

    announcements = Assignment.query.filter(
        Assignment.user_id == user.id,
        Assignment.category.in_([CATEGORY_ANNOUNCEMENT, CATEGORY_RESCHEDULE]),
    ).order_by(Assignment.created_at.desc()).limit(50).all()

    return jsonify([a.to_dict() for a in announcements])
