# ROADMAP

**Projeto:** Fluxoly Platform  
**Data de atualização:** 2026-07-06  
**Versão atual:** 1.x (pós-deploy Fly.io)  
**Horizonte:** 4 fases / ~8 sprints

---

## Visão Geral

```
Fase 1 — Estabilização         [Sprint 0–1]   ████████████ CONCLUÍDA
Fase 2 — Qualidade             [Sprint 2–3]   ███░░░░░░░░░ EM ANDAMENTO
Fase 3 — Refatoração           [Sprint 4–5]   ░░░░░░░░░░░░ FUTURA
Fase 4 — Evolução Funcional    [Sprint 6–7]   ░░░░░░░░░░░░ FUTURA
```

---

## Fase 1 — Estabilização

> **Status: CONCLUÍDA**  
> Estabelecer o MVP funcional em produção com as features centrais do negócio operando de forma confiável.

---

### Sprint 0 — MVP em Produção

**Objetivo estratégico:** Entregar uma ferramenta operacional funcional em produção antes de otimizar.

**Objetivo:** Colocar o sistema funcional no ar com as operações essenciais de uma assistência técnica.

**Motivação:** O time precisava de uma ferramenta operacional imediatamente para substituir planilhas e processos manuais. O foco foi na entrega rápida das funcionalidades core, aceitando dívida técnica inicial.

**Arquivos envolvidos:**
- `app.py` — inicialização, schema DB, registro de blueprints
- `irflow_blueprints_api.py` — todos os endpoints REST
- `irflow_os.py` — lógica de negócio de OS
- `irflow_blueprints_auth.py` — autenticação
- `frontend/src/App.jsx` — roteamento e guards
- `frontend/src/pages/` — Login, Dashboard, Orders, NewOrder, EditOrder, Stock
- `Dockerfile`, `fly.toml` — infraestrutura de deploy

**Critérios de aceitação:**
- [ ] Login e controle de sessão funcionando
- [ ] CRUD completo de Ordens de Serviço
- [ ] Controle de estoque com movimentações
- [ ] Tabela de preços por modelo/reparo
- [ ] Relatórios básicos (IR Phones, Técnicos)
- [ ] Backup manual e automático
- [ ] Deploy em Fly.io estável

**Testes obrigatórios:**
- Smoke test de todas as rotas REST (`smoke_test_full.py`)
- E2E: login, criação de OS, criação de item de estoque

**Riscos:**
- SQLite em prod sem replicação
- Ausência de CI/CD — regressões sem detecção automática

**Definition of Done:**
- Sistema acessível em produção via URL pública
- Todas as rotas retornam 200/esperado nos smoke tests
- Operação real de OS funcionando end-to-end sem erros críticos

---

### Sprint 1 — Correções Críticas e Shopping List

**Objetivo estratégico:** Garantir que o fluxo central de OS seja confiável antes de crescer.

**Objetivo:** Resolver bugs críticos identificados em auditoria pós-deploy e entregar o módulo de lista de compras.

**Motivação:** A auditoria de abril/2026 identificou 4 bugs bloqueantes no fluxo de OS. O módulo de Shopping List era a próxima prioridade de negócio para rastrear necessidade de peças.

**Arquivos envolvidos:**
- `irflow_blueprints_api.py` — endpoint `GET /api/precos/sugerir`, `shopping_list` CRUD
- `frontend/src/pages/NewOrder.jsx` — auto-fill `valor_cobrado`
- `frontend/src/pages/EditOrder.jsx` — auto-fill com flag `initialized`, fix campo `cor`
- `frontend/src/api/client.js` — fix URL PDF IR Phones, fix `historico-cliente`, client `shoppingList`
- `frontend/src/pages/Compras.jsx` — página de lista de compras
- `frontend/src/components/ui/EditShoppingItemModal.jsx` — modal de edição
- `frontend/src/components/shopping/ShoppingModal.jsx` — modal de adição

