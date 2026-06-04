"""OCR module — text extraction from images and documents."""
from flask import Blueprint

ocr_bp = Blueprint("ocr", __name__, url_prefix="/api/ocr")
