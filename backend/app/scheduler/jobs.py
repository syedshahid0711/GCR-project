"""APScheduler Background Jobs — the brain of the automation system.

Jobs:
1. auto_pipeline_job (every 1 min) — unified pipeline: sync → classify → generate → submit
2. check_deadlines_job (every 1 min) — fallback submit 30 min before deadline
3. send_reminders_job (every 1 min) — fire due reminders
4. check_returned_assignments_job (every 30 min) — detect teacher-returned work
"""
from datetime import datetime, timedelta, timezone
from flask import current_app

from app.extensions import db, scheduler


def _process_single_assignment(assignment, user, app):
    """Process a single NEW assignment through the full pipeline: classify → generate → submit.

    This is the core logic extracted so it can be called both from the
    scheduled pipeline AND from sync_coursework when new assignments arrive.
    """
    from app.models.assignment import (
        Assignment, STATE_NEW, STATE_CLASSIFIED, STATE_IN_PROGRESS,
        STATE_SUBMITTED_AI, STATE_WAITING_REVIEW, STATE_HANDWRITTEN,
        CATEGORY_DIGITAL, CATEGORY_HANDWRITTEN,
    )
    from app.ai.classifier import classify_assignment
    from app.ai.generator import generate_assignment
    from app.models.activity_log import ActivityLog, ACTION_CLASSIFIED, ACTION_AI_GENERATED, ACTION_SUBMITTED
    from app.notifications.service import create_notification
    from app.models.notification import NOTIF_SUCCESS, NOTIF_FAILED, NOTIF_CONFIDENCE

    try:
        # ── Step 1: Extract text from attachments if needed ──
        if assignment.attachments and not assignment.extracted_text:
            try:
                from app.ocr.processor import extract_text_from_url
                extracted_parts = []
                for att in assignment.attachments:
                    text = extract_text_from_url(att.get("url", ""), att.get("mime_type", ""))
                    if text:
                        extracted_parts.append(text)
                assignment.extracted_text = "\n".join(extracted_parts)
            except Exception as e:
                app.logger.warning(f"OCR extraction failed for {assignment.id}: {e}")

        # ── Step 2: Classify ──
        result = classify_assignment(
            assignment.title,
            assignment.description,
            assignment.extracted_text,
        )
        assignment.category = result["category"]
        assignment.ai_confidence = result.get("confidence", 50.0)

        if result["category"] == CATEGORY_HANDWRITTEN:
            assignment.state = STATE_HANDWRITTEN
            _schedule_handwritten_reminders(assignment, user)
            db.session.add(ActivityLog(
                user_id=user.id, assignment_id=assignment.id,
                action=ACTION_CLASSIFIED, details=result,
            ))
            db.session.commit()
            app.logger.info(f"[Pipeline] Handwritten assignment detected: {assignment.title}")
            return
        else:
            assignment.state = STATE_CLASSIFIED

        db.session.add(ActivityLog(
            user_id=user.id, assignment_id=assignment.id,
            action=ACTION_CLASSIFIED, details=result,
        ))
        db.session.commit()
        app.logger.info(f"[Pipeline] Classified '{assignment.title}' as {result['category']}")

        # ── Step 3: Generate AI solution for digital assignments ──
        if result["category"] != CATEGORY_DIGITAL:
            return

        output_format = result.get("output_format")
        gen_result = generate_assignment(assignment, output_format)

        if not gen_result:
            app.logger.error(f"[Pipeline] AI generation failed for {assignment.id}: {assignment.title}")
            return

        db.session.add(ActivityLog(
            user_id=user.id, assignment_id=assignment.id,
            action=ACTION_AI_GENERATED,
            details={"file_type": gen_result["file_type"], "confidence": gen_result["confidence"]},
        ))

        # Schedule deadline reminders
        _schedule_deadline_reminders(assignment, user)

        app.logger.info(
            f"[Pipeline] Generated solution for '{assignment.title}' "
            f"(type={gen_result['file_type']}, confidence={gen_result['confidence']:.0f}%)"
        )

        # ── Step 4: Submit immediately after AI generation completes successfully if confidence is >= 80% ──
        if gen_result["confidence"] >= 80:
            from app.automation.submitter import submit_assignment as playwright_submit

            assignment.state = STATE_IN_PROGRESS
            db.session.commit()

            submit_result = playwright_submit(assignment, assignment.ai_output_path, user)

            if submit_result["success"]:
                assignment.state = STATE_SUBMITTED_AI
                assignment.submitted_at = datetime.now(timezone.utc)
                assignment.submission_verified = True

                db.session.add(ActivityLog(
                    user_id=user.id, assignment_id=assignment.id,
                    action=ACTION_SUBMITTED,
                    details={
                        "method": "immediate_auto_submit",
                        "confidence": gen_result["confidence"],
                        "screenshot": submit_result.get("screenshot_path"),
                    },
                ))
                create_notification(
                    user,
                    f"✅ Submitted: {assignment.title}",
                    f"Assignment was auto-submitted immediately after AI generation (Confidence: {gen_result['confidence']:.0f}%).",
                    NOTIF_SUCCESS, assignment.id,
                )
                app.logger.info(f"[Pipeline] ✅ Submitted '{assignment.title}' successfully!")
            else:
                # Submission failed — keep as IN_PROGRESS so it can be retried manually in the portal
                assignment.state = STATE_IN_PROGRESS
                create_notification(
                    user,
                    f"⚠️ Auto-submit failed: {assignment.title}",
                    f"Immediate submission failed: {submit_result.get('error')}. You can review and retry manually in the portal.",
                    NOTIF_FAILED, assignment.id,
                )
                app.logger.warning(f"[Pipeline] Submission failed for {assignment.id}: {submit_result.get('error')}")
        else:
            # Under 80% confidence: do NOT submit. Set to WAITING_REVIEW.
            assignment.state = STATE_WAITING_REVIEW
            create_notification(
                user,
                f"📝 Review Required: {assignment.title}",
                f"AI solution ready but confidence score is {gen_result['confidence']:.0f}% (under 80% threshold). Please review and submit manually.",
                NOTIF_CONFIDENCE, assignment.id,
            )
            app.logger.info(f"[Pipeline] Assignment '{assignment.title}' requires manual review (confidence={gen_result['confidence']:.0f}%)")

        db.session.commit()

    except Exception as e:
        app.logger.error(f"[Pipeline] Error processing assignment {assignment.id}: {e}")
        db.session.rollback()


