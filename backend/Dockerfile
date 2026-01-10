# =========================================================
# CortAI Backend - Dockerfile (Produção)
# Python 3.11 + FFmpeg + Whisper + Playwright
# =========================================================

FROM python:3.11-slim

# -------------------------
# Variáveis de ambiente
# -------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# -------------------------
# Diretório de trabalho
# -------------------------
WORKDIR /app

# -------------------------
# Dependências do sistema
# -------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build / Python native deps
    build-essential \
    pkg-config \
    libpq-dev \
    curl \
    ca-certificates \

    # FFmpeg + PyAV deps
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavdevice-dev \
    libavfilter-dev \
    libavutil-dev \
    libswresample-dev \
    libswscale-dev \

    # Playwright runtime deps
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \

    && rm -rf /var/lib/apt/lists/*
# -------------------------
# Dependências Python
# -------------------------
COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# -------------------------
# Playwright (Browsers)
# -------------------------
RUN python -m playwright install --with-deps

# -------------------------
# Código da aplicação
# -------------------------
COPY . .

# -------------------------
# Porta exposta (FastAPI)
# -------------------------
EXPOSE 8000

# -------------------------
# Comando padrão
# (sobrescrito pelo docker-compose se necessário)
# -------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
