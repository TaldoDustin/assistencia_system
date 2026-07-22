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

# Volume persistente para banco de dados e dados gravados em disco
# Render monta /data (Disks) — a app detecta e usa automaticamente via RENDER_DISK_PATH
VOLUME ["/data"]

# Expõe a porta interna (o provedor de deploy roteia externamente)
EXPOSE 8080

# Inicia com gunicorn (produção)
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