def register_jobs(app):
    """Register all background jobs with APScheduler."""

    @scheduler.task("interval", id="auto_pipeline", minutes=1, misfire_grace_time=30)
    def auto_pipeline_job():
        """Unified pipeline: sync classrooms → classify → generate → submit.

        Runs every 1 minute so new assignments are picked up and completed ASAP.
        """
        with app.app_context():
            try:
                from app.models.user import User
                from app.models.assignment import Assignment, STATE_NEW
                from app.classroom.service import sync_courses, sync_coursework, detect_manual_submissions

                users = User.query.all()
                for user in users:
                    if not user.access_token:
                        continue
                    try:
                        # ── Phase 1: Sync all courses & coursework ──
                        courses = sync_courses(user)
                        settings = user.settings or {}
                        course_filters = settings.get("course_filters", {})

                        all_new_assignments = []
                        for course in courses:
                            if course_filters.get(course.id) is False:
                                continue
                            new_from_course = sync_coursework(user, course)
                            all_new_assignments.extend(new_from_course)
                            detect_manual_submissions(user, course)

                        # ── Phase 2: Process each new assignment through the full pipeline ──
                        for assignment in all_new_assignments:
                            app.logger.info(f"[Pipeline] New assignment detected: '{assignment.title}' — starting processing...")
                            _process_single_assignment(assignment, user, app)

                        # ── Phase 3: Also process any leftover NEW assignments (from previous failed runs) ──
                        leftover = Assignment.query.filter_by(
                            user_id=user.id, state=STATE_NEW,
                        ).all()
                        for assignment in leftover:
                            if assignment not in all_new_assignments:
                                app.logger.info(f"[Pipeline] Retrying leftover assignment: '{assignment.title}'")
                                _process_single_assignment(assignment, user, app)

                    except Exception as e:
                        app.logger.error(f"[Pipeline] Failed for user {user.id}: {e}")

            except Exception as e:
                app.logger.error(f"auto_pipeline_job error: {e}")

    @scheduler.task("interval", id="check_deadlines", minutes=1, misfire_grace_time=30)
    def check_deadlines_job():
        """Mark overdue assignments as OVERDUE."""
        with app.app_context():
            try:
                from app.models.assignment import Assignment, STATE_NEW, STATE_CLASSIFIED, STATE_IN_PROGRESS, STATE_WAITING_REVIEW, STATE_HANDWRITTEN, STATE_OVERDUE

                now = datetime.now(timezone.utc)

                # Mark overdue assignments
                overdue = Assignment.query.filter(
                    Assignment.due_date.isnot(None),
                    Assignment.due_date < now,
                    Assignment.state.in_([STATE_NEW, STATE_CLASSIFIED, STATE_IN_PROGRESS, STATE_WAITING_REVIEW, STATE_HANDWRITTEN]),
                ).all()

                if overdue:
                    for a in overdue:
                        a.state = STATE_OVERDUE
                    db.session.commit()
                    app.logger.info(f"[Scheduler] Marked {len(overdue)} assignments as OVERDUE.")

            except Exception as e:
                app.logger.error(f"check_deadlines_job error: {e}")

    @scheduler.task("interval", id="send_reminders", minutes=1, misfire_grace_time=30)
    def send_reminders_job():
        """Send due reminders."""
        with app.app_context():
            try:
                from app.models.reminder import Reminder
                from app.models.assignment import Assignment
                from app.models.user import User
                from app.notifications.service import create_notification
                from app.models.notification import NOTIF_REMINDER

                now = datetime.now(timezone.utc)
                due_reminders = Reminder.query.filter(
                    Reminder.trigger_at <= now,
                    Reminder.is_sent == False,
                ).all()

                for reminder in due_reminders:
                    assignment = Assignment.query.get(reminder.assignment_id)
                    user = User.query.get(reminder.user_id)

                    if not assignment or not user:
                        reminder.is_sent = True
                        continue

                    # Skip if already submitted
                    if assignment.is_submitted:
                        reminder.is_sent = True
                        continue

                    time_left = ""
                    if reminder.type == "TWO_DAYS":
                        time_left = "2 days"
                    elif reminder.type == "TWELVE_HOURS":
                        time_left = "12 hours"
                    elif reminder.type == "TWO_HOURS":
                        time_left = "2 hours"
                    elif reminder.type == "THIRTY_MINUTES":
                        time_left = "30 minutes"

                    create_notification(
                        user,
                        f"Deadline in {time_left}: {assignment.title}",
                        f"Your assignment '{assignment.title}' is due in {time_left}. Current state: {assignment.state}",
                        NOTIF_REMINDER,
                        assignment.id,
                    )

                    reminder.is_sent = True

                db.session.commit()

            except Exception as e:
                app.logger.error(f"send_reminders_job error: {e}")

    @scheduler.task("interval", id="check_returned", minutes=30, misfire_grace_time=120)
    def check_returned_assignments_job():
        """Check for assignments returned by teachers."""
        with app.app_context():
            try:
                from app.models.user import User
                from app.models.course import Course
                from app.classroom.service import check_returned_assignments
                from app.notifications.service import create_notification
                from app.models.notification import NOTIF_RETURNED

                users = User.query.all()
                for user in users:
                    if not user.access_token:
                        continue
                    courses = Course.query.filter_by(user_id=user.id, is_active=True).all()
                    for course in courses:
                        try:
                            returned = check_returned_assignments(user, course)
                            for assignment in returned:
                                create_notification(
                                    user,
                                    f"Assignment returned: {assignment.title}",
                                    "Your teacher has returned this assignment. You may need to resubmit.",
                                    NOTIF_RETURNED,
                                    assignment.id,
                                )
                        except Exception as e:
                            app.logger.error(f"Returned check failed for course {course.id}: {e}")

            except Exception as e:
                app.logger.error(f"check_returned_assignments_job error: {e}")


