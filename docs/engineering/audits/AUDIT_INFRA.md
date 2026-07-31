# AUDIT_INFRA — Render, Vercel, GitHub Actions, Docker (Sprint Housekeeping)

**Data:** 2026-07-31
**Fase:** Sprint Housekeeping — Fase 1 (Auditoria), item 6 de 6 — **última auditoria, fecha a Fase 1**
**Método:** Inspeção de todo arquivo de infraestrutura versionado (`Dockerfile`, `docker-entrypoint.sh`,
`gunicorn.conf.py`, `.dockerignore`, `.env.example`, `.github/workflows/ci.yml`,
`frontend/vercel.json`). **Limitação importante:** não há acesso a este agente aos dashboards do
Render/Vercel/GitHub — tudo que só existe nesses painéis (não versionado como código) é listado como
"requer confirmação manual", não como achado confirmado.

**Insumos:** `AUDIT_LEGACY.md` (seção 2-3, env vars e URLs), `AUDIT_REPOSITORY.md` (seção 5, pergunta
sobre build da Vercel).

---

## O que é Infrastructure-as-Code neste projeto (e o que não é)

| Camada | Arquivo versionado? | Onde vive a configuração real |
|--------|:--:|-------------------------------|
| Render (backend) | **Não** — sem `render.yaml` no repositório | 100% no dashboard do Render — nada disso é inferível ou auditável a partir do código |
| Vercel (frontend) | Parcial — `frontend/vercel.json` só define `rewrites` (fallback de SPA) | Build Command / Output Directory / variáveis de ambiente ficam no dashboard, a menos que sobrescritas em `vercel.json` (não estão) |
| Docker | Sim — `Dockerfile`, `docker-entrypoint.sh`, `.dockerignore`, `gunicorn.conf.py` | Totalmente no repositório |
| CI | Sim — `.github/workflows/ci.yml` | Totalmente no repositório, já auditado em detalhe na Sprint CI/CD 1.1 |

Isso por si só é um achado: **qualquer rename de infraestrutura (repositório, domínios, nome de
serviço) depende inteiramente de mudança manual em painel externo — não existe automação nem
versionamento que garanta consistência.** Reforça por que esses itens ficam fora da Fase 4 desta sprint
(já era a conclusão de `AUDIT_DEPENDENCIES.md`/`AUDIT_DOCUMENTATION.md`; esta auditoria explica a causa
raiz: não há IaC).

---

## 1. Docker — sem achados de nomenclatura legada

`Dockerfile`, `docker-entrypoint.sh`, `gunicorn.conf.py` não contêm nenhuma referência a
`irflow`/`assistencia`/`IR_FLOW` (confirmado por busca direta). Único ponto relacionado:
`.dockerignore` replica os mesmos padrões `build_irflow/`, `build_irflow2/`, `build_irflow_setup/` do
`.gitignore` (raiz) — consistente com o achado já registrado em `AUDIT_REPOSITORY.md` seção 8 (scripts
de build desktop legado). Nenhuma imagem Docker recebe nome/tag fixo em nenhum lugar versionado — `ci.yml`
só valida `docker build .` sem tag; o nome real da imagem em produção (se houver) só existiria no
dashboard do Render.

---

## 2. Variáveis de ambiente — inventário completo de `.env.example`

`.env.example` já está bem documentado (cabeçalho explica onde cada variável é configurada em
produção). Consolidando com `AUDIT_LEGACY.md` seção 2:

| Grupo | Variáveis | Nomenclatura legada? |
|-------|-----------|:--:|
| Segredos | `FLASK_SECRET_KEY` | Não |
| Diretório de dados / rede | `IR_FLOW_DATA_DIR`, `IR_FLOW_HOST`, `IR_FLOW_PORT`, `IR_FLOW_PUBLIC_BASE_URL`, `IR_FLOW_CORS_ORIGINS`, `IR_FLOW_NO_BROWSER` | **Sim** (6) |
| Segurança | `IR_FLOW_SESSION_INACTIVITY_MINUTES`, `IR_FLOW_PASSWORD_RESET_TOKEN_HOURS` | **Sim** (2) |
| Backup | `IR_FLOW_ENABLE_BACKGROUND_JOBS`, `IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR`, `IR_FLOW_BACKUP_EMAIL`, `IR_FLOW_BACKUP_EMAIL_SENHA`, `IR_FLOW_BACKUP_EMAIL_DESTINO` | **Sim** (5) |
| Timeouts | `IR_FLOW_SQLITE_TIMEOUT_SECONDS` | **Sim** (1) |
| MercadoPhone | `MERCADO_PHONE_WEBHOOK_TOKEN`, `MERCADO_PHONE_API_TOKEN`, `MERCADO_PHONE_DEFAULT_TECNICO`, `MERCADO_PHONE_SYNC_*` (5 variáveis) | Não |
| Observabilidade | `SENTRY_DSN`, `METRICS_TOKEN` | Não |
| Injetadas pela plataforma (não configuráveis) | `FLY_DATA_DIR` (legado Fly.io), `RENDER`, `RENDER_DISK_PATH`, `RENDER_SERVICE_ID`, `RENDER_GIT_COMMIT`, `VERCEL_URL`, `VERCEL_GIT_COMMIT_SHA`, `PROMETHEUS_MULTIPROC_DIR`, `LOCALAPPDATA` (build desktop Windows) | `FLY_DATA_DIR` é legado de hospedagem descontinuada — não é nomenclatura `irflow`, mas é a mesma categoria de dívida (achado já registrado em `AUDIT_REPOSITORY.md` seção 7) |