**Critérios de aceitação:**
- [ ] `valor_cobrado` auto-preenchido ao selecionar modelo + reparo em OS nova
- [ ] `valor_cobrado` não sobrescrito ao abrir OS existente para edição
- [ ] PDF IR Phones exportado corretamente
- [ ] Histórico de cliente sem erro 404
- [ ] Campo `cor` limpo ao trocar modelo em EditOrder
- [ ] CRUD da lista de compras funcionando com workflow de status
- [ ] Modal de edição de item de compra operacional
- [ ] `.env` removido do repositório

**Testes obrigatórios:**
- Teste do endpoint `GET /api/precos/sugerir` com diferentes combinações modelo/reparo
- E2E: criar OS e verificar auto-preenchimento de preço
- Smoke test do módulo shopping list (`test_shopping_list.py`)

**Riscos:**
- Flag `initialized.current` no EditOrder pode ter edge cases com carregamento assíncrono
- Workflow de status da shopping list não validado com o time operacional

**Definition of Done:**
- Todos os 4 bugs do `.TESTING_REPORT.md` com status ✅ IMPLEMENTADO
- Shopping List acessível e funcional em produção
- Nenhuma regressão nas funcionalidades do Sprint 0

---

## Fase 2 — Infraestrutura de Qualidade

> **Status: EM ANDAMENTO**  
> Antes de qualquer nova feature, o projeto precisa de uma base confiável: CI, testes e observabilidade mínima.
> Sprint 2.2 (primeiros testes — login/logout/sessão) concluída em 2026-07-07. Sprint 2.7 (2026-07-11)
> fechou a meta de cobertura (43%, gate bloqueante) e corrigiu um bug real encontrado no processo
> (KI-016). Resta `.env.example` e Playwright no CI antes de considerar a Sprint 2 encerrada. Ver
> `docs/operations/SPRINTS/SPRINT_02.md`.

---

### Sprint 2 — Pipeline de CI e Testes Backend

**Objetivo estratégico:** Construir a infraestrutura de qualidade que permitirá crescer sem regredir.

**Objetivo:** Implementar GitHub Actions com lint e testes automatizados no backend. Atingir 40% de cobertura nas rotas críticas.

**Motivação:** Sem CI, qualquer commit pode introduzir regressões que chegam a produção sem detecção. Com o crescimento do número de módulos, a manutenção manual de qualidade não é sustentável.

**Arquivos envolvidos:**
- `.github/workflows/ci.yml` — pipeline a criar
- `tests/` — diretório de testes pytest a criar
- `tests/conftest.py` — fixtures isoladas com banco em memória
- `tests/test_os.py` — testes de OS
- `tests/test_auth.py` — testes de autenticação
- `tests/test_pricing.py` — testes de tabela de preços e `sugerir`
- `tests/test_shopping.py` — testes da shopping list
- `.env.example` — documentação de variáveis de ambiente
- `requirements-dev.txt` — pytest, pytest-cov, coverage

**Critérios de aceitação:**
- [x] GitHub Actions executa em cada push para `main` e PRs
- [x] Pipeline inclui: lint (flake8/ruff), testes (pytest), build frontend
- [x] Cobertura >= 40% nas rotas de OS, auth, preços e shopping list — 43% global, atingida em 2026-07-11 (Sprint 2.7), gate bloqueante em `pyproject.toml`/`ci.yml`
- [x] Testes rodam com banco SQLite em memória (sem depender do `database.db`) — via `IR_FLOW_DATA_DIR`, ver `tests/conftest.py`
- [ ] Playwright E2E incluído no CI em modo headless
- [ ] `.env.example` documentado com todas as variáveis necessárias
- [ ] Badge de CI no README

**Testes obrigatórios:**
- `test_auth.py`: login válido, credenciais inválidas, acesso sem sessão
- `test_os.py`: criar OS, editar status, deletar, histórico de cliente
- `test_pricing.py`: `GET /api/precos/sugerir` com modelo/reparo existente e inexistente
- `test_shopping.py`: CRUD completo + transições de status
- E2E Playwright: fluxo de login + criação de OS completo

