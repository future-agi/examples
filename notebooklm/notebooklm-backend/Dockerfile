# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libmagic1 \
    libmagic-dev \
    poppler-utils \
    tesseract-ocr \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads chroma_db logs model_cache

# Pre-download models during build
RUN python download_models.py || echo "Model download failed, will retry at runtime"

# Set environment variables
ENV FLASK_APP=src/main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
# Hugging Face settings to reduce download issues
ENV HF_HOME=/app/model_cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV HF_HUB_DISABLE_PROGRESS_BARS=1
ENV HF_HUB_DISABLE_TELEMETRY=1
# Tokenizers settings to prevent fork warnings
ENV TOKENIZERS_PARALLELISM=false
# ChromaDB settings
ENV CHROMA_TELEMETRY=false
ENV ANONYMIZED_TELEMETRY=false

# Expose port
EXPOSE 5050

# Create non-root user
RUN useradd -m -u 1000 notebooklm && chown -R notebooklm:notebooklm /app
USER notebooklm

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5050/api/health || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "1", "--worker-class", "sync", "--timeout", "120", "--preload", "src.main:app"]

CMD ["python", "src/main.py"]