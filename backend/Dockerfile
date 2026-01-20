# =========================================================
# CortAI - Dockerfile 
# =========================================================

FROM python:3.11-slim

# -------------------------
# Environment
# -------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

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
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Python dependencies
# -------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

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
