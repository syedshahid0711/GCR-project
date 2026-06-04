"""AI Generator — generates assignment solutions using Google Gemini (FREE).

Supports output formats: PDF, DOCX, PPTX, TXT, Code files.
Uses free libraries for document generation:
- fpdf2 for PDFs
- python-docx for DOCX
- python-pptx for PPTX
"""
import os
import json
import re
import time
import hashlib
from datetime import datetime, timezone
from flask import current_app
import google.generativeai as genai

from app.extensions import db
from app.models.ai_output import AIOutput


def generate_assignment(assignment, output_format=None):
    """Generate a solution for a digital assignment using Gemini AI.

    Args:
        assignment: Assignment model object
        output_format: Desired format (pdf, docx, pptx, txt, code). Auto-detected if None.

    Returns:
        dict with keys: file_path, file_type, confidence, generation_time
    """
    start_time = time.time()

    # Determine output format
    if not output_format:
        output_format = _detect_output_format(assignment)

    # Build context prompt
    context = _build_context(assignment)

    # Generate content using Gemini
    content = _generate_with_gemini(context, output_format)

    if not content:
        return None

    # Create output file
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
    else:  # txt
        file_path = _create_txt(content, upload_dir, safe_title, timestamp)

    generation_time = time.time() - start_time

    # Calculate content hash for duplicate detection
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check for duplicate output
    existing_output = AIOutput.query.filter_by(
        assignment_id=assignment.id,
        content_hash=content_hash,
    ).first()

    if existing_output:
        # Same content already generated
        return {
            "file_path": existing_output.file_path,
            "file_type": existing_output.file_type,
            "confidence": existing_output.confidence,
            "generation_time": 0,
            "duplicate": True,
        }

    # Calculate confidence based on content quality
    confidence = _calculate_confidence(content, assignment)

    # Save AI output record
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    ai_output = AIOutput(
        assignment_id=assignment.id,
        file_path=file_path,
        file_type=output_format,
        file_size=file_size,
        content_hash=content_hash,
        confidence=confidence,
        prompt_used=context[:2000],  # Truncate for storage
        model_used="gemini-2.0-flash",
        generation_time=generation_time,
    )
    db.session.add(ai_output)

    # Update assignment
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


def _build_context(assignment):
    """Build a comprehensive prompt from assignment data."""
    parts = [
        f"Assignment Title: {assignment.title}",
        f"Course: {assignment.course.name if assignment.course else 'Unknown'}",
    ]

    if assignment.description:
        parts.append(f"Instructions: {assignment.description}")

    if assignment.extracted_text:
        parts.append(f"Content from attachments: {assignment.extracted_text}")

    if assignment.max_points:
        parts.append(f"Maximum Points: {assignment.max_points}")

    if assignment.due_date:
        parts.append(f"Due Date: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}")

    return "\n".join(parts)


def _generate_with_gemini(context, output_format):
    """Generate assignment content using Gemini AI."""
    try:
        api_key = current_app.config.get("GEMINI_API_KEY")
        if not api_key:
            current_app.logger.error("No GEMINI_API_KEY configured")
            return None

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        format_instructions = {
            "pdf": "Write a well-structured academic document with clear headings, paragraphs, and conclusions.",
            "docx": "Write a well-structured academic document with clear headings, paragraphs, and conclusions.",
            "pptx": "Create presentation content with slide titles and bullet points. Format each slide as:\n## Slide Title\n- Bullet point 1\n- Bullet point 2",
            "txt": "Write a clear, well-organized text response.",
            "code": "Write clean, well-commented code that solves the problem. Include necessary imports and a main function.",
        }

        prompt = f"""You are an intelligent AI student assistant. Complete the following assignment professionally and accurately.

{context}

OUTPUT REQUIREMENTS:
- Format: {output_format.upper()}
- {format_instructions.get(output_format, format_instructions['txt'])}
- Be thorough and detailed
- Use proper academic language
- Include references if applicable
- Make sure the response is complete and submission-ready

Generate the content now. Do NOT include any meta-commentary about the task — just produce the final content directly."""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        current_app.logger.error(f"Gemini generation failed: {e}")
        return None


def _detect_output_format(assignment):
    """Auto-detect the best output format based on assignment context."""
    text = f"{assignment.title} {assignment.description or ''}".lower()

    if any(kw in text for kw in ["presentation", "ppt", "slides", "powerpoint"]):
        return "pptx"
    if any(kw in text for kw in ["code", "program", "python", "java", "c++", "algorithm", "function"]):
        return "code"
    if any(kw in text for kw in ["document", "doc", "report", "essay", "paper"]):
        return "docx"
    if any(kw in text for kw in ["pdf"]):
        return "pdf"

    # Default to PDF for academic assignments
    return "pdf"


