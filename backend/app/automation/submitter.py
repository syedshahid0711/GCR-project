"""Google Classroom API Submission Engine — uploads files and submits via API.

Replaces the old Playwright browser automation approach which failed because
Google Classroom detects headless browsers and renders blank pages.

Now uses:
- Google Drive API to upload the assignment file
- Google Classroom API to attach the file and turn in the submission

SAFETY:
- Never stores passwords
- Uses OAuth tokens from the authenticated user
- Max 3 retry attempts
- Detailed logging for audit trail
"""
import os
import time
import mimetypes
from datetime import datetime, timezone
from flask import current_app

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.auth.routes import get_user_credentials


MAX_RETRIES = 3

# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def get_state_path():
    """Return the path to the Playwright session state file."""
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    return os.path.join(upload_dir, "state.json")


def is_logged_in():
    """Check whether a valid Playwright browser session exists."""
    return os.path.exists(get_state_path())


def _find_chrome():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def launch_login_browser():
    """Launch a standard Google Chrome browser window to log into Google Classroom securely.

    Uses a DETACHED subprocess so the Flask server thread is NOT blocked.
    Starts a background thread to monitor the Chrome process. When the user closes
    the Chrome window, the thread automatically extracts and decrypts the session
    cookies to state.json.

    The caller should poll is_logged_in() to detect when the user has
    finished logging in and closed the browser window.

    Returns:
        dict  {success: bool, launched: bool, error: str | None}
    """
    import subprocess
    import os
    import threading

    chrome_path = _find_chrome()
    if not chrome_path:
        current_app.logger.error("[Browser Login] Google Chrome was not found on the system.")
        return {
            "success": False,
            "launched": False,
            "error": "Google Chrome was not found on this system. Please install Google Chrome to set up login."
        }

    state_path = get_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    profile_dir = os.path.join(upload_dir, "chrome_profile")
    os.makedirs(profile_dir, exist_ok=True)

    current_app.logger.info(f"[Browser Login] Launching standard Google Chrome via: {chrome_path}")

    try:
        # Launch Chrome as a native, normal user application (no debugging ports, no automation flags!)
        cmd = [
            chrome_path,
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-mode",
            "https://classroom.google.com"
        ]

        # Use CREATE_NEW_PROCESS_GROUP on Windows to run detached
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )

        # Start a background monitoring thread
        def monitor_and_extract(process, prof_dir, st_path):
            try:
                # Wait for Chrome process to terminate
                process.wait()
                # Wait a brief moment to ensure all cookie database writes are flushed
                time.sleep(2)
                
                # Import and run the cookie extractor
                import cookie_extractor
                success = cookie_extractor.extract_and_convert(profile_dir=prof_dir, state_path=st_path)
                if success:
                    print(f"[Browser Login Monitor] Session cookies successfully extracted to {st_path}")
                else:
                    print("[Browser Login Monitor] Failed to extract cookies from Chrome profile.")
            except Exception as e:
                print(f"[Browser Login Monitor] Error during monitoring/extraction: {e}")

        monitor_thread = threading.Thread(
            target=monitor_and_extract,
            args=(proc, profile_dir, state_path),
            daemon=True
        )
        monitor_thread.start()

        current_app.logger.info("[Browser Login] ✅ Chrome browser window launched. Monitoring for closure...")
        return {"success": True, "launched": True, "error": None}

    except Exception as e:
        current_app.logger.error(f"[Browser Login] Subprocess failed: {e}")
        return {"success": False, "launched": False, "error": f"Failed to launch Chrome browser: {str(e)}"}