**Riscos:**
- Testes podem requerer refatoração do `app.py` para injetar banco em memória — risco de quebrar inicialização existente
- Pipeline de Playwright no CI pode ser instável (flaky tests)
- Sem coverage de integração MercadoPhone (depende de API externa)

**Definition of Done:**
- CI verde em 100% dos commits do sprint
- Cobertura >= 40% reportada pelo pytest-cov
- Nenhum teste flaky identificado (0 falhas intermitentes em 5 execuções consecutivas)
- `.env.example` revisado e aprovado pelo time

---

### Sprint 3 — Segurança e Observabilidade

**Objetivo estratégico:** Eliminar vulnerabilidades ativas antes de qualquer expansão funcional.

**Objetivo:** Corrigir vulnerabilidades de segurança conhecidas e implementar observabilidade básica (logs estruturados + alertas de erro).

**Motivação:** O sistema está em produção com dados reais de clientes. Rate limiting ausente, tokens sem expiração e falta de logs estruturados são riscos operacionais que precisam ser resolvidos antes de qualquer expansão funcional.

**Arquivos envolvidos:**
- `irflow_blueprints_auth.py` — rate limiting em `/api/auth/login`
- `irflow_blueprints_api.py` — expiração de tokens de checklist, headers de segurança
- `app.py` — logging estruturado, integração Sentry (ou similar)
- `irflow_os.py` — logs de auditoria em operações críticas
- `frontend/src/` — headers CSP, sanitização de inputs

**Critérios de aceitação:**
- [ ] Rate limiting em `/api/auth/login`: máx 5 tentativas/minuto por IP
- [ ] Tokens de checklist expiram após 30 dias (configurável)
- [ ] Logs estruturados em JSON para todas as operações críticas (criação/edição/deleção de OS)
- [ ] Headers de segurança HTTP: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- [ ] Alertas de erro em produção (Sentry ou similar) com threshold configurado
- [ ] Sem segredos hardcoded no código (validado por `git secrets` ou similar)

**Testes obrigatórios:**
- `test_auth.py`: verificar bloqueio após 5 tentativas falhas
- `test_checklist.py`: verificar que token expirado retorna 401/403
- Teste de smoke com headers de segurança
- Teste de auditoria: verificar que log é gerado ao criar/editar OS

**Riscos:**
- Rate limiting por IP pode bloquear usuários legítimos atrás de NAT
- Expiração de tokens pode quebrar checklists já compartilhados com clientes
- Integração com serviço externo de monitoramento adiciona dependência de terceiro

**Definition of Done:**
- Todos os itens de segurança validados por revisão manual de código
- Nenhum falso positivo de rate limiting em uso normal (validado com QA)
- Logs visíveis e consultáveis em produção
- Nenhum segredo detectado no histórico git (audit passado)

---

## Fase 3 — Refatoração Arquitetural

> **Status: FUTURA**  
> Eliminar dívida técnica estrutural que impede escalabilidade e manutenibilidade do código.

---

### Sprint 4 — Decomposição do Módulo API e Migrations Formais

**Objetivo estratégico:** Separar completamente regras de negócio da camada HTTP.

**Objetivo:** Quebrar `irflow_blueprints_api.py` (~130KB) em módulos coesos por domínio. Substituir `ALTER TABLE` ad-hoc por sistema de migrations versionado.

**Motivação:** O módulo de API monolítico torna difícil encontrar código, aumenta o risco de conflitos em merges e viola o princípio de responsabilidade única. As migrations ad-hoc com try/except tornam impossível saber o estado real do schema em diferentes ambientes.

**Arquivos envolvidos:**
- `irflow_blueprints_api.py` — a ser decomposto em:
  - `irflow_api_os.py` — endpoints de Ordens de Serviço
  - `irflow_api_estoque.py` — endpoints de Estoque
  - `irflow_api_shopping.py` — endpoints de Shopping List
  - `irflow_api_relatorios.py` — endpoints de Relatórios
  - `irflow_api_admin.py` — endpoints de usuários, backup, configurações
  - `irflow_api_integracoes.py` — endpoints MercadoPhone
