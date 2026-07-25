#!/bin/sh
set -e

# SECURITY_AUDIT_2026-07.md item 12: o container roda o gunicorn como o
# usuario sem privilegio "appuser", nao root. O disco persistente do Render
# em /data (montado no boot, fora do controle da imagem) pode chegar com
# dono root -- este script roda como root so o suficiente para corrigir a
# posse de /data, depois troca para appuser via gosu antes do gunicorn.
if [ -d /data ]; then
  chown -R appuser:appuser /data
fi

exec gosu appuser "$@"
