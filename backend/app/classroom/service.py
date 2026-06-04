"""Google Classroom API service — fetches courses, coursework, submissions.

Uses the Google Classroom API (completely FREE, no cost).
"""
from datetime import datetime, timezone
from googleapiclient.discovery import build
from flask import current_app

from app.extensions import db
from app.models.course import Course
from app.models.assignment import Assignment, STATE_NEW, STATE_SUBMITTED_MANUAL
from app.models.activity_log import ActivityLog, ACTION_DETECTED, ACTION_MANUALLY_SUBMITTED
from app.auth.routes import get_user_credentials


def _build_classroom_service(user):
    """Build Google Classroom API service for a user."""
    credentials = get_user_credentials(user)
    if not credentials:
        raise ValueError("No valid credentials for user")
    return build("classroom", "v1", credentials=credentials)


def sync_courses(user):
    """Fetch all enrolled courses from Google Classroom and sync to DB.

    Returns list of synced Course objects.
    """
    service = _build_classroom_service(user)
    synced_courses = []

    page_token = None
    while True:
        response = service.courses().list(
            pageSize=100,
            courseStates=["ACTIVE"],
            pageToken=page_token,
        ).execute()

        courses = response.get("courses", [])
        for gc in courses:
            google_course_id = gc.get("id")

            # Upsert course
            course = Course.query.filter_by(
                user_id=user.id,
                google_course_id=google_course_id,
            ).first()

            if not course:
                course = Course(
                    user_id=user.id,
                    google_course_id=google_course_id,
                    name=gc.get("name", "Untitled Course"),
                    section=gc.get("section"),
                )
                db.session.add(course)
            else:
                course.name = gc.get("name", course.name)
                course.section = gc.get("section", course.section)

            # Try to get teacher name
            try:
                teachers = service.courses().teachers().list(
                    courseId=google_course_id
                ).execute()
                teacher_list = teachers.get("teachers", [])
                if teacher_list:
                    course.teacher_name = teacher_list[0].get("profile", {}).get("name", {}).get("fullName")
            except Exception:
                pass

            course.synced_at = datetime.now(timezone.utc)
            synced_courses.append(course)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    db.session.commit()
    return synced_courses


def sync_coursework(user, course):
    """Fetch all coursework for a specific course and detect new assignments.

    Returns list of new Assignment objects.
    """
    service = _build_classroom_service(user)
    new_assignments = []

    page_token = None
    while True:
        response = service.courses().courseWork().list(
            courseId=course.google_course_id,
            pageSize=100,
            pageToken=page_token,
        ).execute()

        coursework_list = response.get("courseWork", [])
        for cw in coursework_list:
            google_cw_id = cw.get("id")

            # Skip if already exists (duplicate detection)
            existing = Assignment.query.filter_by(
                user_id=user.id,
                google_coursework_id=google_cw_id,
            ).first()

            if existing:
                # Update due date if changed
                new_due = _parse_due_date(cw)
                if new_due and existing.due_date != new_due:
                    existing.due_date = new_due
                continue

            # Parse attachments
            attachments = []
            for material in cw.get("materials", []):
                if "driveFile" in material:
                    df = material["driveFile"]["driveFile"]
                    attachments.append({
                        "name": df.get("title", "Untitled"),
                        "url": df.get("alternateLink", ""),
                        "mime_type": df.get("mimeType", ""),
                    })
                elif "link" in material:
                    link = material["link"]
                    attachments.append({
                        "name": link.get("title", "Link"),
                        "url": link.get("url", ""),
                        "mime_type": "text/html",
                    })

            # Create new assignment
            assignment = Assignment(
                user_id=user.id,
                course_id=course.id,
                google_coursework_id=google_cw_id,
                title=cw.get("title", "Untitled"),
                description=cw.get("description", ""),
                due_date=_parse_due_date(cw),
                max_points=cw.get("maxPoints"),
                attachments=attachments,
                state=STATE_NEW,
            )
            db.session.add(assignment)
            new_assignments.append(assignment)

            # Log detection
            log = ActivityLog(
                user_id=user.id,
                assignment_id=assignment.id,
                action=ACTION_DETECTED,
                details={"title": assignment.title, "course": course.name},
            )
            db.session.add(log)

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    db.session.commit()
    return new_assignments


def detect_manual_submissions(user, course):
    """Check Google Classroom for manually submitted assignments.

    If a student submitted an assignment manually in Google Classroom,
    update our state and cancel any pending automation.
    """
    service = _build_classroom_service(user)
    manually_submitted = []

    # Get all assignments for this course that aren't already marked as submitted
    pending_assignments = Assignment.query.filter(
        Assignment.user_id == user.id,
        Assignment.course_id == course.id,
        ~Assignment.state.in_([STATE_SUBMITTED_MANUAL, "SUBMITTED_BY_AI", "CANCELLED"]),
    ).all()

    for assignment in pending_assignments:
        try:
            # Check student submission status
            submissions = service.courses().courseWork().studentSubmissions().list(
                courseId=course.google_course_id,
                courseWorkId=assignment.google_coursework_id,
                userId="me",
            ).execute()

            for sub in submissions.get("studentSubmissions", []):
                state = sub.get("state", "")
                if state in ("TURNED_IN", "RETURNED"):
                    # Student manually submitted!
                    assignment.state = STATE_SUBMITTED_MANUAL
                    assignment.google_submission_id = sub.get("id")
                    assignment.submitted_at = datetime.now(timezone.utc)
                    manually_submitted.append(assignment)

                    # Log manual submission
                    log = ActivityLog(
                        user_id=user.id,
                        assignment_id=assignment.id,
                        action=ACTION_MANUALLY_SUBMITTED,
                        details={"google_state": state},
                    )
                    db.session.add(log)

        except Exception as e:
            current_app.logger.error(f"Error checking submission for {assignment.id}: {e}")

    db.session.commit()
    return manually_submitted


def check_returned_assignments(user, course):
    """Detect assignments returned by the teacher for resubmission."""
    service = _build_classroom_service(user)
    returned = []

    submitted_assignments = Assignment.query.filter(
        Assignment.user_id == user.id,
        Assignment.course_id == course.id,
        Assignment.state == "SUBMITTED_BY_AI",
    ).all()

    for assignment in submitted_assignments:
        try:
            submissions = service.courses().courseWork().studentSubmissions().list(
                courseId=course.google_course_id,
                courseWorkId=assignment.google_coursework_id,
                userId="me",
            ).execute()

            for sub in submissions.get("studentSubmissions", []):
                if sub.get("state") == "RETURNED":
                    assignment.state = STATE_NEW  # Reset for reprocessing
                    returned.append(assignment)

        except Exception as e:
            current_app.logger.error(f"Error checking returned status for {assignment.id}: {e}")

    db.session.commit()
    return returned


def _parse_due_date(coursework):
    """Parse due date from Google Classroom coursework object."""
    due = coursework.get("dueDate")
    due_time = coursework.get("dueTime", {})

    if not due:
        return None

    try:
        year = due.get("year", 2025)
        month = due.get("month", 1)
        day = due.get("day", 1)
        hour = due_time.get("hours", 23)
        minute = due_time.get("minutes", 59)
        return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