- `migrations/` — diretório de migrations a criar
- `migrations/001_initial_schema.sql` — schema inicial documentado
- `migrations/002_shopping_list.sql` — adição da tabela shopping_list
- `app.py` — atualizar registro de blueprints

**Critérios de aceitação:**
- [ ] `irflow_blueprints_api.py` original removido — todos os endpoints migrados para módulos por domínio
- [ ] Cada módulo de API tem <= 500 linhas
- [ ] Sistema de migrations executa em ordem e é idempotente
- [ ] Schema do banco documentado em `migrations/` reflete o estado atual de produção
- [ ] Nenhuma regressão nos testes do Sprint 2
- [ ] CI verde após refatoração

**Testes obrigatórios:**
- Todos os testes existentes do Sprint 2 devem passar sem alteração
- Smoke test completo após decomposição
- Verificar que nenhum endpoint foi perdido na migração (diff de rotas antes/depois)

**Riscos:**
- Refatoração de módulo crítico com alta chance de regressão
- Importações circulares entre módulos novos
- Migrations podem divergir do schema real em produção se `ALTER TABLE` ad-hoc não for mapeado completamente

**Definition of Done:**
- Todos os testes automatizados passando
- Revisão de código por pelo menos um revisor (PR review)
- Produção estável por 48h após deploy

---

### Sprint 5 — Paginação, Performance e Refatoração Frontend

**Objetivo estratégico:** Preparar o sistema para crescimento de volume sem degradação de performance.

**Objetivo:** Implementar paginação na listagem de OS, otimizar queries críticas e organizar o frontend com separação clara de responsabilidades.

**Motivação:** Com crescimento do volume de dados, a ausência de paginação causará degradação de performance. O frontend mistura lógica de negócio diretamente nas pages, dificultando testes e reutilização.

**Arquivos envolvidos:**
- `irflow_blueprints_api.py` (ou módulo decomposto) — paginação em `GET /api/ordens`
- `frontend/src/pages/Orders.jsx` — suporte a paginação
- `frontend/src/hooks/` — diretório a criar para hooks customizados
- `frontend/src/hooks/useOrders.js` — lógica de listagem extraída da page
- `frontend/src/hooks/useShopping.js` — lógica de shopping extraída
- `database.db` — índices adicionais em `os(status, data, tecnico)`

**Critérios de aceitação:**
- [ ] `GET /api/ordens` suporta `?page=N&per_page=50` com resposta paginada
- [ ] Frontend exibe paginação na listagem de OS
- [ ] Tempo de resposta `GET /api/ordens` < 200ms com 10.000+ registros
- [ ] Lógica de negócio extraída de `Orders.jsx` para hooks customizados
- [ ] Índices de banco adicionados e verificados com `EXPLAIN QUERY PLAN`

**Testes obrigatórios:**
- `test_os.py`: verificar resposta paginada com `page` e `per_page`
- Teste de performance: `GET /api/ordens` com dataset de 10.000 registros
- Teste de regressão: filtros existentes funcionando com paginação

**Riscos:**
- Paginação pode quebrar integrações que esperam todos os resultados de uma vez
- Hooks customizados podem introduzir bugs sutis de estado assíncrono

**Definition of Done:**
- Listagem de OS funcional com paginação em produção
- Performance validada com carga real
- Nenhuma regressão nos filtros e busca existentes

---

## Fase 4 — Evolução Funcional

> **Status: FUTURA**  
> Expansão das capacidades do sistema com novas features de alto valor para o negócio.

---

### Sprint 6 — Notificações e Fluxo de Status Automatizado

**Objetivo estratégico:** Transformar o sistema de passivo a proativo — de ferramenta a parceiro de operação.

