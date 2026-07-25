# syntax=docker/dockerfile:1
FROM python:3.11-slim

# gosu: usado pelo docker-entrypoint.sh para trocar de root para "appuser"
# depois de ajustar a posse de /data (SECURITY_AUDIT_2026-07.md item 12).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system appuser && useradd --system --gid appuser --home /app --shell /usr/sbin/nologin appuser

# Diretório da aplicação
WORKDIR /app

# Dependências primeiro (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Código da aplicação
COPY --chown=appuser:appuser . .

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copia o backup para o local do banco de dados

# Volume persistente para banco de dados e dados gravados em disco
# Render monta /data (Disks) — a app detecta e usa automaticamente via RENDER_DISK_PATH
VOLUME ["/data"]

# Expõe a porta interna (o provedor de deploy roteia externamente)
EXPOSE 8080

# O entrypoint roda como root só para corrigir a posse de /data (disco
# montado em runtime, fora do controle desta imagem) e então troca para
# "appuser" antes de executar o gunicorn — container nunca serve tráfego
# como root (SECURITY_AUDIT_2026-07.md item 12).
ENTRYPOINT ["docker-entrypoint.sh"]

# Inicia com gunicorn (produção)
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