def _schedule_deadline_reminders(assignment, user):
    """Create reminder entries for an assignment's deadline."""
    if not assignment.due_date:
        return

    from app.models.reminder import Reminder, REMINDER_TWO_DAYS, REMINDER_TWELVE_HOURS, REMINDER_TWO_HOURS, REMINDER_THIRTY_MINUTES

    reminder_offsets = [
        (REMINDER_TWO_DAYS, timedelta(days=2)),
        (REMINDER_TWELVE_HOURS, timedelta(hours=12)),
        (REMINDER_TWO_HOURS, timedelta(hours=2)),
        (REMINDER_THIRTY_MINUTES, timedelta(minutes=30)),
    ]

    due_date = assignment.due_date
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    for reminder_type, offset in reminder_offsets:
        trigger_at = due_date - offset
        if trigger_at > now:
            # Check if reminder already exists
            existing = Reminder.query.filter_by(
                assignment_id=assignment.id,
                type=reminder_type,
            ).first()

            if not existing:
                reminder = Reminder(
                    user_id=user.id,
                    assignment_id=assignment.id,
                    trigger_at=trigger_at.replace(tzinfo=None),
                    type=reminder_type,
                )
                db.session.add(reminder)


def _schedule_handwritten_reminders(assignment, user):
    """Create daily reminders for handwritten assignments until completed."""
    if not assignment.due_date:
        return

    from app.models.reminder import Reminder

    due_date = assignment.due_date
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    days_until_due = (due_date - now).days

    for day in range(1, min(days_until_due + 1, 15)):  # Max 14 daily reminders
        trigger_at = now + timedelta(days=day)
        if trigger_at < due_date:
            reminder = Reminder(
                user_id=user.id,
                assignment_id=assignment.id,
                trigger_at=trigger_at.replace(tzinfo=None),
                type="TWO_DAYS",  # Reuse type for daily reminders
            )
            db.session.add(reminder)
