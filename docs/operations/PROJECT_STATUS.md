# PROJECT_STATUS

**Projeto:** Fluxoly Platform  
**Responsável:** Principal Software Engineer  
**Branch principal:** `main`  
**Ambiente de produção:** Fly.io — `https://assistencia-system.fly.dev`

**Última revisão:** 2026-07-10  
**Próxima revisão:** 2026-07-13

---

## Estado Atual

| Dimensão           | Status                          |
|--------------------|---------------------------------|
| Produção           | Operacional (Fly.io)            |
| Backend            | Estável — Flask + SQLite (WAL)  |
| Frontend           | Estável — React 19 + Vite       |
| CI/CD              | Presente (`.github/workflows/ci.yml` — lint, testes, frontend, build). Cobertura agora bloqueante (`fail_under = 40`). **Atenção:** job `Lint` está vermelho em `main` com 20 erros de `ruff check .` pré-existentes (KI-017) — como `backend`/`frontend` dependem de `Lint`, o pipeline inteiro fica bloqueado até isso ser corrigido |
| Cobertura de testes| 43% global, 331 testes — meta de 40% da Sprint 2 atingida (ver Cobertura de Testes) |
| Dívida técnica     | Alta                            |
| Segurança          | Média (sem auditoria formal)    |

O sistema está em produção e cobre o ciclo completo de uma assistência técnica: abertura de OS, controle de estoque, tabela de preços, lista de compras, garantias, relatórios e backup. A cobertura de testes atingiu a meta da Sprint 2 (40%) e o gate de CI já bloqueia regressão de cobertura. A fragilidade mais visível agora é operacional, não funcional: o job de lint do CI está vermelho em `main` por dívida técnica pré-existente (KI-017), bloqueando o restante do pipeline para qualquer push.

---

## Última Sprint Concluída

**Sprint 1 — Shopping List & Estabilização de OS**  
Período estimado: 01/06/2026 – 21/06/2026

### O que foi entregue

| Entrega | Descrição |
|---------|-----------|
| Shopping List (backend) | Tabela `shopping_list`, API REST completa com status workflow |
| Shopping List (frontend) | Página `Compras.jsx` com client dedicado `shoppingList` |
| `EditShoppingItemModal` | Modal de edição de itens da lista de compras |
| Auto-preenchimento de `valor_cobrado` | Endpoint `GET /api/precos/sugerir` + `useEffect` em NewOrder/EditOrder |
| Fix: PDF IR Phones | URL corrigida de `irphones` para `ir-phones` |
| Fix: `historico-cliente` | Rota corrigida no client.js |
| Fix: campo `cor` no EditOrder | Campo limpo ao trocar modelo |
| Remoção do `.env` do repositório | Commit `832945c` |
| Build/dist pipeline corrigido | Commit `ae7c575` |

---

## Sprint em Andamento

**Sprint 2 — Infraestrutura de Qualidade** (EM ANDAMENTO — ver `docs/operations/SPRINTS/SPRINT_02.md`)
Objetivo: estabelecer pipeline de CI, testes unitários no backend e cobertura mínima de 40% antes de qualquer nova feature.

**Sprint 2.2 (T-01 a T-04) concluída em 2026-07-07:** primeira suíte pytest do projeto (`tests/test_auth.py`, 18 casos — login, logout, sessão, controle de acesso por perfil), isolada via `IR_FLOW_DATA_DIR`. Corrigido no processo um bug crítico pré-existente (KI-012) que impedia `app.py` de inicializar. Revisão independente de código concluída — aprovada para merge. Mergeado em `main`.

