"""
irflow_rate_limit.py

Responsabilidade: limitar tentativas de login por IP, contado na tabela
SQLite `login_attempts` em vez de armazenamento em memória de processo.

Por quê SQLite e não Flask-Limiter/memória: o Gunicorn deste projeto roda
com `--workers 2` (`Dockerfile`) — um contador em memória seria por
processo, o que enfraqueceria o limite nominal (5/min vira ~10/min na
prática) e poderia ser parcialmente contornado sendo roteado entre workers.
O SQLite já é a fonte de verdade compartilhada entre os dois workers (modo
WAL), então o limite fica realmente global sem depender de infraestrutura
nova.

Depende de: nenhum outro módulo de domínio.
"""


def resolver_ip_cliente(request):
    """
    Resolve o IP real do cliente atrás do proxy reverso.

    Produção atual (Render) injeta `X-Forwarded-For`. `Fly-Client-IP` é
    checado primeiro por compatibilidade com um deploy anterior em Fly.io;
    na ausência de ambos (dev local, outro proxy), cai para
    `request.remote_addr`.
    """
    fly_ip = (request.headers.get("Fly-Client-IP") or "").strip()
    if fly_ip:
        return fly_ip

    forwarded = request.headers.get("X-Forwarded-For") or ""
    primeiro = forwarded.split(",")[0].strip()
    if primeiro:
        return primeiro

    return request.remote_addr or "desconhecido"


def limite_excedido(cursor, identificador, max_tentativas=5, janela_minutos=1):
    """True se `identificador` já atingiu `max_tentativas` dentro da janela."""
    cursor.execute(
        """
        SELECT COUNT(*) FROM login_attempts
        WHERE identificador = ?
          AND criado_em >= datetime('now', ?)
        """,
        (identificador, f"-{janela_minutos} minutes"),
    )
    total = cursor.fetchone()[0] or 0
    return total >= max_tentativas


def registrar_tentativa(cursor, identificador, sucesso):
    cursor.execute(
        "INSERT INTO login_attempts (identificador, sucesso) VALUES (?, ?)",
        (identificador, 1 if sucesso else 0),
    )