def _calculate_confidence(content, assignment):
    """Calculate confidence score (0-100) based on content quality."""
    score = 50.0  # Base score

    if not content:
        return 0.0

    # Length check — longer content generally means more thorough
    word_count = len(content.split())
    if word_count > 500:
        score += 15
    elif word_count > 200:
        score += 10
    elif word_count > 100:
        score += 5
    elif word_count < 50:
        score -= 15

    # Check if content addresses the title
    title_words = set(assignment.title.lower().split())
    content_lower = content.lower()
    title_coverage = sum(1 for w in title_words if w in content_lower and len(w) > 3) / max(len(title_words), 1)
    score += title_coverage * 20

    # Structure check — headings, paragraphs
    if re.search(r'^#{1,3}\s', content, re.MULTILINE):
        score += 5  # Has headings
    if content.count('\n\n') > 2:
        score += 5  # Has multiple paragraphs

    return max(0.0, min(100.0, score))


def _create_pdf(content, upload_dir, safe_title, timestamp):
    """Create a PDF file from content using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, safe_title.replace('_', ' '), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # Content
    pdf.set_font("Helvetica", size=11)
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 8, line[2:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
        elif line.startswith('## '):
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, line[3:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
        elif line.startswith('### '):
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, line[4:], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
        elif line:
            # Encode to latin-1 safe characters
            safe_line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, safe_line)
        else:
            pdf.ln(3)

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.pdf")
    pdf.output(file_path)
    return file_path


def _create_docx(content, upload_dir, safe_title, timestamp):
    """Create a DOCX file from content using python-docx."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.add_heading(safe_title.replace('_', ' '), 0)

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif line:
            doc.add_paragraph(line)

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.docx")
    doc.save(file_path)
    return file_path


def _create_pptx(content, upload_dir, safe_title, timestamp):
    """Create a PPTX file from content using python-pptx."""
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()

    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    slide.shapes.title.text = safe_title.replace('_', ' ')

    # Parse content into slides
    current_title = ""
    current_bullets = []

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('## ') or line.startswith('# '):
            # Save previous slide
            if current_title and current_bullets:
                _add_content_slide(prs, current_title, current_bullets)
            current_title = line.lstrip('#').strip()
            current_bullets = []
        elif line.startswith('- ') or line.startswith('* '):
            current_bullets.append(line[2:])
        elif line and current_title:
            current_bullets.append(line)

    # Save last slide
    if current_title and current_bullets:
        _add_content_slide(prs, current_title, current_bullets)

    # If no slides were parsed, create a single content slide
    if len(prs.slides) <= 1:
        _add_content_slide(prs, "Content", content.split('\n')[:10])

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.pptx")
    prs.save(file_path)
    return file_path


def _add_content_slide(prs, title, bullets):
    """Add a content slide with title and bullet points."""
    from pptx.util import Inches, Pt

    bullet_layout = prs.slide_layouts[1]  # Title and Content
    slide = prs.slides.add_slide(bullet_layout)
    slide.shapes.title.text = title

    body = slide.placeholders[1]
    tf = body.text_frame
    tf.clear()

    for i, bullet in enumerate(bullets):
        if i == 0:
            tf.text = bullet
        else:
            p = tf.add_paragraph()
            p.text = bullet


def _create_txt(content, upload_dir, safe_title, timestamp):
    """Create a plain text file."""
    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}.txt")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def _create_code_file(content, upload_dir, safe_title, timestamp):
    """Create a code file (auto-detect language)."""
    # Try to detect language from content
    if 'def ' in content or 'import ' in content or 'print(' in content:
        ext = '.py'
    elif '#include' in content or 'int main' in content:
        ext = '.cpp'
    elif 'public class' in content or 'public static void' in content:
        ext = '.java'
    elif 'function ' in content or 'const ' in content or 'let ' in content:
        ext = '.js'
    elif '<html' in content.lower() or '<div' in content.lower():
        ext = '.html'
    else:
        ext = '.py'  # Default to Python

    # Clean markdown code blocks
    content = re.sub(r'^```\w*\n', '', content)
    content = re.sub(r'\n```$', '', content)
    content = content.strip()

    file_path = os.path.join(upload_dir, f"{safe_title}_{timestamp}{ext}")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path
