"""AI Generator — generates assignment solutions using Google Gemini.

Supports output formats: PDF, DOCX, PPTX, TXT, Code files.
Uses a strict template to output ONLY simple code with no extra text.
"""
import os
import re
import time
import hashlib
from datetime import datetime
from flask import current_app
import google.generativeai as genai

from app.extensions import db
from app.models.ai_output import AIOutput


def generate_assignment(assignment, output_format=None):
    """Generate a solution for a digital assignment using Gemini AI."""
    start_time = time.time()

    if not output_format:
        output_format = _detect_output_format(assignment)

    context = _build_context(assignment)
    content = _generate_with_gemini(context, output_format, assignment.title)

    if not content:
        return None

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = re.sub(r'[^\w\s-]', '', assignment.title)[:50].strip().replace(' ', '_')

    if output_format == "pdf":
        file_path = _create_pdf(content, upload_dir, safe_title, timestamp)
    elif output_format == "docx":
        file_path = _create_docx(content, upload_dir, safe_title, timestamp)
    elif output_format == "pptx":
        file_path = _create_pptx(content, upload_dir, safe_title, timestamp)
    elif output_format == "code":
        file_path = _create_code_file(content, upload_dir, safe_title, timestamp)
    else:  
        file_path = _create_txt(content, upload_dir, safe_title, timestamp)

    generation_time = time.time() - start_time
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    existing_output = AIOutput.query.filter_by(
        assignment_id=assignment.id,
        content_hash=content_hash,
    ).first()

    if existing_output:
        return {
            "file_path": existing_output.file_path,
            "file_type": existing_output.file_type,
            "confidence": existing_output.confidence,
            "generation_time": 0,
            "duplicate": True,
        }

    # Since it's only code now, we give it a default high confidence if content exists
    confidence = 90.0 if content else 0.0
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    
    ai_output = AIOutput(
        assignment_id=assignment.id,
        file_path=file_path,
        file_type=output_format,
        file_size=file_size,
        content_hash=content_hash,
        confidence=confidence,
        prompt_used=context[:2000],  
        model_used="gemini-2.5-flash",
        generation_time=generation_time,
    )
    db.session.add(ai_output)

    assignment.ai_output_path = file_path
    assignment.ai_output_type = output_format
    assignment.ai_confidence = confidence
    db.session.commit()

    return {
        "file_path": file_path,
        "file_type": output_format,
        "confidence": confidence,
        "generation_time": generation_time,
        "duplicate": False,
    }


def _generate_with_gemini(context, output_format, assignment_title):
    """Generate assignment content using Gemini AI with a strict code-only template."""
    try:
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            current_app.logger.error("No GEMINI_API_KEY configured")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # THE ULTRA-MINIMAL CODE-ONLY PROMPT
        prompt = (
            f"You are an expert AI student assistant. Generate a solution for this assignment:\n"
            f"{context}\n\n"
            f"STRICT OUTPUT REQUIREMENTS:\n"
            f"1. Generate ONLY the code required to solve the problem.\n"
            f"2. The code MUST be as simple, basic, and beginner-friendly as possible.\n"
            f"3. ABSOLUTELY NO Table of Contents, Introduction, Analysis, Conclusion, or References.\n"
            f"4. ABSOLUTELY NO extra text, explanations, or meta-commentary outside of code comments.\n"
            f"5. Use this exact, minimal structure:\n\n"
            f"# Assignment: {assignment_title}\n\n"
            f"```\n"
            f"[Insert simple code here]\n"
            f"```"
        )

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        current_app.logger.error(f"Gemini generation failed: {e}")
        return None


def _build_context(assignment):
    parts = [
        f"Assignment Title: {assignment.title}",
    ]
    if assignment.description:
        parts.append(f"Instructions: {assignment.description}")
    if assignment.extracted_text:
        parts.append(f"Content from attachments: {assignment.extracted_text}")
    return "\n".join(parts)


def _detect_output_format(assignment):
    text = f"{assignment.title} {assignment.description or ''}".lower()
    if any(kw in text for kw in ["presentation", "ppt", "slides", "powerpoint"]): return "pptx"
    if any(kw in text for kw in ["code", "program", "python", "java", "c++", "algorithm", "function", "html"]): return "code"
    if any(kw in text for kw in ["document", "doc", "report", "essay", "paper"]): return "docx"
    if any(kw in text for kw in ["pdf"]): return "pdf"
    return "docx"


# ---------------------------------------------------------
# FILE CREATION HELPERS
# ---------------------------------------------------------

def _create_docx(content, upload_dir, safe_title, timestamp):
    from docx import Document
    doc = Document()
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line and not line.startswith('```'):
            doc.add_paragraph(line)

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.docx")
    doc.save(file_path)
    return file_path


def _create_code_file(content, upload_dir, safe_title, timestamp):
    if 'def ' in content or 'import ' in content or 'print(' in content: ext = '.py'
    elif '#include' in content or 'int main' in content: ext = '.cpp'
    elif 'public class' in content or 'public static void' in content: ext = '.java'
    elif 'function ' in content or 'const ' in content or 'let ' in content: ext = '.js'
    elif '<html' in content.lower() or '<div' in content.lower(): ext = '.html'
    else: ext = '.txt'

    clean_code = content
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 3:
            clean_code = parts[1]
            if '\n' in clean_code:
                clean_code = clean_code.split('\n', 1)[1]

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}{ext}")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(clean_code.strip())
    return file_path


def _create_txt(content, upload_dir, safe_title, timestamp):
    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.txt")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def _create_pdf(content, upload_dir, safe_title, timestamp):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Courier", size=10) # Using Courier for code

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 8, line[2:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Courier", size=10)
        elif line and not line.startswith('```'):
            safe_line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, safe_line)
        else:
            pdf.ln(2)

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.pdf")
    pdf.output(file_path)
    return file_path


def _create_pptx(content, upload_dir, safe_title, timestamp):
    from pptx import Presentation
    prs = Presentation()
    
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = safe_title.replace('_', ' ')
    
    tf = slide.placeholders[1].text_frame
    tf.text = "Please open the generated .code or .docx file for the code snippet."

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.pptx")
    prs.save(file_path)
    return file_path