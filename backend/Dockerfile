# Multi-stage build for Backend FastAPI - Railway Production
FROM python:3.11-slim as base-image

# Instalar dependências de sistema necessárias para Railway
# Adicionado tesseract-ocr-por para suporte a português
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

WORKDIR /home/app

# Criar diretório para uploads ANTES de copiar o código e dar permissão
RUN mkdir -p uploads && chown -R app:app uploads

# Copiar requerimentos e instalar dependências Python
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY --chown=app:app . .

# Mudar para o usuário não-root
USER app

# Health check usando a variável de ambiente PORT (padrão 8001 se não definida)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8001}/health || exit 1

# Comando para produção na Railway usando a variável de ambiente PORT
CMD uvicorn server:app --host 0.0.0.0 --port $PORT --workers 4
