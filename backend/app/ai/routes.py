"""AI module REST API routes."""
from flask import jsonify, request
from app.ai import ai_bp
from app.ai.classifier import classify_assignment
from app.ai.generator import generate_assignment
from app.auth.routes import login_required
from app.extensions import db
from app.models.assignment import (
    Assignment, STATE_CLASSIFIED, STATE_IN_PROGRESS,
    STATE_WAITING_REVIEW, CATEGORY_HANDWRITTEN, STATE_HANDWRITTEN,
)
from app.models.activity_log import ActivityLog, ACTION_CLASSIFIED, ACTION_AI_GENERATED, ACTION_REVIEW_REQUESTED


@ai_bp.route("/classify/<assignment_id>", methods=["POST"])
@login_required
def classify(assignment_id):
    """Classify an assignment using AI."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    result = classify_assignment(
        title=assignment.title,
        description=assignment.description,
        extracted_text=assignment.extracted_text,
    )

    # Update assignment
    assignment.category = result["category"]
    assignment.ai_confidence = result.get("confidence", 50.0)

    if result["category"] == CATEGORY_HANDWRITTEN:
        assignment.state = STATE_HANDWRITTEN
    else:
        assignment.state = STATE_CLASSIFIED

    # Log classification
    log = ActivityLog(
        user_id=user.id,
        assignment_id=assignment.id,
        action=ACTION_CLASSIFIED,
        details=result,
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "assignment_id": assignment.id,
        "classification": result,
        "state": assignment.state,
    })


@ai_bp.route("/generate/<assignment_id>", methods=["POST"])
@login_required
def generate(assignment_id):
    """Generate AI solution for a digital assignment."""
    user = request.current_user
    assignment = Assignment.query.filter_by(id=assignment_id, user_id=user.id).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    if assignment.category == CATEGORY_HANDWRITTEN:
        return jsonify({"error": "Cannot generate content for handwritten assignments"}), 400

    # Get optional format override from request
    data = request.get_json(silent=True) or {}
    output_format = data.get("format")

    # Update state
    assignment.state = STATE_IN_PROGRESS
    db.session.commit()

    # Generate
    result = generate_assignment(assignment, output_format)

    if not result:
        return jsonify({"error": "AI generation failed. Please try again."}), 500

    # Log generation
    log = ActivityLog(
        user_id=user.id,
        assignment_id=assignment.id,
        action=ACTION_AI_GENERATED,
        details={
            "file_type": result["file_type"],
            "confidence": result["confidence"],
            "generation_time": result["generation_time"],
        },
    )
    db.session.add(log)

    submitted = False
    submit_error = None

    # Auto-submit IMMEDIATELY after generation if confidence is >= 80%
    if result["confidence"] >= 80:
        from app.automation.submitter import submit_assignment as playwright_submit
        from app.models.assignment import STATE_SUBMITTED_AI
        from app.models.activity_log import ACTION_SUBMITTED
        from app.notifications.service import create_notification
        from app.models.notification import NOTIF_SUCCESS, NOTIF_FAILED

        db.session.commit()  # Save generation output first

        submit_result = playwright_submit(assignment, assignment.ai_output_path, user)

        if submit_result["success"]:
            from datetime import datetime, timezone
            assignment.state = STATE_SUBMITTED_AI
            assignment.submitted_at = datetime.now(timezone.utc)
            assignment.submission_verified = True
            submitted = True

            submit_log = ActivityLog(
                user_id=user.id,
                assignment_id=assignment.id,
                action=ACTION_SUBMITTED,
                details={
                    "method": "immediate_auto_submit",
                    "confidence": result["confidence"],
                    "screenshot": submit_result.get("screenshot_path"),
                },
            )
            db.session.add(submit_log)

            create_notification(
                user,
                f"Submitted: {assignment.title}",
                f"Assignment was auto-submitted immediately after AI generation (Confidence: {result['confidence']:.0f}%).",
                NOTIF_SUCCESS,
                assignment.id,
            )
        else:
            # Submission failed — keep as IN_PROGRESS
            submit_error = submit_result.get("error")
            assignment.state = STATE_IN_PROGRESS
            create_notification(
                user,
                f"Auto-submit failed: {assignment.title}",
                f"Immediate submission failed: {submit_error}. You can retry manually in the portal.",
                NOTIF_FAILED,
                assignment.id,
            )
    else:
        # Under 80% confidence: do NOT submit. Set to WAITING_REVIEW.
        assignment.state = STATE_WAITING_REVIEW
        from app.notifications.service import create_notification
        from app.models.notification import NOTIF_CONFIDENCE
        create_notification(
            user,
            f"Review Required: {assignment.title}",
            f"AI solution ready but confidence score is {result['confidence']:.0f}% (under 80% threshold). Please review and submit manually.",
            NOTIF_CONFIDENCE,
            assignment.id,
        )

    db.session.commit()

    return jsonify({
        "assignment_id": assignment.id,
        "file_path": result["file_path"],
        "file_type": result["file_type"],
        "confidence": result["confidence"],
        "generation_time": result["generation_time"],
        "state": assignment.state,
        "needs_review": result["confidence"] < 80,
        "submitted": submitted,
        "submit_error": submit_error,
    })