Total: **14 variáveis `IR_FLOW_*`** confirmadas — mesmo número já levantado em `AUDIT_LEGACY.md`, sem
achado novo aqui além da organização por grupo funcional (útil para a janela de manutenção futura:
dá pra ver que "Diretório de dados / rede" e "Backup" são os grupos mais numerosos, então são os que
mais precisam de teste após qualquer rename coordenado).

---

## 3. GitHub Actions — sem segredos, sem achados

`.github/workflows/ci.yml` **não usa nenhum `${{ secrets.* }}`** — confirmado por busca direta. Todos os
jobs (Lint, Backend Tests, Frontend Quality, Frontend Build, Coverage Report, Docker Build) são
autocontidos, sem deploy nem consumo de credencial. Isso significa que um eventual rename de repositório
não quebra o CI por causa de secrets mal configurados — não há secrets. Baixo risco confirmado, não
apenas assumido.

---

## 4. Itens que exigem confirmação manual (fora do alcance desta auditoria)

Nenhum destes pode ser confirmado por leitura de arquivo — são decisões vivas nos dashboards:

| Item | Por que importa | Onde confirmar |
|------|------------------|-----------------|
| Nome do serviço Render (backend) | Pode ou não conter `irflow`/`assistencia` no slug interno do Render, independente da URL pública | Dashboard Render → Settings do serviço |
| `IR_FLOW_DATA_DIR` está de fato configurada no Render? | Se sim, é a variável mais crítica de todas para uma futura janela de rename (ativa `IS_SERVER_RUNTIME`) — confirmado como preocupação em `AUDIT_DEPENDENCIES.md` seção 3 | Dashboard Render → Environment |
| Todas as 14 variáveis `IR_FLOW_*` — quais estão de fato setadas em produção vs. usando o default do código? | Necessário para dimensionar o esforço real da janela de manutenção futura | Dashboard Render → Environment |
| Vercel: Build Command / Output Directory sobrescritos manualmente no dashboard? | `frontend/vercel.json` não define isso, então por padrão a Vercel builda do fonte (achado de `AUDIT_REPOSITORY.md` seção 5) — mas se alguém configurou algo diferente direto no dashboard, isso teria precedência e mudaria a conclusão | Dashboard Vercel → Project Settings → Build & Development Settings |
| Variáveis de ambiente configuradas na Vercel (`VITE_*`, `VITE_SENTRY_DSN`, etc.) | Fora do escopo de `.env.example` (que é só do backend) | Dashboard Vercel → Environment Variables |
| Nome do projeto/slug na Vercel | Determina a URL `assistencia-system.vercel.app` — mudar isso é justamente o item já registrado como fora desta sprint (`AUDIT_DEPENDENCIES.md` seção 4) | Dashboard Vercel → Project Settings |
| Webhooks/integrações externas apontando para as URLs atuais (MercadoPhone?) | Se o MercadoPhone (ou qualquer outro serviço externo) estiver configurado com a URL atual do Render como destino de webhook, um rename de domínio quebra a integração sem aviso no código | Painel do MercadoPhone (fora do controle deste repositório) |

---

## Conclusão da Fase 1

Com `AUDIT_INFRA.md`, as 6 auditorias da Fase 1 estão completas:

1. ✅ `AUDIT_LEGACY.md` — nomenclatura legada, inventário completo
2. ✅ `AUDIT_DEPENDENCIES.md` — impacto de renomeação, classificado por risco/complexidade/estratégia
3. ✅ `AUDIT_DOCUMENTATION.md` — escopo ampliado (badges/imagens/links), achado de estratégia (ADR-008)
4. ✅ `AUDIT_REPOSITORY.md` — arquivos órfãos, scripts, assets, build
5. ✅ `AUDIT_BRANCHES.md` — 8 branches não-mergeadas investigadas por conteúdo
6. ✅ `AUDIT_INFRA.md` — infraestrutura inferível do repo + lista do que precisa confirmação manual

Nenhum arquivo de código foi alterado em toda a Fase 1. Pronto para a **Fase 2 — Planejamento**: montar
a tabela única (Item / Prioridade / Risco / Ação) consolidando os achados dos 6 documentos.
