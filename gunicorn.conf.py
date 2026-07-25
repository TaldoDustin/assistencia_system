"""
gunicorn.conf.py

Configuração do Gunicorn — migrada dos flags soltos do `Dockerfile` CMD
(Sprint Observabilidade, 2026-07-25) porque os hooks `on_starting`/
`child_exit` do modo multiprocess do prometheus_client só podem ser
registrados via arquivo de config, não via flag de linha de comando.

Depende de: PROMETHEUS_MULTIPROC_DIR (env var, setada no Dockerfile). Sem
ela (dev local), os hooks abaixo viram no-op — nenhum diretório pra limpar
— e o prometheus_client roda no modo padrão de processo único, sem mudança
de comportamento fora do container.
"""

import os
import shutil

bind = "0.0.0.0:8080"
workers = 2
timeout = 60
accesslog = "-"
errorlog = "-"


def on_starting(server):
    """Roda uma vez no processo mestre, antes de qualquer worker subir.
    Limpa arquivos de métricas de um boot anterior -- sem isso, dados de
    um processo que já morreu ficariam grudados no agregado de /metrics."""
    multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not multiproc_dir:
        return
    shutil.rmtree(multiproc_dir, ignore_errors=True)
    os.makedirs(multiproc_dir, exist_ok=True)


def child_exit(server, worker):
    """Roda no mestre quando um worker morre (reciclagem normal ou
    crash). Marca o worker como morto no registry multiprocess -- sem
    isso, a métrica dele fica presa no agregado do /metrics."""
    multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if not multiproc_dir:
        return
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker.pid)