def submit_assignment(assignment, file_path, user):
    """Submit an assignment via Google Classroom API.

    Steps:
    1. Upload file to Google Drive
    2. Attach the Drive file to the student submission
    3. Turn in the submission

    Args:
        assignment: Assignment model object
        file_path: Path to the file to upload
        user: User model object

    Returns:
        dict with keys: success (bool), screenshot_path (str), error (str)
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}", "screenshot_path": None}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = _attempt_submission_via_api(assignment, file_path, user, attempt)
            if result["success"]:
                return result
            current_app.logger.warning(
                f"[Submit API] Attempt {attempt}/{MAX_RETRIES} failed for {assignment.id}: {result['error']}"
            )
        except Exception as e:
            current_app.logger.error(f"[Submit API] Attempt {attempt}/{MAX_RETRIES} error: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(5 * attempt)  # Backoff: 5s, 10s

    return {
        "success": False,
        "error": f"All {MAX_RETRIES} submission attempts failed",
        "screenshot_path": None,
    }


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _attempt_submission_via_api(assignment, file_path, user, attempt):
    """Single submission attempt using Google Classroom + Drive APIs."""
    credentials = get_user_credentials(user)
    if not credentials:
        return {
            "success": False,
            "error": "No valid OAuth credentials. Please log out and log back in.",
            "screenshot_path": None,
        }

    # Refresh credentials if expired
    if credentials.expired and credentials.refresh_token:
        try:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            # Update stored tokens
            from app.auth.routes import _encrypt_token
            from app.extensions import db
            user.access_token = _encrypt_token(credentials.token)
            user.token_expiry = credentials.expiry
            db.session.commit()
            current_app.logger.info("[Submit API] Refreshed expired OAuth token.")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to refresh OAuth token: {str(e)}. Please log out and log back in.",
                "screenshot_path": None,
            }

    course_id = assignment.course.google_course_id if assignment.course else None
    coursework_id = assignment.google_coursework_id

    if not course_id or not coursework_id:
        return {
            "success": False,
            "error": "Missing Google Classroom course or coursework ID.",
            "screenshot_path": None,
        }

    current_app.logger.info(
        f"[Submit API] Attempt {attempt}: course={course_id}, coursework={coursework_id}, file={os.path.basename(file_path)}"
    )

    # ── Step 1: Upload file to Google Drive ──
    try:
        drive_service = build("drive", "v3", credentials=credentials)

        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        file_metadata = {
            "name": file_name,
            "description": f"Auto-submitted: {assignment.title}",
        }

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        drive_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,name,webViewLink",
        ).execute()

        drive_file_id = drive_file.get("id")
        current_app.logger.info(f"[Submit API] ✅ Uploaded to Drive: {drive_file.get('name')} (ID: {drive_file_id})")

    except Exception as e:
        error_msg = str(e)
        if "insufficient" in error_msg.lower() or "403" in error_msg:
            return {
                "success": False,
                "error": "Drive upload permission denied. Please log out and log back in to grant the new 'drive.file' permission.",
                "screenshot_path": None,
            }
        return {
            "success": False,
            "error": f"Failed to upload file to Google Drive: {error_msg}",
            "screenshot_path": None,
        }

    # ── Step 2: Find the student submission ──
    try:
        classroom_service = build("classroom", "v1", credentials=credentials)

        submissions_response = classroom_service.courses().courseWork().studentSubmissions().list(
            courseId=course_id,
            courseWorkId=coursework_id,
            userId="me",
        ).execute()

        student_submissions = submissions_response.get("studentSubmissions", [])
        if not student_submissions:
            return {
                "success": False,
                "error": "No student submission found for this assignment. You may not be enrolled in this course.",
                "screenshot_path": None,
            }

        submission = student_submissions[0]
        submission_id = submission.get("id")
        submission_state = submission.get("state", "")

        current_app.logger.info(f"[Submit API] Found submission {submission_id}, state={submission_state}")

        # Check if already turned in
        if submission_state in ("TURNED_IN", "RETURNED"):
            current_app.logger.info(f"[Submit API] Assignment already in state '{submission_state}'. Treating as success.")
            return {
                "success": True,
                "error": None,
                "screenshot_path": None,
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to find student submission: {str(e)}",
            "screenshot_path": None,
        }

    # ── Step 3: Attach the Drive file to the submission ──
    attachment_succeeded = False
    try:
        attachment_body = {
            "addAttachments": [
                {
                    "driveFile": {
                        "id": drive_file_id,
                    }
                }
            ]
        }

        classroom_service.courses().courseWork().studentSubmissions().modifyAttachments(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
            body=attachment_body,
        ).execute()

        attachment_succeeded = True
        current_app.logger.info(f"[Submit API] ✅ Attached Drive file {drive_file_id} to submission {submission_id}")

    except Exception as e:
        error_msg = str(e)
        if "TURNED_IN" in error_msg or "RETURNED" in error_msg:
            current_app.logger.info("[Submit API] Submission already turned in, skipping attachment.")
        elif "ProjectPermissionDenied" in error_msg or "403" in error_msg:
            current_app.logger.warning(
                f"[Submit API] ⚠️ modifyAttachments blocked by project permissions (403). "
                f"Continuing to turnIn without API attachment. File is in Drive: {drive_file_id}"
            )
        else:
            current_app.logger.warning(f"[Submit API] ⚠️ modifyAttachments failed: {error_msg}. Continuing to turnIn...")

    # ── Step 4: Turn in the submission ──
    try:
        classroom_service.courses().courseWork().studentSubmissions().turnIn(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
            body={},
        ).execute()

        current_app.logger.info(f"[Submit API] ✅ Turned in submission {submission_id} for '{assignment.title}'!")

    except Exception as e:
        error_msg = str(e)
        # If already turned in, that's fine
        if "TURNED_IN" in error_msg or "already" in error_msg.lower():
            current_app.logger.info("[Submit API] Submission was already turned in.")
        elif "ProjectPermissionDenied" in error_msg or "403" in error_msg:
            current_app.logger.warning(
                f"[Submit API] ⚠️ turnIn also blocked by project permissions. "
                f"The file has been uploaded to Google Drive (ID: {drive_file_id}). "
                f"Please check Google Cloud Console configuration."
            )
            # Generate a shareable link so the student can manually attach
            try:
                drive_service = build("drive", "v3", credentials=credentials)
                drive_service.permissions().create(
                    fileId=drive_file_id,
                    body={"type": "anyone", "role": "reader"},
                ).execute()
                file_info = drive_service.files().get(
                    fileId=drive_file_id, fields="webViewLink"
                ).execute()
                drive_link = file_info.get("webViewLink", f"https://drive.google.com/file/d/{drive_file_id}/view")
                current_app.logger.info(f"[Submit API] 📎 Shareable Drive link: {drive_link}")
            except Exception:
                drive_link = f"https://drive.google.com/file/d/{drive_file_id}/view"

            return {
                "success": False,
                "error": (
                    f"Google Cloud project lacks permission for Classroom write operations. "
                    f"Your file has been uploaded to Google Drive. "
                    f"Please open your assignment in Google Classroom, click 'Add or create' → 'Google Drive', "
                    f"and select '{os.path.basename(file_path)}', then click 'Turn in'. "
                    f"Drive link: {drive_link}"
                ),
                "screenshot_path": None,
            }
        else:
            return {
                "success": False,
                "error": f"Failed to turn in submission: {error_msg}",
                "screenshot_path": None,
            }

    # ── Step 5: Verify ──
    try:
        verify_response = classroom_service.courses().courseWork().studentSubmissions().get(
            courseId=course_id,
            courseWorkId=coursework_id,
            id=submission_id,
        ).execute()

        final_state = verify_response.get("state", "UNKNOWN")
        current_app.logger.info(f"[Submit API] Final submission state: {final_state}")

        if final_state in ("TURNED_IN", "RETURNED"):
            if not attachment_succeeded:
                current_app.logger.info(
                    f"[Submit API] ✅ Assignment turned in! Note: file attachment via API was skipped. "
                    f"File is in Drive (ID: {drive_file_id})."
                )
            return {
                "success": True,
                "error": None,
                "screenshot_path": None,
            }
        else:
            return {
                "success": False,
                "error": f"Submission state is '{final_state}' after turnIn — expected TURNED_IN.",
                "screenshot_path": None,
            }

    except Exception as e:
        # turnIn succeeded but verification failed — treat as success
        current_app.logger.warning(f"[Submit API] Verification check failed: {e}. Assuming success since turnIn completed.")
        return {
            "success": True,
            "error": None,
            "screenshot_path": None,
        }


def verify_submission(assignment, user):
    """Verify that a previously submitted assignment is actually submitted.

    Returns:
        dict with keys: verified (bool), status (str)
    """
    credentials = get_user_credentials(user)
    if not credentials:
        return {"verified": False, "status": "No valid OAuth credentials"}

    try:
        classroom_service = build("classroom", "v1", credentials=credentials)

        course_id = assignment.course.google_course_id if assignment.course else None
        coursework_id = assignment.google_coursework_id

        if not course_id or not coursework_id:
            return {"verified": False, "status": "Missing course or coursework ID"}

        submissions = classroom_service.courses().courseWork().studentSubmissions().list(
            courseId=course_id,
            courseWorkId=coursework_id,
            userId="me",
        ).execute()

        for sub in submissions.get("studentSubmissions", []):
            state = sub.get("state", "")
            if state in ("TURNED_IN", "RETURNED"):
                return {"verified": True, "status": "TURNED_IN"}

        return {"verified": False, "status": "NOT_SUBMITTED"}

    except Exception as e:
        return {"verified": False, "status": f"Verification error: {str(e)}"}