**Objetivo:** Implementar notificações em tempo real para mudanças de status de OS e automatizar transições de status baseadas em eventos.

**Motivação:** Atualmente o sistema é completamente passivo — nenhuma notificação é disparada quando uma OS muda de status, quando uma peça chega ou quando um prazo de garantia se aproxima. Isso força o time a checar o sistema constantemente.

**Arquivos envolvidos:**
- `irflow_blueprints_api.py` / `irflow_api_os.py` — webhooks e eventos
- `irflow_notifications.py` — módulo a criar
- `frontend/src/` — notificações toast em tempo real (polling ou WebSocket)
- `app.py` — configuração de WebSocket ou SSE

**Critérios de aceitação:**
- [ ] Notificação disparada quando OS muda de status (para todos os usuários conectados)
- [ ] Alerta visual quando garantia vence em <= 7 dias
- [ ] Notificação quando item de shopping list muda para `RECEBIDO`
- [ ] Configuração de notificações por perfil de usuário

**Testes obrigatórios:**
- Teste de integração: mudança de status dispara evento
- Teste E2E: notificação aparece no navegador em <= 3s após mudança
- Teste de carga: 10 usuários simultâneos recebendo notificações

**Riscos:**
- WebSocket em Fly.io requer configuração adicional
- Polling tem impacto de performance — decidir arquitetura antes de implementar

**Definition of Done:**
- Notificações funcionando para todos os perfis em produção
- Nenhum impacto perceptível de performance (< 5% de aumento de CPU)
- Documentação da arquitetura de notificações

---

### Sprint 7 — Relatórios Avançados e Exportação

**Objetivo estratégico:** Dar ao gestor visibilidade estratégica sobre o negócio através de dados históricos.

**Objetivo:** Expandir o módulo de relatórios com análises por período, comparativos e exportação em múltiplos formatos.

**Motivação:** Os relatórios atuais são básicos e não permitem análise de tendências. O gestor precisa de visibilidade sobre evolução de receita, desempenho por técnico e sazonalidade de reparos para tomar decisões estratégicas.

**Arquivos envolvidos:**
- `irflow_reports.py` — novos relatórios e agregações
- `irflow_blueprints_api.py` / `irflow_api_relatorios.py` — novos endpoints
- `frontend/src/pages/Reports.jsx` — nova interface de relatórios
- `frontend/src/components/dashboard/` — novos widgets de chart
- Dependência nova: `openpyxl` para exportação Excel

**Critérios de aceitação:**
- [ ] Relatório de tendência: receita mensal dos últimos 12 meses
- [ ] Comparativo entre técnicos (quantidade, receita, margem)
- [ ] Análise de reparos mais frequentes por período
- [ ] Exportação em Excel além de PDF
- [ ] Filtro por período customizado (date range picker) em todos os relatórios

**Testes obrigatórios:**
- `test_relatorios.py`: verificar agregações com dados conhecidos
- E2E: gerar e baixar PDF e Excel para cada tipo de relatório
- Teste de carga: relatório anual com 10.000 OS em < 5s

**Riscos:**
- Queries de agregação em SQLite podem ser lentas com volume alto
- Interface de relatórios complexa pode demandar mais de uma sprint

**Definition of Done:**
- Todos os novos relatórios disponíveis em produção
- Exportação Excel funcional
- Performance validada com dataset real
- Documentação de uso para o gestor

---

## Critérios Globais de Definition of Done

Aplicáveis a **todas** as sprints:

1. Todos os testes automatizados passando (CI verde)
2. Cobertura de testes não regrediu em relação à sprint anterior
3. Nenhum bug de severidade Alta ou Crítica aberto
4. Código revisado em PR (ao menos um revisor)
5. Documentação atualizada (`PROJECT_STATUS.md` e `ROADMAP.md`)
6. Deploy em produção estável por >= 24h sem erros críticos nos logs
7. Commits seguindo Conventional Commits (`feat:`, `fix:`, `refactor:`, etc.)