**Sprint 2.3 (T-12 a T-16) concluída em 2026-07-07:** fecha os gaps de cobertura deixados pela 2.2 e expande para autorização — 55 novos casos em 4 módulos (`test_users.py`, `test_permissions.py`, `test_session.py`, `test_security.py`), todos consumindo fixtures compartilhados extraídos para `conftest.py`. Cobre CRUD de usuários via API, matriz de permissões por perfil (admin/tecnico/vendedor), sessão (expiração simulada, cookie adulterado, logout múltiplo) e resiliência de entrada (SQLi, payload inválido, content-type). Suíte completa: 73 testes, 100% passando. Um caso do escopo original (JSON de tipo errado no login) expôs uma exceção não tratada em produção e foi retirado da suíte em vez de commitado como teste falho — reportado separadamente para decisão, sem registro em `KNOWN_ISSUES.md` nesta sprint (orientação explícita do usuário). Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.4 (T-17 a T-20) concluída em 2026-07-07, mergeada em `main` em 2026-07-10:** cobertura de regras de negócio de Ordens de Serviço — 88 novos casos em 3 módulos (`test_os_creation_query.py`, `test_os_update_status.py`, `test_os_deletion_security.py`) mais fixtures compartilhados em `conftest.py`. Durante a investigação (antes de qualquer teste), dois bugs reais foram encontrados na validação de `status` ao editar OS — um valor ausente/desconhecido era silenciosamente normalizado para "Em andamento" em vez de rejeitado, o que em `PUT /api/ordens/<id>` reabria silenciosamente uma OS Finalizada e apagava `data_finalizado` (ver B-14 abaixo). As correções foram escritas em 2026-07-07 mas ficaram presas na branch, que só foi revisada e mergeada em `main` em 2026-07-10, ao retomar o Sprint 2 — nesse intervalo o bug esteve ativo em produção; extraídas via `hotfix/status-os-padrao-vazio` (KI-015) antes do restante da branch. Uma divergência de comportamento entre a rota legada e a API (reativação de OS Cancelada não re-consome estoque via API) foi caracterizada via teste, não corrigida — já registrada como exemplo em `docs/engineering/ENGINEERING_GUIDE.md` §11. Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.5 (T-21 a T-25) concluída em 2026-07-07:** cobertura de regras de negócio de Estoque — 69 novos casos em 4 módulos (`test_stock_creation_query.py`, `test_stock_movement.py`, `test_stock_os_integration.py`, `test_stock_security.py`) mais fixtures compartilhados em `conftest.py`. Durante a investigação, dois bugs reais foram encontrados e corrigidos via `hotfix/` conforme ADR-004, com aprovação explícita do usuário antes de cada um (ver B-11 e B-12 abaixo). Um deles (ordem de parâmetros SQL) não se encaixava perfeitamente nos critérios objetivos do `ENGINEERING_GUIDE.md` §11 — critério novo C-05 registrado no backlog (ver Próximos Objetivos). **Mergeada em `main` em 2026-07-07** (merge fast-forward, sem conflitos). Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.6 — Padronização de Validação e Parsing (T-26, T-27) concluída em 2026-07-07, mergeada em `main`:** criada camada compartilhada de parsing (`irflow_validation.py`: `parse_int`, `parse_float`, `safe_json`, `validate_positive_number`) e aplicada em `irflow_blueprints_api.py`, eliminando ~50 pontos de duplicação (22x `request.get_json(silent=True) or {}`, checagens de valor positivo, parsing de quantidade). No processo, corrigidos 9 pontos onde um valor não numérico em `request.args`/corpo JSON derrubava a rota com 500 não tratado (KI-013, commit `fix:` isolado do `refactor:`). Registrado KI-014 (bloco `criar_estoque` duplicado e morto, sem efeito em runtime, fora de escopo). 38 testes novos (`tests/test_validation.py`, `tests/test_api_parsing.py`, `tests/test_api_parsing_refactor.py`). Auto-merge com os hotfixes de estoque da Sprint 2.5 (`584c501`, `44be10c`) verificado linha a linha — sem sobreposição, ambos preservados corretamente. Ver `docs/operations/SPRINTS/SPRINT_02.md`.

**Sprint 2.7 — Fechamento (T-28, T-29) concluída em 2026-07-11:** `tests/test_pricing.py` (27 casos — lógica pura de `irflow_price_tables.py` e integração de `/api/precos*`) e `tests/test_shopping.py` (34 casos — CRUD, workflow de status, bloqueio de compra simultânea, auditoria de `/api/shopping-list`), mais fixtures locais de limpeza por teste. Cobertura global subiu de 36% para 43%, passando a meta de 40% da Sprint 2. Durante a escrita de `test_shopping.py`, um bug real foi encontrado em `POST /api/shopping-list` (quantidade `0` normalizada silenciosamente para `1` — C-01+C-04) e corrigido via `hotfix/quantidade-zero-shopping-list` antes de continuar (KI-016). Cobertura tornada bloqueante no CI (`fail_under = 40` em `pyproject.toml`, `continue-on-error` removido de `ci.yml`) com aprovação explícita do usuário. Achado adicional fora de escopo: `ruff check .` falha em `main` com 20 erros pré-existentes, não introduzidos nesta sprint — registrado como KI-017, não corrigido (seria refatoração multi-arquivo). `.env.example` permanece pendente. Ver `docs/operations/SPRINTS/SPRINT_02.md`.

Restante da Sprint 2: `.env.example`.

### Escopo previsto

