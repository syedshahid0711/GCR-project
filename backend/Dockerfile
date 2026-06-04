FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for OCR and Playwright
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium --with-deps

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
