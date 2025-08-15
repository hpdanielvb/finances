FROM python:3.11-slim

WORKDIR /app

# Instala o Tesseract OCR e outras dependências de sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação (incluindo o novo deploy.py)
COPY . .

# Expõe a porta que a Railway vai usar
EXPOSE 8000

# Comando final para produção, usando o script deploy.py com gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:${PORT:-8000}", "deploy:app"]
