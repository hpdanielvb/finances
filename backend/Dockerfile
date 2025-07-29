# Multi-stage build para Backend FastAPI - Railway Production
FROM python:3.11-slim as backend-base

# Instalar dependências do sistema necessárias para Railway
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copiar requirements e instalar dependências Python
COPY --chown=app:app requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY --chown=app:app . .

# Criar diretório para uploads
RUN mkdir -p uploads

# Expor porta (Railway usa PORT environment variable)
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Comando para produção Railway
CMD ["python", "-m", "gunicorn", "server:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001"]