- ~~Configurar GitHub Actions (lint + testes no push)~~ — já existe (`.github/workflows/ci.yml`), descoberto desatualizado nesta revisão (2026-07-10)
- Escrever testes unitários para módulos críticos do backend (`irflow_os.py`, `irflow_blueprints_api.py`)
- Migrar testes de smoke para pytest com fixtures isoladas
- Configurar Playwright no CI (headless)
- Documentar variáveis de ambiente em `.env.example`
- Padronizar mensagens de commit (Conventional Commits)
- ~~Tornar a cobertura bloqueante no CI~~ — feito em 2026-07-11 (`fail_under = 40`); os `continue-on-error` de formatação (ruff format/isort/black) seguem adiados para a Sprint 3, sem mudança

---

## Score do Projeto

| Critério                      | Peso | Nota | Score |
|-------------------------------|------|------|-------|
| Funcionalidade core           | 25%  | 8/10 | 2,0   |
| Cobertura de testes           | 20%  | 4/10 | 0,8   |
| Arquitetura e organização     | 15%  | 5/10 | 0,75  |
| Segurança                     | 15%  | 5/10 | 0,75  |
| Observabilidade / logs        | 10%  | 3/10 | 0,3   |
| DevEx (CI/CD, docs, DX)       | 10%  | 2/10 | 0,2   |
| Desempenho                    | 5%   | 6/10 | 0,3   |
| **Total**                     |      |      | **5,1 / 10** |

> Score recalculado em 2026-07-10, pós-merge da Sprint 2.4 em `main` — ver seção "Cobertura de Testes"
> abaixo para os números reais medidos após o merge. **Nota (2026-07-10):** esta revisão descobriu que
> `.github/workflows/ci.yml` já existe desde antes desta conversa (commit `563765f`) — a nota "DevEx
> (CI/CD, docs, DX)" 2/10 acima foi calculada assumindo CI/CD ausente, o que estava errado. A cobertura
> ainda não é bloqueante no pipeline (`--cov-fail-under=0`), então algum desconto permanece válido, mas
> a nota provavelmente já justifica um valor mais alto. Recálculo formal do score fica para a próxima
> revisão, não decidido unilateralmente aqui — mesma disciplina já aplicada à nota anterior sobre a
> Sprint 2.6. Meta para fim de Sprint 2: >= 6,0.

---

## Bugs Conhecidos

| ID   | Descrição                                                        | Severidade | Status        |
|------|------------------------------------------------------------------|------------|---------------|
| B-01 | Mensagens de commit sem padrão dificultam rastreabilidade de bugs | Baixa      | Aberto        |
| B-02 | SQLite não adequado para cenários de alta concorrência           | Média       | Aceito (risco) |
| B-03 | Sem rate limiting nas rotas de autenticação (`/api/auth/login`)  | Alta        | Aberto        |
| B-04 | Tokens de checklist público não expiram                          | Média       | Aberto        |
| B-05 | Backup por e-mail pode falhar silenciosamente sem alertas visíveis| Baixa      | Aberto        |
| ~~B-06~~ | ~~Auto-fill `valor_cobrado` ausente~~ | ~~Crítica~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-07~~ | ~~PDF IR Phones com URL errada~~ | ~~Alta~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-08~~ | ~~`historico-cliente` apontando para rota inexistente~~ | ~~Média~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-09~~ | ~~Campo `cor` não limpo ao trocar modelo~~ | ~~Média~~ | ~~Resolvido (Sprint 1)~~ |
| ~~B-10~~ | ~~Endpoint `/api/shopping-list` duplicado (código legado) travava a inicialização do Flask (KI-012)~~ | ~~Crítica~~ | ~~Resolvido (2026-07-07)~~ |
| ~~B-11~~ | ~~`PUT /api/estoque/<id>` calculava o diff de movimentação com a quantidade não limitada a zero — quantidade negativa gerava saída maior que o saldo real no histórico~~ | ~~Média~~ | ~~Resolvido (2026-07-07, hotfix, commit `584c501`)~~ |
| ~~B-12~~ | ~~`GET /api/estoque` com qualquer filtro (modelo/tipo/qualidade) retornava sempre lista vazia — ordem errada de parâmetros SQL~~ | ~~Alta~~ | ~~Resolvido (2026-07-07, hotfix, commit `44be10c`)~~ |
| ~~B-13~~ | ~~9 rotas de `irflow_blueprints_api.py` retornavam 500 não tratado com entrada não numérica em `int()`/`float()` (KI-013)~~ | ~~Média~~ | ~~Resolvido (2026-07-07)~~ |
| ~~B-14~~ | ~~`PATCH /api/ordens/<id>/status` e `PUT /api/ordens/<id>` sem `status_padrao=""` explícito — status ausente/inválido normalizado silenciosamente para "Em andamento"; em `PUT`, reabria OS Finalizada e zerava `data_finalizado` sem erro (KI-015)~~ | ~~Crítica~~ | ~~Resolvido (2026-07-10, hotfix, commit `2defd17`; achados originais durante a Sprint 2.4, commits `c85a321`/`e755f25`, 2026-07-07)~~ |
| ~~B-15~~ | ~~`POST /api/shopping-list` normalizava `quantidade_solicitada: 0` silenciosamente para `1` (operador `or` tratando `0` como ausente) em vez de rejeitar (KI-016)~~ | ~~Média~~ | ~~Resolvido (2026-07-11, hotfix `quantidade-zero-shopping-list`, achado durante a Sprint 2.7)~~ |

