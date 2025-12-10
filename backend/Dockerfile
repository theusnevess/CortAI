# Usamos uma imagem oficial leve do Python 3.11
FROM python:3.11-slim

# Variáveis de ambiente para otimizar o Python no Docker
# PYTHONDONTWRITEBYTECODE: Impede criação de arquivos .pyc inúteis
# PYTHONUNBUFFERED: Garante que os logs apareçam no console em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Diretório de trabalho dentro do container
WORKDIR /app

# --- Instalação de Dependências do Sistema (OS Level) ---
# Atualizamos o apt-get e instalamos:
# 1. gcc e libpq-dev: Necessários para compilar drivers de banco de dados
# 2. ffmpeg: O MOTOR de processamento de vídeo do CortAI
# 3. curl: Útil para healthchecks
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- Instalação de Dependências Python ---
# Copiamos apenas o requirements primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalamos as libs sem cache para manter a imagem leve
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Cópia do Código Fonte ---
# Copiamos todo o conteúdo da pasta backend para dentro do container
COPY . .

# Expomos a porta 8000 (Padrão FastAPI)
EXPOSE 8000

# O comando final será sobrescrito pelo docker-compose, 
# mas deixamos um padrão seguro aqui.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]