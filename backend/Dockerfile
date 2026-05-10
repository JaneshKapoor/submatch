FROM python:3.11-slim

# System dependencies: ffmpeg (Whisper audio), Tesseract + Indic packs, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-kan \
    tesseract-ocr-tam \
    tesseract-ocr-tel \
    tesseract-ocr-mar \
    tesseract-ocr-ben \
    tesseract-ocr-guj \
    tesseract-ocr-mal \
    tesseract-ocr-pan \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create temp directory for job files
RUN mkdir -p temp

# Railway injects PORT; fall back to 8000 locally
ENV PORT=8000

EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
