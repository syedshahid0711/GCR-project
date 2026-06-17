import os
import time
import mimetypes
from flask import current_app
from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.auth.routes import get_user_credentials

MAX_RETRIES = 3

def get_state_path():
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    return os.path.join(upload_dir, "state.json")

def _playwright_turn_in(course_id, coursework_id, drive_link, assignment_title):
    """Navigates Assigned/Missing pages to find assignment by name and turn it in."""
    import os
    from flask import current_app
    
    # Define state_path properly inside the function
    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    state_path = os.path.join(upload_dir, "state.json")
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
            context = browser.new_context(storage_state=state_path)
            page = context.new_page()
            
            # 1. Try ASSIGNED page first
            current_app.logger.info("🤖 [BOT] Checking ASSIGNED page...")
            page.goto("https://classroom.google.com/a/not-turned-in/all")
            page.wait_for_timeout(5000)
            
            assignment_link = page.get_by_role("link", name=assignment_title)
            
            # 2. If not in ASSIGNED, check MISSING page
            if assignment_link.count() == 0:
                current_app.logger.info("🤖 [BOT] Not in ASSIGNED, checking MISSING page...")
                page.goto("https://classroom.google.com/a/missing/all")
                page.wait_for_timeout(5000)
                assignment_link = page.get_by_role("link", name=assignment_title)
            
            # 3. Click the assignment
            if assignment_link.count() > 0:
                current_app.logger.info(f"🤖 [BOT] Found '{assignment_title}'! Clicking...")
                assignment_link.first.click(force=True)
                page.wait_for_timeout(5000)
            else:
                current_app.logger.error("❌ [BOT] Could not find assignment by name.")
                return False
            
            # 4. Perform Submission
            current_app.logger.info("🤖 [BOT] Clicking 'Add or create'...")
            page.get_by_role("button", name="Add or create").first.wait_for(state="visible", timeout=10000)
            page.get_by_role("button", name="Add or create").first.click(force=True)
            
            page.get_by_role("menuitem", name="Link").click(force=True)
            page.get_by_role("textbox").fill(drive_link)
            page.get_by_role("button", name="Add link").click(force=True)
            
            page.wait_for_timeout(4000)
            
            current_app.logger.info("🤖 [BOT] Turning in...")
            page.get_by_role("button", name="Turn in").first.click(force=True)
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Turn in").last.click(force=True)
            
            return True
            
    except Exception as e:
        current_app.logger.error(f"❌ [BOT CRASH]: {e}")
        return False
    finally:
        try: browser.close()
        except: pass

def submit_assignment(assignment, file_path, user):
    """
    1. Uploads file to Drive via API
    2. Hands off to Playwright Bot to Turn In
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    import mimetypes
    
    # --- DEFINE THESE FIRST TO AVOID UnboundLocalError ---
    course_id = assignment.course.google_course_id if assignment.course else None
    coursework_id = assignment.google_coursework_id
    
    if not course_id or not coursework_id:
        return {"success": False, "error": "Missing course or coursework ID", "screenshot_path": None}

    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}", "screenshot_path": None}

    credentials = get_user_credentials(user)

    # --- 1. UPLOAD TO DRIVE (API) ---
    try:
        current_app.logger.info(f"[Submit API] Uploading {os.path.basename(file_path)}...")
        drive_service = build("drive", "v3", credentials=credentials)
        
        mime_type, _ = mimetypes.guess_type(file_path)
        file_metadata = {"name": os.path.basename(file_path)}
        media = MediaFileUpload(file_path, mimetype=mime_type or "application/octet-stream", resumable=True)
        
        drive_file = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id,webViewLink"
        ).execute()
        
        drive_link = drive_file.get("webViewLink")
        current_app.logger.info(f"[Submit API] ✅ Uploaded to Drive.")
        
    except Exception as e:
        return {"success": False, "error": f"Drive upload failed: {str(e)}", "screenshot_path": None}
    
    # --- 2. HAND OFF TO BOT ---
    current_app.logger.info(f"[Submit API] Handing off to bot for {assignment.title}...")
    
    # Now course_id and coursework_id are guaranteed to exist
    success = _playwright_turn_in(course_id, coursework_id, drive_link, assignment.title)
    
    if success:
        return {"success": True, "error": None, "screenshot_path": None}
    else:
        return {"success": False, "error": "Bot failed to turn in assignment.", "screenshot_path": None}