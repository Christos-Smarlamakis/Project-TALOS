# TALOS v5.8.2 — Docker image
# Multi-tier LLM routing with FastAPI on port 8001.
FROM python:3.11-slim

# Install system build tools.
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory.
WORKDIR /app

# Copy and install dependencies (cached layer).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . .

# Environment variables.
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Expose TALOS FastAPI port (8001; avoids SYNAPSE bus on 8000).
EXPOSE 8001

# Healthcheck via the TALOS health endpoint.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/api/v1/health')" || exit 1

# Default entry point: FastAPI server on port 8001.
CMD ["python", "-m", "uvicorn", "src.api.main_api:app", "--host", "0.0.0.0", "--port", "8001"]