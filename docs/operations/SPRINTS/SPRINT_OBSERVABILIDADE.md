# SPRINT OBSERVABILIDADE — Logs estruturados, correlation ID, health checks, métricas, Sentry

**Status:** CONCLUÍDA
**Período:** 25/07/2026 – 25/07/2026
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
| `irflow_logging.py` + logging JSON configurado | feat | Concluído |
| Correlation ID por request + log de acesso | feat | Concluído |
| `/health` e `/ready` | feat | Concluído |
| `/metrics` (Prometheus multiprocess) | feat | Concluído |
| Sentry (gated por `SENTRY_DSN`) | feat | Concluído |
| Migração dos `print()` críticos (`app.py`, `irflow_storage.py`, `irflow_mercadophone.py`) | refactor | Concluído |

---

## Critérios de Aceitação

- [x] Toda resposta HTTP carrega `X-Request-Id`; um valor enviado pelo cliente é validado antes de ser ecoado
- [x] `/health` sempre 200 sem autenticação; `/ready` reflete o estado real do banco (503 se inacessível)
- [x] `/metrics` expõe contagem e duração de requests, corretos entre os 2 workers do Gunicorn (modo multiprocess), protegido por token em produção — validado com `docker build`/`docker run` reais, 20 requests distribuídos entre os 2 workers agregados corretamente
- [x] Sentry inicializa só quando `SENTRY_DSN` está definida; nenhum PII de cliente enviado (`send_default_pii=False`)
- [x] Logs de backup e sincronização Mercado Phone saem em JSON estruturado, não mais `print()`
- [x] Suíte completa (526 testes) passando, `ruff check .` limpo

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

- [x] Todos os critérios de aceitação atingidos
- [x] Testes obrigatórios passando
- [x] `ruff check .` limpo
- [x] `CHANGELOG.md` atualizado
- [x] `PROJECT_STATUS.md` atualizado
- [x] `KNOWN_ISSUES.md` atualizado (KI-006 parcialmente endereçado — alerta agora existe via Sentry/log, falta notificação visível na UI)
- [x] `ROADMAP.md` — nota adicionada referenciando esta sprint como o fechamento real dos critérios de observabilidade da Sprint 3 original
- [x] Nenhum commit sem padrão Conventional Commits

---

## Retrospectiva

### O que funcionou bem

- Planejamento em modo plano antes de implementar: 3 perguntas de escopo (conta Sentry, estratégia de
  métricas multiprocess, extensão da migração de `print()`) evitaram decisões erradas caras — em
  especial a escolha de `/metrics` real com modo multiprocess em vez de uma solução mais simples que
  teria reproduzido a mesma classe de bug de INC-001/INC-002/rate limiting.
- Validação real com Docker (via `colima`, já instalado da Sprint Segurança 1.0) encontrou um bug
  genuíno que a leitura de código sozinha não pegaria: o socket de controle do Gunicorn ≥25 falhando
  por permissão no container non-root. Reforça o padrão já estabelecido nesta sprint anterior — não
  confiar só em leitura de código para mudanças de infraestrutura.
- Escopo da migração de `print()` (só os 22 com sinal operacional real, não os 243) evitou uma mudança
  desproporcional em arquivos sem relação com observabilidade de produção.

### O que poderia ter sido melhor

- O bug do socket de controle do Gunicorn só apareceu na validação Docker, depois de todos os
  componentes já implementados — poderia ter sido antecipado revisando o changelog do Gunicorn 26.0.0
  mais a fundo durante a Sprint Segurança 1.0 (quando a versão foi atualizada de 22 para 26).

### Lições aprendidas para a próxima sprint

- Ao atualizar uma dependência de infraestrutura (Gunicorn, neste caso) para uma versão com vários
  majors de diferença, vale revisar o changelog completo entre as versões, não só procurar pela CVE que
  motivou a atualização — features novas habilitadas por padrão (como o socket de controle) podem
  interagir mal com decisões de arquitetura já tomadas (aqui, o container non-root).
- Para a Sprint Performance proposta pelo usuário (próxima): logs estruturados e `/metrics` já existem
  agora, então o diagnóstico de `database is locked`/INC-001 pode se apoiar neles desde o início, em vez
  de precisar de instrumentação ad-hoc como na investigação original do INC-001.

### Dívida técnica gerada (se houver)

| ID | Descrição | Prioridade |
|----|-----------|-----------|
| TD-01 | `/metrics` fica pronto mas sem nenhum Prometheus/Grafana real consumindo — decisão deliberada de não provisionar infraestrutura de monitoramento externa nesta sprint | Baixa |
| ~~TD-02~~ | ~~Sentry integrado mas inativo (`SENTRY_DSN` vazia) até o usuário criar a conta~~ — **resolvido em 2026-07-30**: conta criada, `environment`/`release` adicionados ao `sentry_sdk.init()`, frontend integrado (`@sentry/react`, novo em 2026-07-30 — não fazia parte do escopo original desta sprint). Ver `docs/engineering/plans/PLAN-Observabilidade-Sentry-Frontend.md` | Média |
