# Medical Claims Validator Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY app/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY app/ /app/

# Copy PDF rule files (needed for load_rules_example.py)
COPY Humaein_Technical_Rules.pdf /app/
COPY Humaein_Medical_Rules.pdf /app/

# Create necessary directories
RUN mkdir -p /app/uploads /app/vector_store/chroma_db

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh /app/scripts/load_rules_example.py

# Expose FastAPI port
EXPOSE 8000

# Health check - uses the comprehensive /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request, json; response = urllib.request.urlopen('http://localhost:8000/health'); data = json.loads(response.read()); exit(0 if data.get('status') == 'healthy' else 1)" || exit 1

# Use entrypoint script that handles migrations and rule loading
ENTRYPOINT ["/app/docker-entrypoint.sh"]

