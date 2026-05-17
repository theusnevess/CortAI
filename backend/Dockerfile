# =========================================================
# CortAI - Dockerfile 
# =========================================================

FROM python:3.11-slim

# -------------------------
# Environment
# -------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# -------------------------
# Workdir
# -------------------------
WORKDIR /app

# -------------------------
# System dependencies
# -------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    git \
    ca-certificates \
    openssl \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Python dependencies
# -------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Local offline TTS runtime used by controlled Docker batches.
ENV PIPER_TTS_VERSION=1.4.1
RUN pip install "piper-tts==${PIPER_TTS_VERSION}" "pathvalidate==3.3.1"

# -------------------------
# Application code
# -------------------------
COPY . .

# -------------------------
# Python path
# -------------------------
ENV PYTHONPATH=/app

# -------------------------
# Default command (debug)
# -------------------------
CMD ["bash"]
