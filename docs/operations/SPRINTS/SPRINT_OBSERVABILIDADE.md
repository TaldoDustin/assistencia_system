# SPRINT OBSERVABILIDADE — Logs estruturados, correlation ID, health checks, métricas, Sentry

**Status:** EM ANDAMENTO
**Período:** 25/07/2026 – (em andamento)
**Tipo:** Infraestrutura

---

## Objetivo

Dar ao time capacidade real de diagnóstico em produção: logs em JSON correlacionados por request, verificação de saúde do processo, métricas via Prometheus e captura de erro via Sentry — hoje a única fonte de diagnóstico são 243 `print()` sem estrutura.

## Motivação

Depois da Sprint Segurança 1.0 (encerrada 2026-07-25, ver `docs/security/SECURITY_AUDIT_2026-07.md`), o usuário (CTO) avaliou que segurança deixou de ser o principal gargalo para o primeiro cliente pagante — o maior risco agora é confiabilidade operacional. Se um cliente reportar "o sistema ficou lento" hoje, a resposta só pode vir de relatos, não de dados. Esta lacuna já estava documentada e nunca fechada: `docs/operations/ROADMAP.md` (Sprint 3 — Segurança e Observabilidade, critérios "logs estruturados em JSON" e "alertas de erro em produção" nunca marcados) e `docs/operations/KNOWN_ISSUES.md` KI-006 (falha de backup sem alerta visível).

---

## Arquivos Envolvidos

| Arquivo | Mudança prevista |
|---------|-----------------|
| `irflow_logging.py` (novo) | `JSONFormatter`, `configurar_logging()`, `get_logger()` |
| `app.py` | Chama `configurar_logging()`; correlation ID (`before_request`/`after_request`); `/health`, `/ready`, `/metrics`; init do Sentry; bypass de auth para as 3 rotas novas |
| `gunicorn.conf.py` (novo) | Config do Gunicorn migrada dos flags do `Dockerfile` CMD; hooks `on_starting`/`child_exit` do Prometheus multiprocess |
| `Dockerfile` | `ENV PROMETHEUS_MULTIPROC_DIR`; `CMD` passa a usar `--config gunicorn.conf.py` |
| `requirements.txt` | `prometheus-client`, `sentry-sdk[flask]` |
| `.env.example` | `SENTRY_DSN`, `METRICS_TOKEN` documentados |
| `irflow_storage.py` | 7 `print()` → `logger.*` (thread de backup) |
| `irflow_mercadophone.py` | ~13 `print()` → `logger.*` (sincronização) |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| `irflow_logging.py` + logging JSON configurado | feat | Planejado |
| Correlation ID por request + log de acesso | feat | Planejado |
| `/health` e `/ready` | feat | Planejado |
| `/metrics` (Prometheus multiprocess) | feat | Planejado |
| Sentry (gated por `SENTRY_DSN`) | feat | Planejado |
| Migração dos `print()` críticos (`app.py`, `irflow_storage.py`, `irflow_mercadophone.py`) | refactor | Planejado |

---

## Critérios de Aceitação

- [ ] Toda resposta HTTP carrega `X-Request-Id`; um valor enviado pelo cliente é validado antes de ser ecoado
- [ ] `/health` sempre 200 sem autenticação; `/ready` reflete o estado real do banco (503 se inacessível)
- [ ] `/metrics` expõe contagem e duração de requests, corretos entre os 2 workers do Gunicorn (modo multiprocess), protegido por token em produção
- [ ] Sentry inicializa só quando `SENTRY_DSN` está definida; nenhum PII de cliente enviado (`send_default_pii=False`)
- [ ] Logs de backup e sincronização Mercado Phone saem em JSON estruturado, não mais `print()`
- [ ] Suíte completa (502+ testes) passando, `ruff check .` limpo

---

## Testes Obrigatórios

| Teste | Arquivo | O que valida |
|-------|---------|-------------|
| Formato JSON do logger, `request_id` presente dentro de request | `tests/test_logging_json.py` | `JSONFormatter` e integração com `flask.g` |
| `/health` e `/ready` | `tests/test_health_ready.py` | Liveness sempre 200; readiness reflete banco |
| Correlation ID | `tests/test_request_id.py` | Header ecoado; valor inválido do cliente é substituído |
| `/metrics` | `tests/test_metrics.py` | Formato Prometheus; token exigido só em `IS_SERVER_RUNTIME` |

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | Métricas inconsistentes entre os 2 workers do Gunicorn (mesma classe de bug de INC-001/INC-002) | Média | Médio | Modo multiprocess do `prometheus_client` com `PROMETHEUS_MULTIPROC_DIR` compartilhada, validado com `docker run` real batendo múltiplos requests |
| RS-02 | `/metrics` exposto sem proteção em produção | Baixa (mitigada no design) | Baixo | Token via `METRICS_TOKEN`, exigido quando `IS_SERVER_RUNTIME` |
| RS-03 | Sentry capturar dado sensível de cliente (nome, IMEI) em breadcrumb/payload | Baixa (mitigada no design) | Alto | `send_default_pii=False` explícito, sem tracing de payload de request |

---

## Dependências

- Depende de: Sprint Segurança 1.0 concluída (`docs/security/SECURITY_AUDIT_2026-07.md`)
- Bloqueia: nada formalmente — mas antecede a "Sprint Performance" proposta pelo usuário (diagnosticar `database is locked`/INC-001 fica mais fácil com logs estruturados e métricas em produção)

---

## Definition of Done

- [ ] Todos os critérios de aceitação atingidos
- [ ] Testes obrigatórios passando
- [ ] `ruff check .` limpo
- [ ] `CHANGELOG.md` atualizado
- [ ] `PROJECT_STATUS.md` atualizado
- [ ] `KNOWN_ISSUES.md` atualizado (KI-006 parcialmente endereçado — alerta agora existe via Sentry/log, falta notificação visível na UI)
- [ ] `ROADMAP.md` — Sprint 3 original tinha "logs estruturados"/"Sentry" como critério nunca marcado; referenciar esta sprint como o fechamento real
- [ ] Nenhum commit sem padrão Conventional Commits

---

## Retrospectiva (preencher ao concluir)

### O que funcionou bem

### O que poderia ter sido melhor

### Lições aprendidas para a próxima sprint

### Dívida técnica gerada (se houver)

| ID | Descrição | Prioridade |
|----|-----------|-----------|