---

## Dívida Técnica

| ID   | Descrição                                                              | Impacto | Prioridade |
|------|------------------------------------------------------------------------|---------|------------|
| TD-01 | `irflow_blueprints_api.py` com ~130KB — módulo demasiado grande        | Alto    | Alta       |
| TD-02 | `app.py` acumula inicialização, DB e lógica misturadas                 | Alto    | Alta       |
| TD-03 | Ausência de migrations formais (usa `ALTER TABLE` com try/except)      | Alto    | Alta       |
| TD-04 | Sem injeção de dependências no backend — acoplamento direto ao SQLite  | Médio   | Média      |
| TD-05 | Testes de backend são scripts ad-hoc, não pytest com fixtures isoladas | Médio   | Alta       |
| TD-06 | Sem variáveis de ambiente documentadas (`.env.example` ausente)        | Médio   | Média      |
| TD-07 | Frontend sem testes unitários (apenas E2E Playwright)                  | Médio   | Média      |
| TD-08 | Commits com mensagens vagas ("att", "S", "att 09/06 5")               | Baixo   | Alta       |
| TD-09 | Sem paginação na listagem de OS — pode degradar com volume alto        | Médio   | Média      |
| TD-10 | Sem compressão de resposta HTTP no Flask                               | Baixo   | Baixa      |
| TD-11 | Bloco `criar_estoque()` duplicado e morto em `irflow_blueprints_api.py` (linhas 220-267, nunca roteado — KI-014) | Baixo | Baixa |

---

## Riscos Atuais

| ID   | Risco                                                                 | Probabilidade | Impacto | Mitigação atual      |
|------|-----------------------------------------------------------------------|---------------|---------|----------------------|
| R-01 | SQLite em produção sem replicação — falha de disco = perda de dados  | Baixa         | Crítico | Backup automático    |
| R-02 | Sem CI/CD — regressões chegam a produção sem detecção automática      | Alta          | Alto    | Nenhuma              |
| R-03 | Chaves secretas em variáveis de ambiente sem documentação formal      | Média         | Alto    | `.env` removido do git|
| R-04 | Sem rate limiting — `/api/auth/login` vulnerável a força bruta        | Média         | Alto    | Nenhuma              |
| R-05 | Tokens de checklist não expiram — link público permanente             | Baixa         | Médio   | Nenhuma              |
| R-06 | Dependência única de Fly.io sem estratégia de fallback documentada    | Baixa         | Médio   | DEPLOY.md alternativo|
| R-07 | Módulo de integração MercadoPhone sem testes — qualquer mudança é risco| Alta         | Médio   | Script diagnose_mercadophone.py |
| R-08 | `ruff check .` vermelho em `main` (KI-017) — job `Lint` bloqueia `backend`/`frontend` via `needs: lint`, nenhum PR consegue rodar o restante do CI enquanto isso não for corrigido | Alta | Alto | Nenhuma — não introduzido nesta sessão, mas descoberto rodando `ruff check .` localmente em 2026-07-11 |

---

## Arquivos Críticos

| Arquivo                          | Papel                                                         | Risco de tocar |
|----------------------------------|---------------------------------------------------------------|----------------|
| `irflow_blueprints_api.py`       | Todos os endpoints REST (~80+) — núcleo do sistema           | Muito alto     |
| `app.py`                         | Inicialização Flask, schema DB, registro de blueprints        | Muito alto     |
| `irflow_os.py`                   | Lógica de negócio das Ordens de Serviço                       | Alto           |
| `irflow_storage.py`              | Backup automático e Google Drive                              | Alto           |
| `irflow_mercadophone.py`         | Integração com sistema externo MercadoPhone                   | Alto           |
| `frontend/src/api/client.js`     | Centraliza todas as chamadas de API do frontend               | Alto           |
| `frontend/src/App.jsx`           | Roteamento, guards de autenticação, layout global             | Alto           |
| `frontend/src/contexts/AuthContext.jsx` | Estado global de autenticação                          | Alto           |
| `irflow_core.py`                 | Constantes de status e utilitários compartilhados             | Médio          |
| `frontend/src/pages/NewOrder.jsx`| Fluxo crítico de criação de OS com auto-price                 | Médio          |
| `frontend/src/pages/EditOrder.jsx`| Fluxo crítico de edição de OS                                | Médio          |

