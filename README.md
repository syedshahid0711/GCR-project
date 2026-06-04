# 🎓 EduAI Assistant

> AI-powered Google Classroom automation platform — 100% FREE

![License](https://img.shields.io/badge/license-MIT-blue)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20Flask%20%2B%20Gemini-blueviolet)
![Cost](https://img.shields.io/badge/cost-%240-brightgreen)

## What It Does

EduAI Assistant connects to your Google Classroom and intelligently manages assignments:

1. **Detects** new assignments, announcements, and deadlines
2. **Classifies** posts as digital assignments, handwritten work, announcements, etc.
3. **Generates** solutions for digital assignments (PDF, DOCX, PPTX, TXT, Code)
4. **Submits** work automatically before deadlines via browser automation
5. **Reminds** you about handwritten work and low-confidence submissions

## 💰 Cost: $0 Forever

| Service | Cost |
|---------|------|
| Google Gemini AI | **Free** (free tier) |
| Google Classroom API | **Free** |
| Google OAuth 2.0 | **Free** |
| SQLite Database | **Free** |
| Tesseract OCR | **Free** (open-source) |
| Playwright | **Free** (open-source) |
| Gmail SMTP | **Free** |
| Telegram Bot | **Free** |

## Tech Stack

- **Frontend**: React 18 + Vite + Tailwind CSS v4 + Zustand
- **Backend**: Python Flask + SQLAlchemy + APScheduler
- **AI**: Google Gemini 2.0 Flash (free tier)
- **Automation**: Playwright Python
- **OCR**: Tesseract (pytesseract)
- **Database**: SQLite (default) / PostgreSQL (optional)

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Google Cloud Console](https://console.cloud.google.com) project with Classroom API enabled
- [Google AI Studio](https://aistudio.google.com) API key (free)

### 1. Clone & Setup Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your Google OAuth and Gemini API keys

pip install -r requirements.txt
playwright install chromium

python run.py
```

### 2. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Open Browser

Visit `http://localhost:5173` — click "Login with Google" to get started.

### 4. Load Demo Data (Optional)

Click the "Load Demo" button on the dashboard, or:
```bash
curl -X POST http://localhost:5000/api/seed
```

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **Google Classroom API**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID**
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:5000/api/auth/google/callback`
5. Download credentials and add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to `.env`
6. Go to **OAuth consent screen** → Add test users (your Google account email)

## Gemini AI Setup

1. Go to [Google AI Studio](https://aistudio.google.com)
2. Click "Get API Key"
3. Create a new API key
4. Add `GEMINI_API_KEY` to `.env`

## Classification Categories

| Category | Action |
|----------|--------|
| `DIGITAL_ASSIGNMENT` | AI solves and auto-submits |
| `HANDWRITTEN_ASSIGNMENT` | Marks pending, sends reminders (never auto-submits) |
| `GENERAL_ANNOUNCEMENT` | Logs and ignores |
| `DEADLINE_UPDATE` | Updates deadline tracking |
| `CLASS_RESCHEDULE` | Logs for reference |
| `EXAM_NOTICE` | Logs for reference |

## Assignment States

`NEW` → `CLASSIFIED` → `IN_PROGRESS` → `SUBMITTED_BY_AI`

Other states: `WAITING_FOR_REVIEW`, `SUBMITTED_MANUALLY`, `CANCELLED`, `OVERDUE`, `HANDWRITTEN_PENDING`

## Safety Rules

- ✅ Never asks for Google passwords (OAuth only)
- ✅ Encrypted token storage (Fernet)
- ✅ Never auto-submits handwritten assignments
- ✅ Detects manual submissions (stops AI workflow)
- ✅ No duplicate submissions
- ✅ Max 3 retry attempts (no infinite loops)
- ✅ Fallback submission 30 min before deadline

## API Endpoints

| Module | Endpoints |
|--------|-----------|
| Auth | `GET /api/auth/google`, `/callback`, `/me`, `POST /logout` |
| Classroom | `GET /api/classroom/courses`, `/sync`, `/announcements` |
| Assignments | `GET/POST /api/assignments/`, `/:id/submit`, `/cancel`, `/resubmit` |
| AI | `POST /api/ai/classify/:id`, `/generate/:id` |
| Notifications | `GET /api/notifications/`, `PATCH /:id/read`, `POST /read-all` |
| Logs | `GET /api/logs/`, `/timeline` |
| Settings | `GET/PATCH /api/settings/` |

## License

MIT
