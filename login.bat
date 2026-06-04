@echo off
echo ==============================================================
echo   EduAI Assistant Google Classroom Login Helper
echo ==============================================================
echo.
echo   This tool will launch a secure, human-like browser window for
echo   you to log in securely without getting blocked by Google.
echo.
echo   Steps:
echo   1. Log in to your Google Account in the opened window.
echo   2. Navigate/load into Google Classroom.
echo   3. Close the browser window when you are logged in.
echo.
echo   Your session will be saved automatically for headless submissions.
echo.
pause
cd /d "%~dp0\backend"
.venv\Scripts\playwright.exe codegen --channel chrome --save-storage=uploads\state.json https://classroom.google.com
echo.
echo   Success! Browser session successfully saved to uploads\state.json.
echo   You can now close this console window.
echo.
pause
