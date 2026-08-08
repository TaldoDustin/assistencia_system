"""
Fluxoly - Sistema formal de migrations (TD-03, Fase 2 Fatia 1).

Ver docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md (Phase 1 --
Architecture Design) para o desenho completo e as decisões aprovadas.

Fatia 1 (atual): pacote construído e testado de forma isolada. app.py NÃO
foi alterado -- criar_tabelas()/SCHEMA_READY/SCHEMA_LOCK continuam sendo o
mecanismo real em produção, chamado por conectar() exatamente como antes.
run_migrations() só é wireado no bootstrap/conectar() na Fatia 2, depois de
validado.
"""
