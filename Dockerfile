# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Diretório da aplicação
WORKDIR /app

# Dependências primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Código da aplicação
COPY . .

# Copia o backup para o local do banco de dados
RUN mkdir -p "/app/IR Flow"
COPY backup-20260429-015724.db "/app/IR Flow/database.db"

# Volume persistente para banco de dados e dados gravados em disco
# O Fly.io monta /data — a app detecta e usa automaticamente via FLY_DATA_DIR
VOLUME ["/data"]

# Expõe a porta interna (Fly.io roteia externamente)
EXPOSE 8080

# Inicia com gunicorn (produção)
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
