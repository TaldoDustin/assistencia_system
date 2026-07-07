# PROJECT_STATUS

**Projeto:** Assistência System  
**Responsável:** Principal Software Engineer  
**Branch principal:** `main`  
**Ambiente de produção:** Fly.io — `https://assistencia-system.fly.dev`

**Última revisão:** 2026-07-07  
**Próxima revisão:** 2026-07-13

---

## Estado Atual

| Dimensão           | Status                          |
|--------------------|---------------------------------|
| Produção           | Operacional (Fly.io)            |
| Backend            | Estável — Flask + SQLite (WAL)  |
| Frontend           | Estável — React 19 + Vite       |
| CI/CD              | Ausente                         |
| Cobertura de testes| Baixa (~15%)                    |
| Dívida técnica     | Alta                            |
| Segurança          | Média (sem auditoria formal)    |

O sistema está em produção e cobre o ciclo completo de uma assistência técnica: abertura de OS, controle de estoque, tabela de preços, lista de compras, garantias, relatórios e backup. A maior fragilidade atual é a ausência de pipeline de CI/CD e a baixa cobertura de testes automatizados.

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

**Sprint 2 — Infraestrutura de Qualidade** (EM ANDAMENTO — ver `docs/SPRINTS/SPRINT_02.md`)
Objetivo: estabelecer pipeline de CI, testes unitários no backend e cobertura mínima de 40% antes de qualquer nova feature.

**Sprint 2.2 (T-01 a T-04) concluída em 2026-07-07:** primeira suíte pytest do projeto (`tests/test_auth.py`, 18 casos — login, logout, sessão, controle de acesso por perfil), isolada via `IR_FLOW_DATA_DIR`. Corrigido no processo um bug crítico pré-existente (KI-012) que impedia `app.py` de inicializar. Revisão independente de código concluída — aprovada para merge. Mergeado em `main`.

**Sprint 2.3 (T-12 a T-16) concluída em 2026-07-07:** fecha os gaps de cobertura deixados pela 2.2 e expande para autorização — 55 novos casos em 4 módulos (`test_users.py`, `test_permissions.py`, `test_session.py`, `test_security.py`), todos consumindo fixtures compartilhados extraídos para `conftest.py`. Cobre CRUD de usuários via API, matriz de permissões por perfil (admin/tecnico/vendedor), sessão (expiração simulada, cookie adulterado, logout múltiplo) e resiliência de entrada (SQLi, payload inválido, content-type). Suíte completa: 73 testes, 100% passando. Um caso do escopo original (JSON de tipo errado no login) expôs uma exceção não tratada em produção e foi retirado da suíte em vez de commitado como teste falho — reportado separadamente para decisão, sem registro em `KNOWN_ISSUES.md` nesta sprint (orientação explícita do usuário). Ver `docs/SPRINTS/SPRINT_02.md`.

Restante da Sprint 2 (T-05 a T-11): `test_os.py`, `test_pricing.py`, `test_shopping.py`, configuração de cobertura, GitHub Actions CI, `.env.example`.

### Escopo previsto

- Configurar GitHub Actions (lint + testes no push)
- Escrever testes unitários para módulos críticos do backend (`irflow_os.py`, `irflow_blueprints_api.py`)
- Migrar testes de smoke para pytest com fixtures isoladas
- Configurar Playwright no CI (headless)
- Documentar variáveis de ambiente em `.env.example`
- Padronizar mensagens de commit (Conventional Commits)

---

## Score do Projeto

| Critério                      | Peso | Nota | Score |
|-------------------------------|------|------|-------|
| Funcionalidade core           | 25%  | 8/10 | 2,0   |
| Cobertura de testes           | 20%  | 3/10 | 0,6   |
| Arquitetura e organização     | 15%  | 5/10 | 0,75  |
| Segurança                     | 15%  | 5/10 | 0,75  |
| Observabilidade / logs        | 10%  | 3/10 | 0,3   |
| DevEx (CI/CD, docs, DX)       | 10%  | 2/10 | 0,2   |
| Desempenho                    | 5%   | 6/10 | 0,3   |
| **Total**                     |      |      | **4,9 / 10** |

> Score recalculado em 2026-07-07 após Sprint 2.3 (cobertura de testes: 2/10 → 3/10 — camada de autenticação/autorização agora robusta, mas cobertura global de backend ainda longe da meta; regras de negócio de domínio — OS, preços, estoque — seguem sem cobertura). Meta para fim de Sprint 2: >= 6,0.

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

| Camada            | Tipo                     | Ferramenta   | Cobertura medida (`pytest-cov`, 2026-07-07) |
|-------------------|--------------------------|--------------|--------------------|
| Backend — API     | Smoke tests ad-hoc       | Python scripts| ~25% das rotas (não medido via `pytest-cov`) |
| Backend — Módulos | pytest (auth, sessão, usuários, permissões, segurança — Sprint 2.2+2.3, 73 testes) | pytest | `irflow_blueprints_auth.py` 83% · `app.py` 52% · `irflow_core.py` 68% · `irflow_blueprints_api.py` 19% (só a fatia de `/api/usuarios`, `/api/auth/*` e `/api/ordens/<id>`) |
| Frontend — Pages  | Sem testes unitários     | —            | 0%                 |
| Frontend — E2E    | Fluxos principais        | Playwright   | ~20% dos fluxos    |
| Integração        | Script manual            | Python       | ~10%               |
| **Global (repo)** |                          |              | **19%** (`pytest --cov=.` — inclui scripts ad-hoc fora de escopo da Sprint 2, ex. `smoke_test_full.py`; ver P-03 em `SPRINT_02.md`) |

> Meta Sprint 2: >= 40% de cobertura nas rotas críticas do backend. Ainda não atingida — depende de `test_os.py`, `test_pricing.py`, `test_shopping.py` (T-05 a T-07, não iniciadas).

---

## Próximos Objetivos

### Curto prazo (Sprint 2)
1. Implementar pipeline de CI com GitHub Actions
2. Migrar smoke tests para pytest com fixtures
3. Atingir 40% de cobertura nas rotas críticas
4. Documentar `.env.example`
5. Padronizar commits com Conventional Commits

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
