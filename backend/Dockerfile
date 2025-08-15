# Multi-stage build for Backend FastAPI - Railway Production
FROM python:3.11-slim as base-image

# Instalar dependências de sistema necessárias para Railway, incluindo Tesseract para OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho e usuário não-root para segurança
WORKDIR /app
RUN useradd --create-home app
COPY --chown=app:app . .
RUN mkdir -p /app/uploads && chown -R app:app /app/uploads
USER app

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que a Railway vai usar
EXPOSE 8000

# Comando final para produção, usando o script deploy.py
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:${PORT:-8000}", "deploy:app"]