---

## Cobertura de Testes

| Camada            | Tipo                     | Ferramenta   | Cobertura medida em `main` (`pytest-cov`, 2026-07-11, pós-merge Sprint 2.7) |
|-------------------|--------------------------|--------------|--------------------|
| Backend — API     | Smoke tests ad-hoc       | Python scripts| ~25% das rotas (não medido via `pytest-cov`) |
| Backend — Módulos | pytest (auth, sessão, usuários, permissões, segurança, estoque, OS, parsing/validação, preços, shopping list — Sprint 2.2 a 2.7) | pytest | `irflow_validation.py` 100% · `irflow_blueprints_auth.py` 83% · `irflow_core.py` 88% · `irflow_price_tables.py` 83% · `app.py` 53% · `irflow_os.py` 64% · `irflow_blueprints_api.py` 58% |
| Frontend — Pages  | Sem testes unitários     | —            | 0%                 |
| Frontend — E2E    | Fluxos principais        | Playwright   | ~20% dos fluxos    |
| Integração        | Script manual            | Python       | ~10%               |
| **Global (repo, `main`)** |                  |              | **43%** (`pytest --cov`, 331 testes, pós-merge Sprint 2.7 — 2026-07-11) |

> Meta Sprint 2: >= 40% de cobertura nas rotas críticas do backend. **Atingida** em 2026-07-11 com `test_pricing.py` e `test_shopping.py` (Sprint 2.7) — cobertura global subiu de 36% para 43%. Gate de CI tornado bloqueante no mesmo commit (`fail_under = 40`). `test_os.py` (nome originalmente previsto) foi substituído por 3 módulos mais granulares na Sprint 2.4 (`test_os_creation_query.py`, `test_os_update_status.py`, `test_os_deletion_security.py`).

---

## Próximos Objetivos

### Curto prazo (Sprint 2)
1. ~~Implementar pipeline de CI com GitHub Actions~~ — já existe, ver "Estado Atual"
2. Migrar smoke tests para pytest com fixtures
3. ~~Atingir 40% de cobertura nas rotas críticas~~ — feito em 2026-07-11 (43%, `test_pricing.py`, `test_shopping.py`)
4. Documentar `.env.example`
5. Padronizar commits com Conventional Commits
6. **[Novo, prioridade alta]** Corrigir os 20 erros de `ruff check .` em `main` (KI-017/R-08) — bloqueia o job `Lint` e, por consequência, `backend`/`frontend` no CI para qualquer PR. Fora do escopo desta sprint (seria refatoração multi-arquivo), mas recomendado antes da Sprint 3
7. **[Backlog — process]** Adicionar critério **C-05 — Consulta incorreta em fluxo oficial** a `docs/engineering/ENGINEERING_GUIDE.md` §11 (ou ADR dedicada). Motivação: o hotfix `44be10c` (Sprint 2.5 — ordem de parâmetros SQL quebrava todo filtro de `GET /api/estoque`) não se encaixava nos critérios C-01–C-04 existentes, que cobrem mutação de dado, não leitura incorreta em rota de consulta usada pelo frontend. Rascunho de critério: *"O achado faz uma rota de consulta (GET) oficialmente usada pelo frontend retornar dado incorreto, incompleto ou vazio de forma sistemática (não um erro pontual de um registro), sem sinalizar erro ao chamador?"* Avaliar junto de C-01–C-04 na próxima ocorrência similar antes de formalizar a redação final.

### Médio prazo (Sprint 3–4)
1. Quebrar `irflow_blueprints_api.py` em módulos menores
2. Implementar migrations formais (Alembic ou scripts versionados)
3. Adicionar rate limiting em `/api/auth/login`
4. Implementar expiração de tokens de checklist
5. Adicionar paginação na listagem de OS

### Longo prazo (Sprint 5+)
1. Avaliar migração de SQLite para PostgreSQL
2. Implementar observabilidade (Sentry ou similar)
3. Criar API pública documentada (OpenAPI/Swagger)
4. Adicionar notificações push/webhook para mudanças de status de OS
