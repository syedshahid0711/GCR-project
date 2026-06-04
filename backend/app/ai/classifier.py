"""AI Classifier — classifies classroom posts using Google Gemini (FREE).

Classification categories:
- DIGITAL_ASSIGNMENT: Solvable digitally, auto-submit
- HANDWRITTEN_ASSIGNMENT: Requires handwritten work, never auto-submit
- GENERAL_ANNOUNCEMENT: Non-actionable announcements
- DEADLINE_UPDATE: Deadline changes
- CLASS_RESCHEDULE: Class timing changes
- EXAM_NOTICE: Exam-related notices
- UNKNOWN: Cannot determine
"""
import json
import re
from flask import current_app
import google.generativeai as genai

from app.models.assignment import (
    CATEGORIES,
    CATEGORY_HANDWRITTEN,
    CATEGORY_DIGITAL,
    CATEGORY_UNKNOWN,
)

# Keywords that strongly indicate handwritten assignments
HANDWRITTEN_KEYWORDS = [
    "write in notebook",
    "write in your notebook",
    "handwritten",
    "hand written",
    "upload handwritten",
    "write and upload image",
    "write and upload",
    "record work",
    "pen and paper",
    "scan and upload",
    "write on paper",
    "photo of your work",
    "image of your work",
    "write in register",
    "write in file",
    "write in copy",
    "practical file",
    "lab manual",
    "write in rough copy",
]


def _detect_handwritten(text):
    """First-pass: keyword-based detection of handwritten assignments.

    Returns True if any handwritten keyword is found.
    """
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in HANDWRITTEN_KEYWORDS)


def classify_assignment(title, description, extracted_text=None):
    """Classify a classroom post using Google Gemini AI.

    Args:
        title: Assignment title
        description: Assignment description/body
        extracted_text: Optional text extracted from attachments via OCR

    Returns:
        dict with keys: category, confidence, reasoning
    """
    full_text = f"{title}\n{description or ''}\n{extracted_text or ''}".strip()

    # ── First pass: keyword detection for handwritten ──
    if _detect_handwritten(full_text):
        return {
            "category": CATEGORY_HANDWRITTEN,
            "confidence": 95.0,
            "reasoning": "Handwritten assignment detected via keyword matching.",
        }

    # ── Second pass: AI classification via Gemini ──
    try:
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            current_app.logger.warning("No GEMINI_API_KEY set — falling back to keyword-only classification")
            return _fallback_classify(full_text)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""You are a classroom post classifier for a student automation system.

Analyze the following classroom post and classify it into EXACTLY ONE of these categories:
- DIGITAL_ASSIGNMENT: An assignment that can be completed digitally (essays, reports, code, presentations, documents)
- HANDWRITTEN_ASSIGNMENT: An assignment requiring handwritten work, notebook entries, or physical submission
- GENERAL_ANNOUNCEMENT: Non-actionable announcement (holidays, seminars, general info)
- DEADLINE_UPDATE: A post about deadline changes or extensions
- CLASS_RESCHEDULE: Class timing or schedule changes
- EXAM_NOTICE: Exam dates, syllabus, or exam-related notices
- UNKNOWN: Cannot determine the category

Also provide:
1. A confidence score from 0 to 100
2. Brief reasoning for your classification
3. The recommended output format IF it's a DIGITAL_ASSIGNMENT (pdf, docx, pptx, txt, code)

POST TITLE: {title}
POST CONTENT: {description or 'No description'}
ATTACHMENT TEXT: {extracted_text or 'No attachments'}

Respond in this exact JSON format only (no markdown, no code blocks):
{{"category": "CATEGORY_NAME", "confidence": 85.0, "reasoning": "Brief explanation", "output_format": "pdf"}}
"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # Clean up markdown code blocks if present
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)

        result = json.loads(response_text)

        # Validate category
        if result.get("category") not in CATEGORIES:
            result["category"] = CATEGORY_UNKNOWN

        # Ensure confidence is a float between 0-100
        result["confidence"] = max(0.0, min(100.0, float(result.get("confidence", 50.0))))

        return result

    except json.JSONDecodeError as e:
        current_app.logger.error(f"Failed to parse Gemini response: {e}")
        return _fallback_classify(full_text)
    except Exception as e:
        current_app.logger.error(f"Gemini classification failed: {e}")
        return _fallback_classify(full_text)


def _fallback_classify(text):
    """Fallback keyword-based classification when AI is unavailable."""
    text_lower = text.lower()

    # Check for assignment keywords
    assignment_keywords = [
        "submit", "assignment", "homework", "project", "report",
        "presentation", "essay", "write a", "create a", "prepare",
        "due date", "deadline", "upload", "solve", "answer",
    ]

    announcement_keywords = [
        "holiday", "no class", "cancelled", "seminar", "event",
        "workshop", "notice", "information", "update", "regarding",
    ]

    exam_keywords = [
        "exam", "test", "quiz", "midterm", "final", "marks",
        "syllabus", "paper", "viva",
    ]

    schedule_keywords = [
        "reschedule", "postpone", "timing change", "new time",
        "class shifted", "moved to",
    ]

    deadline_keywords = [
        "deadline extended", "new deadline", "extension",
        "last date", "due date changed",
    ]

    if any(kw in text_lower for kw in deadline_keywords):
        return {"category": "DEADLINE_UPDATE", "confidence": 60.0, "reasoning": "Keyword match: deadline"}
    if any(kw in text_lower for kw in schedule_keywords):
        return {"category": "CLASS_RESCHEDULE", "confidence": 60.0, "reasoning": "Keyword match: schedule"}
    if any(kw in text_lower for kw in exam_keywords):
        return {"category": "EXAM_NOTICE", "confidence": 60.0, "reasoning": "Keyword match: exam"}
    if any(kw in text_lower for kw in announcement_keywords):
        return {"category": "GENERAL_ANNOUNCEMENT", "confidence": 55.0, "reasoning": "Keyword match: announcement"}
    if any(kw in text_lower for kw in assignment_keywords):
        return {"category": CATEGORY_DIGITAL, "confidence": 55.0, "reasoning": "Keyword match: assignment"}

    return {"category": CATEGORY_UNKNOWN, "confidence": 30.0, "reasoning": "No strong keyword matches found"}
