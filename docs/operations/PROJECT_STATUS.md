# PROJECT_STATUS

**Projeto:** Fluxoly Platform
**Responsável:** Principal Software Engineer
**Branch principal:** `main`
**Ambiente de produção:** Render (backend) — `https://irflow-backend.onrender.com` · Vercel (frontend) — `https://assistencia-system.vercel.app`

**Última revisão:** 2026-07-30
**Próxima revisão:** Deploy em produção + observação com `IR_FLOW_DEBUG_CONN_TRACE=1` (INC-001, ver abaixo) — ação do usuário (CTO), fora do alcance desta sessão. Sequência: 🟡 INC-001 (Branch A + Branch C mergeadas e enviadas 2026-07-27, aguardando deploy/observação; Branch B condicionada à evidência) → ✅ C1.3.5 (Rastreabilidade Individual de Estoque, concluída 2026-07-27) → ✅ Vendas MVP (concluída 2026-07-27, ver abaixo) → ✅ Sprint Infra 1.1 — CI Verde (concluída 2026-07-27, KI-026/R-10/R-11, ver abaixo) → ✅ Sprint Vendas 1.1 — Histórico + Detalhe (concluída 2026-07-27, ver abaixo) → ✅ V1.2 — Cancelamento (concluída 2026-07-27, ver abaixo) → ✅ ADR-010 — ciclo de feature com regra de negócio (concluída 2026-07-28) → ✅ V1.3 — Descontos e Aprovação (concluída 2026-07-28, ver abaixo) → ✅ V1.4 — Comissão (concluída 2026-07-29, ver abaixo, inclui revogação do bloqueio de desconto da V1.3) → ✅ Fix de responsividade do Dashboard em MacBook (concluído 2026-07-30, ver abaixo) → ✅ V1.5 — Garantia (concluída 2026-07-30, ver abaixo)

---

## ✅ INC-002 — Ordens de Serviço duplicadas após sincronização com Mercado Phone (RESOLVIDO)

**Ver `docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md` para o relatório completo.**

Reportado pelo usuário (CTO) em 2026-07-23 — OS "1072" (número externo do Mercado Phone,
`id_externo_integracao`) aparentemente duplicada. Causa estrutural: a thread de sincronização do
Mercado Phone iniciava uma vez por processo do Gunicorn, sem coordenação entre processos — com
`--workers 2` em produção, dois processos rodavam o sync ao mesmo tempo, gerando uma corrida clássica
(TOCTOU) que duplicava OS, já que o schema não tinha `UNIQUE` em
`(origem_integracao, id_externo_integracao)`. Mesma classe de bug já corrigida em KI-001 (rate
limiting) para outro recurso.

**Resolução completa em 3 etapas:**
1. **Lock cross-processo** (`irflow_mercadophone.py`, lease de 90s via tabela já existente) — elimina o
   mecanismo que gera novas duplicatas.
2. **Confirmado e limpo em produção**: 3 pares duplicados encontrados (`id_externo_integracao` 1083,
   1093, 832). Dois eram duplicatas idênticas sem filhos (limpeza direta); um (832) tinha as duas linhas
   editadas de forma divergente após a duplicação — peça consumida duas vezes do estoque, reparo extra,
   checklist próprio em cada uma — exigiu decisão humana sobre qual linha refletia a realidade antes de
   remover a outra. 3 linhas + filhos órfãos removidos, verificado `[]` na consulta pós-limpeza.
3. **`UNIQUE INDEX`** em `(origem_integracao, id_externo_integracao)` (`app.py::criar_tabelas()`) —
   proteção definitiva no banco, independente do lock, aplicada automaticamente no próximo deploy.

9 novos testes no total (`test_inc002_mercado_phone_sync_lock.py`, `test_inc002_unique_index_os_mercado_phone.py`),
489 no total do projeto, `ruff check .` limpo, zero regressão em cada etapa.

Achado ainda em aberto (não confirmado, registrado em INC-001): `sincronizar_mercado_phone()` mantinha
uma única transação aberta por todo o ciclo de sync, rodando em 2 processos concorrentes — candidato
mais forte para a causa de INC-001 do que qualquer coisa testada até agora ali. Migração arquitetural
para worker/cron dedicado (em vez de lock) registrada como melhoria futura, não decidida, requer ADR.

---

## 🟡 INC-001 — `database is locked` (P0, vetores confirmados corrigidos, causa raiz não confirmada em runtime)

**Ver `docs/operations/INCIDENTS/INC-001-database-is-locked.md` para o relatório completo.**

Reportado pelo usuário (CTO) em 2026-07-23 ao editar/criar OS e cadastrar/alterar estoque, de forma
intermitente. Investigação encontrou: WAL e timeout já configurados corretamente (descartados como
causa); as 4 rotas citadas como sintoma já têm `try/except/finally` corretos (não são a origem do
vazamento, só a vítima do lock, se a hipótese estiver certa). Hipótese específica de conexão aninhada
dentro das 4 rotas de OS/Estoque (auditoria/movimentação abrindo `conectar()` de novo) foi investigada e
**descartada** por leitura de código.

Após releitura completa (não só grep) das rotas candidatas: as 4 rotas de `/api/shopping-list*`
reclassificadas de "sem proteção" para **risco estrutural, não vazamento confirmado** (fecham a conexão
em todo caminho, via padrão não idiomático — `except` amplo + `close()` manual).

**Corrigido (2026-07-23):** `POST /api/auth/login` — hotfix isolado em
`hotfix/conexao-login-database-locked`, mantido independente do resultado da investigação. Provado por
teste automatizado. 480 testes, `ruff check .` limpo, zero regressão.

**Corrigido (2026-07-27):** as 4 rotas de checklist (`GET/POST /api/ordens/<id>/checklist[/token]`,
`GET/POST /api/checklist/<token>` — as duas últimas públicas, sem login), único risco confirmado por
leitura de código que ainda restava — mesmo padrão do hotfix de login, branch
`fix/checklist-conexao-database-locked`, mergeada em `main`. 533 testes, `ruff check .` limpo.

**Instrumentação transparente pronta e mergeada (2026-07-27):** `_ConexaoRastreada` (`app.py`), gated
por `IR_FLOW_DEBUG_CONN_TRACE`, zero impacto desligada, delega tudo que não instrumenta à conexão real
(`__getattr__`/`__setattr__`) — critérios de aceitação C-1 a C-9 documentados. Branch
`chore/inc-001-instrumentacao-transparente`, mergeada em `main` (substitui a branch anterior
`chore/inc-001-instrumentacao-conexoes`, que usava `print()` e nunca foi mergeada). 541 testes,
`ruff check .` limpo. Duas rodadas de reprodução por carga local (antes desta branch) **não
reproduziram** o erro — causa raiz segue não confirmada em runtime.

**Aguardando (ação do usuário, fora do alcance desta sessão):** deploy em produção — recomendado em duas
etapas (deploy com a flag desligada, validar saúde do sistema, só depois ligar
`IR_FLOW_DEBUG_CONN_TRACE=1` e redeployar) — seguido de alguns dias de observação real. A Branch B
(reduzir a transação de `sincronizar_mercado_phone()`) fica **condicionada à evidência** coletada nessa
observação, não decidida por suspeita.

---

## Estado Atual

| Dimensão           | Status                          |
|--------------------|---------------------------------|
| Produção           | Operacional (Render + Vercel)    |
| Backend            | Estável — Flask + SQLite (WAL)  |
| Frontend           | Estável — React 19 + Vite       |
| CI/CD              | Presente e ativo (`.github/workflows/ci.yml` — lint, testes, frontend, build, cobertura, docker build). Cobertura bloqueante (`fail_under = 60`, elevado de 40 na Sprint CI/CD 1.1 — Hardening, 2026-07-31). Job `Lint` (Ruff, backend) verde em `main` desde 2026-07-21 (KI-017 resolvido, `ruff check .` → 0 erros). Workflow `CI` como um todo verde desde 2026-07-27 (Sprint Infra 1.1) — histórico de por que não estava, ver KI-026 (resolvida). `main` protegida, exige 6 status checks antes de merge (Lint, Backend Tests, Frontend Quality, Frontend Build, Coverage Report, Docker Build — R-10/R-11 mitigados, `Docker Build` adicionado na Sprint CI/CD 1.1; endurecimento adicional em TD-13) |
| Cobertura de testes| 65.22% global (`pytest --cov`, 2026-07-31), 682 testes (ver Cobertura de Testes) |
| Dívida técnica     | Alta                            |
| Segurança          | Melhor — Sprint Segurança 1.0 + 2º scan Aikido (2026-07-25), ambos fechados: `FLASK_SECRET_KEY` rotacionada em produção, autorização de OS/Estoque por perfil, headers HTTP, Docker non-root (validado com `docker build`/`docker run` reais), gunicorn/deps atualizadas — ver `docs/security/SECURITY_AUDIT_2026-07.md` |
| Observabilidade    | Logs estruturados em JSON, correlation ID por request, `/health`/`/ready`, métricas Prometheus (`/metrics`, modo multiprocess validado com Docker real), Sentry ativo nos dois lados (backend + frontend novo, `environment`/`release` automáticos, conta criada e captura real validada em 2026-07-30) — ver `docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md` e `docs/engineering/plans/PLAN-Observabilidade-Sentry-Frontend.md`. Falta configurar `SENTRY_DSN`/`VITE_SENTRY_DSN` nos dashboards Render/Vercel para ativar em produção |

O sistema está em produção e cobre o ciclo completo de uma assistência técnica: abertura de OS, controle de estoque, tabela de preços, lista de compras, garantias, relatórios e backup. Além disso, a Sprint 3 fechou quatro lacunas de segurança (rate limiting de login, expiração de sessão por inatividade, auditoria central reutilizável, recuperação de senha via token do admin) e a Sprint P0.1 entregou o primeiro domínio de produto (Clientes) seguindo pela primeira vez a convenção controller/service/repository documentada em `ENGINEERING_GUIDE.md` §3.1. Em 2026-07-20, antes do início do Épico Vendas (decisão do usuário — CTO), o lint vermelho em `main` (KI-017) foi corrigido em 6 commits atômicos na branch `chore/fix-ruff-lint-ki-017` — o CI estava bloqueado para qualquer PR desde antes da Sprint 3. No processo, também foi resolvido KI-014 (bloco de código morto duplicado em `irflow_blueprints_api.py`). No mesmo dia, a Sprint Comercial 0.1 entregou o primeiro passo do Épico Vendas: domínio `produtos` (catálogo comercial — iPhone/Apple Watch/AirPods/Acessório), separado do domínio Estoque (peças de reparo) por decisão de arquitetura investigada e confirmada com o usuário antes de implementar. Sem tela ainda — ver `docs/operations/SPRINTS/SPRINT_COMERCIAL_0.1.md`.

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

Restante da Sprint 2: `.env.example` (será fechado junto da Unidade 8 da Sprint 3, ver abaixo — mesma
variável de ambiente documentada nas duas frentes).

---

**Sprint 3 — Segurança e Observabilidade** (CONCLUÍDA em 2026-07-11, 4 unidades) e **Sprint P0.1 —
Fundações de Produto** (EM ANDAMENTO) rodando em paralelo, decisão do usuário (CTO) de não começar o
módulo de Vendas ainda e investir primeiro nas fundações reutilizáveis (Clientes, IMEI, camada de
serviços). Plano completo em `docs/operations/SPRINTS/` (a formalizar em `SPRINT_03.md` na conclusão).

- **Unidade 1 — Rate limiting em login (KI-001):** contador em tabela SQLite (`login_attempts`), não
  Flask-Limiter — o Gunicorn de produção roda com `--workers 2`, então memória de processo daria um
  limite mais fraco que o nominal. 5 tentativas/minuto por identificador (`Fly-Client-IP` →
  `X-Forwarded-For` → `remote_addr`). 7 testes.
- **Unidade 2 — Expiração de sessão por inatividade:** janela deslizante de 30 min
  (`IR_FLOW_SESSION_INACTIVITY_MINUTES`), um único ponto de checagem em `verificar_autenticacao()`
  cobrindo views legadas e `/api/*`. 11 testes.
- **Unidade 3 — Auditoria central:** tabela genérica `audit_log` (`irflow_audit.py`), não replica
  `shopping_list_logs` por domínio a cada feature nova. Sem consumidor até a Unidade 5. 5 testes.
- **Unidade 4 — Recuperação de senha:** token de uso único gerado pelo admin (não self-service por
  e-mail), expira em 24h, `secrets.token_urlsafe` como `gerar_token_checklist_os`. 10 testes.
- **Unidade 5 — Domínio Clientes:** `irflow_clientes_controller/service/repository.py` — primeira
  aplicação real da convenção de `ENGINEERING_GUIDE.md` §3.1. CRUD + busca/paginação, `os.cliente_id`
  aditivo sem backfill, exclusão bloqueada com OS vinculada (BR-023, BR-024). Sem tela ainda. 23 testes.
  Achado corrigido: `verificar_autenticacao()` só reconhecia bypass de `/api/*` pelo nome do blueprint
  `api.*` — um segundo blueprint sob `/api/*` caía na checagem de sessão legada; trocado para checar
  `request.path`, escala para qualquer domínio futuro sob `/api/*` sem precisar editar essa lista de novo.
- **Unidade 6 — Domínio `estoque_unidades` (IMEI):** `irflow_estoque_unidades_controller/service/repository.py`
  — segunda aplicação da convenção. Cadastro de unidade individual (bloqueado se `estoque.requer_imei=0`),
  transições manuais `disponivel ↔ em_reparo`, `em_reparo/devolvido → disponivel` (BR-025, BR-026).
  `reservado`/`vendido` existem no schema, sem uso — reservados para o futuro Vendas. Fecha o gap de
  marca de IMEI (`BRAND_IDENTITY.md` seção 2). Sem tela ainda. 20 testes.
- **Unidade 7 — Stub `irflow_vendas_service.py`:** arquivo só com docstring, sem rota/tabela/wiring —
  placeholder explícito para quando o épico Vendas for aprovado, referenciando Clientes e
  `estoque_unidades` como pré-requisitos já entregues.

- **Unidade 8 — `.env.example`:** pendente desde a Sprint 2 (T-10), fechado aqui — 26 variáveis
  documentadas (as ~24 já existentes em `app.py` + as 2 novas desta sprint), incluindo as injetadas
  automaticamente por plataforma de deploy, comentadas como referência. No processo, contagem real de
  KI-017 corrigida para 175 erros (repo inteiro, não só os 2 arquivos que a Sprint 3/P0.1 tocou).
- **Unidade 9 — Adendo `ENGINEERING_GUIDE.md` §3.1:** registra a interpretação "README de domínio =
  docstring no topo do `_service.py`" (já usada em Clientes e `estoque_unidades`) como precedente formal
  para os próximos domínios.

**Sprint 3 e Sprint P0.1 (fase de fundações do produto) concluídas em 2026-07-11** — 9 unidades, testes
subindo de 331 (fim da Sprint 2.7) para 407 (+76), cobertura 43% → 48%. Próximo passo, por decisão do
usuário: retomar o épico Vendas com as fundações (Clientes, IMEI, auditoria, camada de serviços) já
prontas.

---

**Sprint Comercial 0.1 — Catálogo de Produtos (CONCLUÍDA em 2026-07-20, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_0.1.md`):** primeira tarefa do Épico Vendas propriamente dito,
divisão de trabalho Frente A (usuário, relacionamento com cliente)/Frente B (Claude, implementação em
tarefas pequenas e fechadas). Domínio `produtos` — `irflow_produtos_controller/service/repository.py`,
terceira aplicação da convenção de `ENGINEERING_GUIDE.md` §3.1. `categoria` (iPhone/Apple Watch/AirPods/
Acessório) e `condicao` (Novo/Seminovo/Vitrine) validadas contra lista fechada e **rejeitadas** com 400
quando inválidas — decisão deliberada de não repetir a coerção silenciosa de
`_normalizar_tipo_estoque`/`_normalizar_qualidade_estoque`, que já causou KI-015 e KI-016. Margem nunca
persistida, sempre calculada no service. Sem tela ainda. 27 testes. Testes subindo de 407 para 434,
cobertura subindo de 48% para 50%. `VENDAS.md` recebeu nota sinalizando que `vendas.estoque_unidade_id` precisa
ser revisado no Sprint Comercial 0.2 (rastreamento por unidade/IMEI de produtos, ainda não desenhado).

**Sprint Comercial 1.1 — Tela Produtos (CONCLUÍDA em 2026-07-21, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.1.md`):** primeira tela do Épico Vendas — sequenciamento
decidido pelo usuário (CTO) pela ótica de impacto no cliente (backend/testes já prontos, zero mudança
de banco), não pela ótica de implementação. `frontend/src/pages/Produtos.jsx` consome integralmente
`/api/produtos*`, sem tocar backend/schema. Ajuste de produto pedido antes da implementação: cards de
resumo (Produtos/Seminovos/Vitrine), badges de categoria com emoji, busca única combinando todos os
campos relevantes (client-side — o parâmetro `q` do backend só cobre descrição/modelo/SKU), coluna
"Unidades" com placeholder reservando espaço para rastreamento por IMEI de uma sprint futura sem
redesenho posterior. Escrita restrita a `admin` no frontend, espelhando a permissão já existente no
backend. Validado manualmente ponta a ponta (servidor real + banco isolado, nunca `database.db`,
navegador dirigido via Playwright) — login, listagem, busca combinada, criar/editar/excluir, e visão
restrita do perfil `vendedor` (sem botão/ícones de escrita). Sem framework de teste de
componente/unitário no frontend ainda (0% de cobertura unitária) — não expandido nesta sprint por
decisão de manter o escopo pequeno.

**Hotfix H-002 — Catálogo iPhone 17 (RESOLVIDO em 2026-07-21, KI-018):** `IPHONE_MODELS`/
`IPHONE_COLORS` (`irflow_reference_data.py`) atualizados com iPhone 17/17 Air/17 Pro/17 Pro Max —
bloqueio operacional real (impossível abrir OS para esses aparelhos). Cores usam lista genérica
por decisão deliberada (sem necessidade comercial ainda de nome exato). Comentário de fonte única
adicionado acima de `IPHONE_MODELS`. Branch própria a partir de `main`, mergeada separada da feature.

**Merge em `main` (2026-07-21):** `fix/catalogo-iphone-17` e `feat/produtos-catalogo` mesclados nesta
ordem. O merge da Tela Produtos trouxe consigo, sem ser plano desta sessão, o fechamento efetivo de
KI-017/KI-014 em `origin/main` — a branch `feat/produtos-catalogo` havia sido construída em cima de
`chore/fix-ruff-lint-ki-017`, cujo merge em `origin/main` nunca havia de fato acontecido apesar da
documentação já registrar como concluído em 2026-07-20 (achado reportado ao usuário antes de
completar o merge; aceito deliberadamente trazer os dois juntos, já que nenhum é código novo desta
sessão). `ruff check .` → 0 erros no repositório inteiro, 434 testes (407 + 27 de `test_produtos.py`)
passando, `npm run build`/`npm run lint` sem erros novos — confirmado após o merge, não só antes.

**Sprint Comercial 1.2 — Tela Clientes (CONCLUÍDA em 2026-07-21, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.2.md`):** segunda tela do Épico Vendas.
`frontend/src/pages/Clientes.jsx` consome integralmente `/api/clientes*` (Sprint 3 Unidade 5), sem
tocar backend/schema. Além do CRUD (padrão igual à Tela Produtos — cards, busca única, permissão
espelhando o backend: criar/editar para qualquer perfil autenticado, excluir só `admin`), inclui um
painel de Perfil do Cliente com Histórico de OS e Garantias reais, montado a partir de dois endpoints
já existentes (`GET /api/ordens/historico-cliente`, `GET /api/garantias?q=`) — nenhum endpoint novo.
Achado durante a investigação: `os.cliente_id` existe no schema desde a Sprint P0.1 mas nenhum fluxo
real o preenche hoje (só testes escrevem nele direto no banco); o histórico de OS depende do
endpoint legado por correspondência de nome, mesma limitação de antes, agora só mais visível na UI.
"Compras" aparece como placeholder vazio, como antecipado pelo usuário — módulo de Vendas ainda não
existe. Validado manualmente ponta a ponta (servidor real + banco isolado + navegador dirigido via
Playwright, dados de OS/garantia semeados via API para exercitar o perfil).

**Sprint Comercial 1.3 — Tela Unidades Serializadas (PAUSADA desde 2026-07-21, ver ADR-007; retomada
2026-07-21 após RC):** ao investigar a implementação, ficou claro que `estoque_unidades` só cobria
peças de `estoque` (assistência) — não o cenário real que a tela deveria resolver (buscar um aparelho
de revenda do catálogo `produtos` por IMEI). Decisão de arquitetura registrada e **aceita pelo usuário
(CTO)** em `ADR-007.md`: `estoque_unidades` **evoluiu** para o domínio `unidades_serializadas` (dados
preservados, não descartados), fonte única de verdade para qualquer unidade física rastreada por
IMEI/serial. Dois princípios de arquitetura fixados junto da decisão: **Regra de Ouro** (um IMEI/serial
= uma unidade, nunca duplicada entre domínios — cada domínio consome e transiciona o mesmo registro) e
**Princípio da Responsabilidade de Transição** (cada domínio só pode transicionar os estados que lhe
pertencem — ex.: Vendas é dona de `Disponível → Reservado → Vendido`, Assistência de `Em Garantia → Em
Reparo → Disponível`; Garantias só consulta/registra eventos). Rename feito na mesma migração que
generaliza a origem (`produto_id` nullable, `estoque_id` agora opcional), sem alias de compatibilidade
(decisão deliberada do CTO — zero consumidores hoje).

**Migração implementada e validada em RC (2026-07-21)** — branch `feat/unidades-serializadas`
(commit `a5a0c8e`), mergeada em `main`. Ver `docs/engineering/migrations/MIGRATION_unidades_serializadas.md`
para o resultado completo do RC (integridade, idempotência, smoke test, todos verdes contra cópia real
de produção). **Achado relevante do RC:** o backup de produção usado revelou que produção está ~10 dias
atrás de `main` — sem a tabela `produtos` nem nenhuma feature da Sprint Comercial 0.1+. Decisão do CTO:
antes do deploy, fazer um **RC do sistema inteiro** (não só desta migração), cobrindo login, dashboard,
OS, estoque, compras, clientes, produtos, backup, MercadoPhone, usuários e IMEI — executado
imediatamente antes do próximo deploy, não antes de retomar a Sprint Comercial 1.3 (decisão do CTO,
2026-07-21: aproveitar os dias até a próxima reunião para entregar telas, não para o RC completo).
Migração do `database.db` real de produção ainda pendente — passo de deploy separado, checklist em
`MIGRATION_unidades_serializadas.md`.

**Sprint Comercial 1.3.1 — Tela de Listagem (CONCLUÍDA e mergeada em `main` em 2026-07-22):**
`frontend/src/pages/UnidadesSerializadas.jsx` — busca única por IMEI/modelo/produto, cards de resumo
(Unidades/Disponíveis/Em Reparo), badges de origem (Estoque/Produto) e status. Backend enriquecido com
`LEFT JOIN` em `estoque`/`produtos` só para exibição (label de origem, categoria/marca quando aplicável)
— nenhuma mudança de filtro/regra de negócio. 449 testes no total (29 em `test_unidades_serializadas.py`),
`ruff check .` limpo. Revisado e mergeado por Claude nesta sessão (trabalho de
implementação de sessão anterior) — validado manualmente rodando o app com unidades seedadas via API a
partir de `estoque` e de `produtos`, confirmando busca cruzada e badges de origem corretas para os
dois casos.

**Sprint Técnica — Centralização de Referências (CONCLUÍDA em 2026-07-22, pedido do usuário — CTO):**
investigação encontrou uma única duplicação real: `PRODUTOS_CATEGORIAS`/`PRODUTOS_CONDICOES` já eram
fonte única no backend, mas nunca expostas em `GET /api/constantes` — `Produtos.jsx` mantinha cópia
própria hardcoded, com risco de divergir quando uma categoria/condição nova fosse adicionada só no
backend. Corrigido: API expõe as duas listas, frontend consome (lista antiga mantida só como fallback
defensivo). `IPHONE_MODELS`/`IPHONE_COLORS` já eram fonte única e já expostas — confirmado, nenhuma
mudança necessária. "Fabricantes" não existe como lista fechada hoje (campo `marca` é texto livre em
`produtos`) — criar uma seria feature nova, não consolidação, fora de escopo. 450 testes (novo teste
confirmando o shape de `/api/constantes`), validado manualmente rodando o app — dropdown de categoria
no modal de Produtos populado via API.

**Sprint Comercial 1.3.2 — Detalhes da Unidade Serializada (CONCLUÍDA em 2026-07-22, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.2.md`):** ao clicar numa unidade na listagem (C1.3.1),
abre painel com IMEI, origem (produto/estoque), status, saúde da bateria, localização e histórico
completo. Achado antes de codar: os eventos de auditoria (criação + mudança de status) já eram gravados
em `audit_log` desde a Sprint P0.1, mas nenhum endpoint do sistema lia essa tabela de volta — adicionado
`GET /api/unidades-serializadas/<id>/historico` (só leitura, zero schema), aprovado explicitamente pelo
usuário antes de implementar por sair do escopo original ("só consumir API existente"). Cliente
atual/Garantia mostrados como placeholder explícito — dependem do módulo de Vendas, ainda não
implementado. 455 testes (34 no domínio de unidades serializadas), `ruff check .` limpo, validado
manualmente com produto/unidade/2 transições de status semeados via API.

**Sprint Comercial 1.3.3 — Filtros Avançados (CONCLUÍDA em 2026-07-22, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.3.md`):** busca combinada (IMEI/serial/modelo/marca/
localização), filtros por origem/status/faixa de saúde da bateria/localização, ordenação, e paginação
real — tudo resolvido no backend, nada só em memória no frontend (antes a tela carregava até 500
registros de uma vez e filtrava localmente). Três pontos do pedido original reportados ao usuário (CTO)
antes de codar por não terem suporte real: filtro por Cliente removido desta sprint (sem dado até
Vendas existir); status "Em Garantia"/"Inativo" não incluídos (não existem em lugar nenhum, seria regra
de negócio nova); filtros de bateria/localização construídos mesmo sem dado real hoje (mesmo padrão do
KI-020), decisão deliberada para não gerar retrabalho quando C1.3.4 escrever esses campos. 467 testes
(46 no domínio), `ruff check .` limpo, validado manualmente com dados de origem mista.

**Sprint Comercial 1.3.4 — Edição da Unidade Serializada (CONCLUÍDA em 2026-07-22, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.4.md`):** `PATCH /api/unidades-serializadas/<id>`
(localização, saúde da bateria — únicos campos de manutenção sem endpoint de escrita até então).
Pedido explícito do usuário (CTO) tratado como módulo de manutenção, não edição isolada — campos
derivados/imutáveis (origem, IMEI, status, campos de Vendas) bloqueados explicitamente com 400 se
enviados; status continua no endpoint próprio já existente (`/status`), com sua máquina de estados.
`DetalheUnidade` evoluído para um único componente de visualização+edição, por pedido explícito do
usuário de não duplicar estrutura entre um modal de detalhe e um de edição separados. Dois pontos
resolvidos antes de codar: "Observações" não existe no schema (fora de escopo, a própria instrução do
usuário de não alterar schema já resolve); IMEI consultado explicitamente e decidido como imutável
após o cadastro (identificador primário usado em busca/auditoria/futura garantia). 476 testes (55 no
domínio), `ruff check .` limpo, validado manualmente editando bateria/localização/status de uma
unidade real.

**Sprint Técnica — Centralização de Referências de OS (CONCLUÍDA em 2026-07-23, ver
`docs/operations/SPRINTS/SPRINT_TECNICA_CENTRALIZACAO_OS.md`):** segunda parte da centralização de
referências pedida pelo usuário (CTO), após a de Produtos (2026-07-22). Encontrado e corrigido: tipos de
OS (Assistencia/Garantia/Upgrade) tinham 2 cópias inline no backend e 3 no frontend, com `OrderFilters.jsx`
nunca buscando da API; prazo de garantia (90 dias) hardcoded 2x no mesmo arquivo backend;
`GARANTIA_DIAS` no frontend era código morto. Tudo centralizado em `OS_TIPOS_OPCOES`/
`GARANTIA_REPARO_DIAS_PADRAO` (`irflow_core.py`), exposto via `/api/constantes`, consumido por
`Orders.jsx`/`OrderFilters.jsx`. Achado registrado, não corrigido: perfis (`admin`/`tecnico`/
`vendedor`) espalhados como string literal em 11 arquivos backend sem lista central — categoria
diferente (autorização, não referência de UI), risco desproporcional a um chore, candidato a sprint
própria. 478 testes, `ruff check .` limpo, validado manualmente com os dropdowns de Status/Tipo em
`/ordens`.

**Sprint Comercial 1.3.5 — Rastreabilidade Individual de Itens de Estoque (CONCLUÍDA em 2026-07-27, ver
`docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.5.md`):** fecha o KI-020 — `POST`/`PUT /api/estoque`
passam a ler/gravar `requer_imei` (já existia no schema, sem caminho de escrita) e `GET /api/estoque`
passa a expô-lo; checkbox correspondente em `Stock.jsx`. Sem esse fechamento, o caminho "unidade
serializada com origem em Estoque" (`irflow_unidades_serializadas_service.py`) era inutilizável em
produção — só funcionava semeando o banco diretamente. Nome da coluna mantido por compatibilidade
(`requer_imei`); conceito documentado como rastreabilidade individual do item, não IMEI
especificamente. 8 novos testes (549 no total), incluindo o fluxo completo via API real (criar item
rastreável → criar unidade serializada com sucesso) e a confirmação de que a ausência da flag continua
rejeitando a criação (regressão). `ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos.

**Vendas MVP (CONCLUÍDA em 2026-07-27, ver `docs/operations/SPRINTS/SPRINT_COMERCIAL_VENDAS_MVP.md`):**
primeiro fluxo comercial completo — venda de um único aparelho (unidade serializada) a um cliente, com
pagamento simples registrado. Escopo deliberadamente independente das decisões de negócio ainda
pendentes do Product Owner em `VENDAS.md` (timeout de reserva, % comissão, limite de desconto, prazo de
garantia, critérios de avaliação de usado) — sem reserva com timeout (unidade vai direto
`disponivel` → `vendido`), sem desconto/comissão/garantia/troca. Modelado como `vendas` + `vendas_itens`
desde o início (mesmo com 1 item por venda nesta fatia), `status='concluida'` (não `'paga'` — venda e
pagamento são conceitos diferentes), snapshot `produto_nome`/`produto_sku` em `vendas_itens`, `UNIQUE`
em `vendas_itens.unidade_serializada_id` como proteção de banco contra a mesma unidade em duas vendas.
`irflow_unidades_serializadas_service.py` ganhou `marcar_como_vendida`, deliberadamente separada de
`transicionar_status`/`TRANSICOES_VALIDAS` para não abrir uma porta lateral no endpoint genérico de
status. Primeiro módulo a nascer com o prefixo `fluxoly_` (`fluxoly_vendas_controller.py`/`_service.py`/
`_repository.py`, ver `ADR-008`) — substitui o stub `irflow_vendas_service.py`, removido nesta sprint.
16 novos testes (565 no total), incluindo duas vendas concorrentes da mesma unidade via threads reais
(exatamente uma sucede, rodado 5x para confirmar ausência de flakiness) e prova de rollback atômico em
erro forçado. Refinado no mesmo dia: `valor_tabela` (snapshot de preço de catálogo, pré-preenchido e
editável) e `observacoes` em `vendas_itens`/`vendas`; frontend `frontend/src/pages/Vendas.jsx` (rota
`/vendas`) entregue e validado manualmente ponta a ponta (servidor real + banco isolado + navegador). 570
testes, `ruff check .` limpo. Próximo passo do roadmap comercial: fluxo completo de Vendas (desconto/
comissão/garantia/troca), condicionado a decisões do Product Owner.

**Sprint Infra 1.1 — CI Verde (CONCLUÍDA em 2026-07-27):** workflow `CI` corrigido e verde em `main` pela
primeira vez, `main` protegida contra merge sem os checks passando. Investigação completa, causas raiz e
justificativa de cada configuração em KI-026 (resolvida)/R-10/R-11 (mitigados)/TD-13 (endurecimento
adiado, backlog).

**Sprint Vendas 1.1 — Histórico + Detalhe de Vendas (CONCLUÍDA em 2026-07-27, branch
`feat/vendas-historico-detalhe`, mergeada em `main`):** retomada de uma branch aberta por uma sessão
anterior (commit WIP `6774016`) — backend (`GET /api/vendas` paginado/filtrável/ordenável, `GET
/api/vendas/<id>` enriquecido com nomes de cliente/vendedor e IMEI) e a página `VendaDetalhe.jsx` já
estavam prontos; pendências fechadas nesta sessão: abas "Nova Venda"/"Histórico" ligadas em `Vendas.jsx`
(componente `Historico()` já existia, sem estar no fluxo de navegação), botão "Ver venda" da tela de
sucesso passou a navegar para `/vendas/:id` em vez de buscar o detalhe inline, e `VendaDetalhe.jsx` teve
um erro real de lint corrigido (`react-hooks/set-state-in-effect` — `setLoading(true)` direto no corpo do
efeito; refeito com função nomeada `carregar()`, mesmo padrão já usado em `Historico()`) — achado que
motivou a investigação da Sprint Infra 1.1 acima. 10 novos testes (31 no domínio, 580 no repositório),
`ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos. Validado manualmente ponta a ponta
com servidor real + banco isolado (nunca `database.db`) e navegador Chrome real: criação de venda, clique
em "Ver venda" navegando corretamente para o detalhe, listagem/filtros/busca/paginação do histórico.

**V1.2 — Cancelamento (CONCLUÍDA em 2026-07-27):** discuss-phase completa antes de código (regras em
`VENDAS.md`/`BUSINESS_RULES.md` BR-031 a BR-036), depois implementação. `POST /api/vendas/<id>/cancelar`
— admin cancela qualquer venda, vendedor só as próprias, motivo obrigatório (lista fechada), terminal
(sem reativação). Índice único de `vendas_itens.unidade_serializada_id` trocado por um parcial
(`WHERE ativo=1`) — permite revenda da mesma unidade após cancelamento sem perder o histórico. 14 novos
testes (45 no domínio, 592 no repositório), `ruff check .`/`npm run lint`/`npm run build` limpos.
Validado ponta a ponta via API real (servidor + banco isolados): criar → cancelar → revenda da mesma
unidade → histórico com as duas vendas → segundo cancelamento rejeitado. Fluxo de clique no navegador não
repetido nesta sessão (limite de contexto) — mesmos componentes já validados manualmente na Sprint 1.1.

**Fechamento — validação de navegador da V1.2 (2026-07-28):** item pendente acima fechado. Servidor
Flask + Vite reais, banco isolado (`IR_FLOW_DATA_DIR`, nunca `database.db`), navegador Chrome real.
Fluxo completo executado: criar venda (unidade → `vendido`) → venda aparece no Histórico com badge
"Concluída" → abrir Detalhe pelo botão "Ver venda" e pela linha do Histórico → cancelar informando
motivo da lista fechada → toast de confirmação, badge "Cancelada", motivo e data exibidos, sem opção de
reativação → confirmado via API que a unidade voltou a `disponivel` e que `audit_log` registrou as duas
transições de status (`vendido→disponivel`, `disponivel→vendido`) → nova venda com o mesmo IMEI
concluída como Venda #2 → Histórico lista as duas vendas (`Concluída`/`Cancelada`) corretamente.
Nenhuma divergência encontrada — Sprint V1.2 encerrada sem achados.

**ADR-010 (CONCLUÍDA em 2026-07-28):** formaliza o ciclo Discovery → Plano Técnico → Implementação →
Testes → QA Manual → Encerramento, com gate explícito em cada etapa e o Princípio da Separação de
Decisões (Plano Técnico nunca decide regra de negócio — se surgir, volta para Discovery). Novo artefato
`docs/engineering/plans/PLAN-<slug>.md` (template em `docs/engineering/templates/PLAN_TEMPLATE.md`),
deliberadamente efêmero. Processo vive só na ADR — `CLAUDE.md` ganhou apenas uma referência de uma
linha, por ser processo do projeto, não de uma ferramenta de IA específica.

**V1.3 — Descontos e Aprovação (CONCLUÍDA em 2026-07-28, primeira feature a seguir o ciclo formal da
ADR-010):** discovery pela ótica do fluxo real de negociação da loja (BR-037 a BR-043,
`VENDAS.md`/`BUSINESS_RULES.md`), plano técnico revisado e aprovado (5 ajustes incorporados —
`docs/engineering/plans/PLAN-V1.3-Descontos.md`), depois implementação. `usuarios.limite_desconto_livre`
(R$, `NULL` = não configurado, tratado como R$0 pelo service — nunca por SQL); `POST /api/vendas` exige
`desconto_aprovado=true` explícito acima do limite (aprovação acontece fora do sistema, só a confirmação
e o timestamp são registrados, nunca quem aprovou). Ajuste Comercial Autorizado
(`PATCH /api/vendas/<id>/itens/<id>/ajuste-desconto`) — única exceção formal ao Princípio da Imutabilidade
da Venda (BR-034): só `admin`, motivo obrigatório, recálculo transacional, auditoria append-only,
compare-and-swap contra cancelamento concorrente. 21 novos testes (613 no total), `ruff check .`/
`npm run lint`/`npm run build` limpos. QA Manual (navegador real, servidor + banco isolados, 6 cenários:
desconto dentro/acima do limite, vendedor sem limite, Ajuste Comercial, segurança, estado obsoleto) —
todos passaram; encontrado e corrigido 1 bug real no processo (`limite_desconto_livre` ausente na
resposta de `POST /api/auth/login`, já que `Login.jsx` popula o `AuthContext` direto dessa resposta, sem
esperar `/api/auth/me`).

**V1.4 — Comissão (CONCLUÍDA em 2026-07-29, segunda feature a seguir o ciclo formal da ADR-010):**
discovery reabriu a V1.3 na mesma sessão e revogou o modelo de bloqueio preventivo de desconto
(BR-037/BR-038 → BR-053: todo desconto passa a ser sempre aceito e sempre registrado, sem exigir
aprovação nem respeitar limite; `limite_desconto_livre`/`desconto_aprovado_em` param de ser
lidos/gravados em qualquer fluxo, colunas mantidas no schema só por compatibilidade histórica, marcadas
como deprecadas). Plano técnico único cobrindo as duas partes
(`docs/engineering/plans/PLAN-V1.4-Comissao.md`, 5 ajustes incorporados), implementado em 8 commits
temáticos (reversão backend → reversão frontend → testes da reversão → schema/repository da comissão →
service/controller → frontend → testes da comissão → docs). Novo perfil `financeiro`; `comissao_valor`
(R$, `NULL` = não atribuída, sem campo de "tipo" fixo/percentual — BR-048) atribuída manualmente por
`admin`/`financeiro` via `PATCH /api/vendas/<id>/itens/<id>/comissao`; ocultação de `comissao_valor` para
qualquer outro perfil centralizada numa única função (`_ocultar_comissao_se_necessario`); zerada
automaticamente no cancelamento, sempre com evento de auditoria; histórico dedicado
(`GET .../historico-comissao`) restrito a `admin`/`financeiro` — diferente do histórico de desconto, que
é aberto. 15 novos testes de comissão + 6 reescritos da reversão (625 no total), `ruff check .`/
`npm run lint`/`npm run build` limpos. QA Manual via `curl` (14 cenários, autorização/ocultação/
zeragem/histórico/criação de usuário financeiro) — todos passaram; navegador real indisponível neste
ambiente por limitação do próprio ambiente de automação de navegador, não do produto (**KI-027**, novo).

**Fix de responsividade do Dashboard em MacBook (CONCLUÍDO em 2026-07-30, branch
`fix/dashboard-responsividade-macbook`, PR #14):** grids de KPIs e gráficos usavam contagem fixa de
colunas por breakpoint, pulando abruptamente entre 3 e 6 colunas e deixando espaço em branco/valores
truncados em larguras de MacBook (1366–1728px). Trocado por CSS Grid `auto-fit`/`minmax`
(`minmax(280px,1fr)` nos KPIs — calibrado para não truncar valores monetários; `minmax(420px,1fr)` nos
gráficos), único arquivo alterado (`Dashboard.jsx`). Validado por medição real de overflow no DOM
(`scrollWidth`/`clientWidth`) nas 6 larguras-alvo, não só cálculo de CSS — validação visual num MacBook
físico não foi possível nesta sessão (sem acesso a Mac). Mergeado em `main`.

**V1.5 — Garantia (CONCLUÍDA em 2026-07-30, terceira feature a seguir o ciclo formal da ADR-010, branch
`feat/vendas-v1-5-garantia`):** Garantia de Venda e Garantia de Reparo como processos independentes,
substituindo o prazo fixo de 90 dias hardcoded do reparo por um cadastro configurável de Tipos de
Garantia (BR-055 a BR-066). Ambas de atribuição manual obrigatória (venda/conclusão de OS) com snapshot
histórico congelado no momento da concessão — nunca recalculado ao vivo contra o cadastro, mesmo se este
mudar depois. Achado de implementação relevante: `salvar_reparos_os()` fazia `DELETE`+`INSERT` cego a
cada edição de OS, o que apagaria silenciosamente a garantia já concedida de uma linha mantida numa
edição sem relação com status — reescrita para sync não-destrutivo antes de expor o problema em
produção. 693 testes no total, `ruff check .`/`npm run lint`/`npm run build` limpos. QA Manual completo
com servidor real + banco isolado + navegador real via Claude in Chrome (login funcionou normalmente
nesta sessão, ao contrário do registrado em KI-027 — ver observação atualizada nesse KI) e `curl` para o
único fluxo sem UI (correção de Garantia de Reparo). Revisão Arquitetural (`ADR-010` etapa 6) sem
inconsistência não documentada. Achado durante o QA Manual, corrigido no mesmo Encerramento (decisão do
CTO): datas de garantia apareciam um dia atrasadas na tela por um bug clássico de parsing de data em JS
(`KI-028`, resolvido).

**Sprint CI/CD 1.1 — Hardening (CONCLUÍDA em 2026-07-31):** revisão do pipeline de CI/CD partiu de uma
premissa errada (que o pipeline ainda precisava ser criado) — descoberto que o CI já estava ativo e
bloqueante desde a Sprint Infra 1.1 (2026-07-27), com `main` protegida exigindo 5 status checks. Escopo
real, bem menor que uma sprint de implantação: (1) `fail_under` de cobertura elevado de 40% para 60%
(`pyproject.toml`, `ci.yml`) — cobertura real medida em 65.22%/682 testes no momento da mudança, ~5
pontos de margem antes de virar bloqueante de verdade; (2) novo job `Docker Build` (`docker build .`,
sem publicar) valida que a imagem builda antes do merge, não só na hora do deploy — testado localmente
via Colima antes de subir. `main` agora exige 6 status checks (Docker Build adicionado via `gh api`).
Deploy permanece manual, sem mudança — decisão deliberada de não automatizar nesta sprint.
`docs/engineering/QUALITY_GATES.md` atualizado (estava desatualizado desde 2026-07-06, antes até da
Sprint Infra 1.1 — vários gates listados como "Planejado"/"Manual" já estavam ativos há dias).

**Sprint Housekeeping — Rebranding Técnico (EM PLANEJAMENTO, iniciada 2026-07-31):** endereça TD-12
(nomenclatura legada `irflow_*`/`IR_FLOW_*`/`assistencia_system` convivendo com `fluxoly_*` desde
ADR-008). Decisão deliberada do usuário (CTO) de priorizar esta sprint agora, antes de retomar
funcionalidades de negócio, mesmo com TD-12 originalmente classificado como prioridade baixa — ver
`docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md` para a estrutura completa em 6 fases (Baseline →
Auditoria → Planejamento → Limpeza → Renomeação → Validação). Nenhuma fase executada ainda além da
Fase 0 (baseline confirmado: `main` sincronizada, tag `v1.2-cicd-hardening` existente, 682 testes).

**Sprint Housekeeping — CONCLUÍDA em 2026-08-03:** todos os módulos `.py` renomeados de `irflow_*` para
`fluxoly_*` (commits `8a085f8`..`14ec238`), branding residual do frontend corrigido, referências mortas
em `pyproject.toml` limpas. CI verde (run `30865336611`, todos os 6 jobs), cobertura 66.13% (acima do
baseline de 65.22%). Deploy validado em produção: Vercel via auto-deploy, Render via Manual Deploy
(auto-deploy não configurado nesse serviço — achado da própria validação de fechamento), ambos sem
erros novos no Sentry pós-deploy. `ADR-011` registra que a decomposição de `fluxoly_blueprints_api.py`
(TD-01) e o restante do épico de rebranding (variáveis `IR_FLOW_*`, infraestrutura, repositório) ficam
fora desta sprint, com dono e destino definidos. Ver retrospectiva completa em
`docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md`.

**TD-01 Phase 2 — Garantias extraído (2026-08-05):** segundo domínio extraído de
`fluxoly_blueprints_api.py` (o primeiro, Shopping List, já registrado na tabela de Dívida Técnica
acima). `api_garantias.py` criado (1 rota — `GET /garantias`, listagem agregada), mesmo padrão do
`api_shopping.py`: `Blueprint` próprio com `url_prefix="/api"`, `deps` parcial (`conectar`,
`garantia_reparo_dias_padrao`, `parse_data_ymd` — os dois últimos continuam também no dict de
`create_api_blueprint`, porque OS e Sistema, ainda não extraídos, dependem deles), helper específico
do domínio (`_classificar_garantia`) migrado junto, helpers genéricos (`err`/`ok`/`usuario_logado`)
reaproveitados de `fluxoly_api_helpers.py` (já criado na extração de Shopping). 682 testes passando
sem alteração, `ruff check .` limpo, `graphify update .` + `graphify explain "api_garantias"` +
`graphify affected "fluxoly_blueprints_api.py"` confirmados sem referência residual do domínio. Ver
`docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` (Phase 2, log de execução) e
`docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe completo.

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
>
> **Nota (2026-07-25):** a linha "Segurança" (5/10) acima também está desatualizada — foi calculada
> antes da Sprint Segurança 1.0, que fechou os P0/P1 de `docs/security/SECURITY_AUDIT_2026-07.md`
> (autorização de OS/Estoque, fallback de `FLASK_SECRET_KEY`, headers HTTP, Docker non-root,
> `persist-credentials`, dependências). A nota provavelmente já justifica um valor mais alto — mesma
> disciplina acima: recálculo formal fica para a próxima revisão do score completo, não decidido
> unilateralmente aqui.

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
| TD-01 | `fluxoly_blueprints_api.py` com ~130KB, 70 rotas, 13 domínios — módulo demasiado grande. Sprint própria iniciada em 2026-08-04 — Phase 0 (Discovery) e Phase 1 (Design) concluídas; Phase 2 (Extração Incremental) em andamento, 2 de 12 domínios extraídos (Shopping List, `api_shopping.py`, 2026-08-04; Garantias, `api_garantias.py`, 2026-08-05). Ver `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` e `docs/engineering/API_DEPENDENCY_MATRIX.md` | Alto    | Alta       |
| TD-02 | `app.py` acumula inicialização, DB e lógica misturadas                 | Alto    | Alta       |
| TD-03 | Ausência de migrations formais (usa `ALTER TABLE` com try/except)      | Alto    | Alta       |
| TD-04 | Sem injeção de dependências no backend — acoplamento direto ao SQLite  | Médio   | Média      |
| TD-05 | Testes de backend são scripts ad-hoc, não pytest com fixtures isoladas | Médio   | Alta       |
| TD-06 | Sem variáveis de ambiente documentadas (`.env.example` ausente)        | Médio   | Média      |
| TD-07 | Frontend sem testes unitários (apenas E2E Playwright)                  | Médio   | Média      |
| TD-08 | Commits com mensagens vagas ("att", "S", "att 09/06 5")               | Baixo   | Alta       |
| TD-09 | Sem paginação na listagem de OS — pode degradar com volume alto        | Médio   | Média      |
| TD-10 | Sem compressão de resposta HTTP no Flask                               | Baixo   | Baixa      |
| ~~TD-11~~ | ~~Bloco `criar_estoque()` duplicado e morto em `irflow_blueprints_api.py` (KI-014)~~ | ~~Baixo~~ | ~~Resolvido (2026-07-20, commit `c3294a3`)~~ |
| ~~TD-12~~ (código) | ~~Nomenclatura legada `irflow_*` em todos os módulos `.py` — resolvido pela Sprint Housekeeping~~ | ~~Baixo~~ | ~~Resolvido (2026-08-03, commits `8a085f8`..`14ec238`, ver `docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md`)~~ |
| TD-12 (infra) | Restante do Épico de Rebranding Técnico, deliberadamente fora da Sprint Housekeeping: variáveis `IR_FLOW_*` (14, alias `FLUXOLY_*` via `ADR-008`), URLs Render/Vercel, nome do repositório GitHub. Decomposição de `fluxoly_blueprints_api.py` (TD-01) também fora, formalizada em `ADR-011` | Baixo (cosmético, sem risco funcional) | Baixa — sem prazo; ligado a `RELEASE_1.0_MASTER_CHECKLIST.md` (janela de manutenção antes do lançamento comercial), não a esta sprint |
| TD-13 | **Infra 1.2 — Endurecer Governança do Repositório.** Proteção de `main` ativada em 2026-07-27 (R-10/R-11) cobre só o mínimo (5 status checks obrigatórios, `enforce_admins: false`). Falta: `enforce_admins: true` (a proteção hoje não vale para push direto do próprio mantenedor), `CODEOWNERS`, revisão obrigatória (`required_pull_request_reviews`) com aprovação mínima. Sugerido pelo usuário (CTO) — decisão deliberada de não fazer agora para não quebrar o fluxo atual de merge local + push direto de um mantenedor único; faz sentido quando a equipe crescer além de uma pessoa | Médio (hoje mitigado por disciplina manual de um único mantenedor; escala mal com mais colaboradores) | Baixa (sem prazo — condicionado a crescimento da equipe) |
| TD-14 | **Evolução do modelo de autorização — perfil único → perfis + permissões por módulo.** Discovery da V1.4 (2026-07-29) propôs substituir `usuarios.perfil` (enum: admin/tecnico/vendedor/estoque/financeiro) por acesso habilitado por módulo (checkboxes: Vendas/Estoque/Assistência/Financeiro/Compras/Dashboard/Administração), evitando explosão combinatória de perfis à medida que o sistema cresce. Decisão explícita: **não fazer agora** — muda arquitetura de autorização transversalmente (checagens espalhadas em ~80 endpoints de `irflow_blueprints_api.py` + `ROUTE_PERMISSIONS` + cada controller de domínio), exigiria migração dos perfis já em produção, e hoje 5 perfis (com `financeiro` da V1.4) ainda são administráveis — a "explosão" é cenário futuro, não problema atual. Merece ADR própria + discovery dedicada quando reaberto. **Preparação de baixo custo feita na V1.4:** checagens de autorização novas encapsuladas em helper reutilizável (ex.: `usuario_pode_financeiro()`), para que uma futura migração troque a implementação do helper sem precisar reescrever os call sites | Médio (não bloqueia nada hoje; custo de migração cresce quanto mais perfis/checagens ad-hoc se acumularem antes de endereçar) | Baixa (sem prazo — reavaliar se a combinação de perfis realmente começar a se multiplicar) |
| TD-15 | **Code Style Cleanup — Black/isort.** Setup de ambiente de desenvolvimento (2026-08-04) encontrou 55 arquivos `.py` fora do padrão do `black` (mesma versão travada do `.pre-commit-config.yaml`, 24.4.2 — não é drift de versão, é debt pré-existente) e 9 arquivos com imports fora de ordem pelo `isort` (`app.py`, `fluxoly_blueprints_api.py` entre eles). `ruff check .` está limpo — só formatação, não lint funcional. Decisão deliberada de não corrigir junto com o setup de ambiente (evitar commit não-atômico misturando dezenas de arquivos sem relação com a tarefa) | Baixo (cosmético, não afeta comportamento; `ruff check` limpo) | Média — resolver antes de a Sprint TD-01 (modularização da API) tocar nesses mesmos arquivos, para não misturar reformatação mecânica com a refatoração estrutural |
| TD-16 | **Formalizar `estoque_service.py`.** `ENGINEERING_GUIDE.md` §3 já recomenda extrair a lógica de movimentação de estoque hoje embutida em `fluxoly_os.py` (`registrar_movimentacao`, `consumir_peca_da_os`, `_consumir_lotes_fifo`, `devolver_pecas_da_os`) para um service formal, para que OS, Vendas e Compras consumam a mesma lógica em vez de cada um reimplementar. Identificado como ortogonal à Sprint TD-01 (Phase 1, 2026-08-04): a decomposição de `fluxoly_blueprints_api.py` não depende disso — as funções já vivem fora do blueprint. Registrado aqui para não repetir o padrão já visto em `ADR-002` original (recomendação feita, nunca rastreada como item de backlog) | Médio (hoje funciona, mas cada novo consumidor de baixa de estoque arrisca reimplementar a lógica à sua maneira) | Baixa — sem prazo; considerar quando Vendas ou Compras precisarem dar baixa em estoque de fato |

---

## Riscos Atuais

| ID   | Risco                                                                 | Probabilidade | Impacto | Mitigação atual      |
|------|-----------------------------------------------------------------------|---------------|---------|----------------------|
| R-01 | SQLite em produção sem replicação — falha de disco = perda de dados  | Baixa         | Crítico | Backup automático    |
| ~~R-02~~ | ~~Sem CI/CD — regressões chegam a produção sem detecção automática~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-27, Sprint Infra 1.1; reforçado 2026-07-31, Sprint CI/CD 1.1 — Hardening)** — mesmo mecanismo de R-10/R-11: CI ativo e bloqueante (6 status checks), cobertura em 60% |
| R-03 | Chaves secretas em variáveis de ambiente sem documentação formal      | Média         | Alto    | `.env` removido do git|
| ~~R-04~~ | ~~Sem rate limiting — `/api/auth/login` vulnerável a força bruta~~ | Baixa | Alto | **Mitigado (2026-07-11)** — `irflow_rate_limit.py`, 5 tentativas/min por identificador (KI-001) |
| R-05 | Tokens de checklist não expiram — link público permanente             | Baixa         | Médio   | Nenhuma              |
| R-06 | Dependência única de Render + Vercel sem estratégia de fallback documentada | Baixa   | Médio   | `DEPLOY.md` documenta o passo a passo, sem provedor alternativo |
| R-07 | Módulo de integração MercadoPhone sem testes — qualquer mudança é risco| Alta         | Médio   | Script diagnose_mercadophone.py |
| ~~R-08~~ | ~~`ruff check .` vermelho em `main` — job `Lint` bloqueava `backend`/`frontend` via `needs: lint` (KI-017)~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-20)** — `ruff check .` → 0 erros, branch `chore/fix-ruff-lint-ki-017`, 6 commits atômicos |
| R-09 | Produção real (Render + Vercel) está atrás de `main` — confirmado em 2026-07-22 consultando `GET /api/constantes` da produção real: ainda retorna só até "iPhone 16e" (sem a linha 17, sem `produtos`, sem `unidades_serializadas`) | Alta | Alto (percepção de bug onde não há — usuário reportou "hotfix não aplicado" quando na verdade é deploy pendente) | Nenhuma automática — deploy é acionado manualmente no dashboard Render/Vercel, decisão já registrada do CTO de acumular mudanças para um RC completo antes do próximo deploy |
| ~~R-10~~ | ~~Workflow `CI` não registrava nenhum sucesso em `main` (84/84 runs falhos confirmados via `total_count` da API, 2026-07-07–2026-07-27) — job `Frontend Quality` (ESLint) vermelho por 3 causas diferentes ao longo do tempo, `Frontend Build` nunca rodava (KI-026)~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-27, Sprint Infra 1.1)** — 4 erros de ESLint corrigidos (`chore/frontend-eslint-cleanup`), primeiro sucesso do workflow identificado nas execuções verificadas |
| ~~R-11~~ | ~~`main` não tinha proteção de branch configurada no GitHub — confirmado via `gh api repos/.../branches/main/protection` retornando `404 Branch not protected` (sem revisão obrigatória, sem status check obrigatório, sem bloqueio de force-push). O CI (R-10) nunca funcionou como gate de merge~~ | ~~Alta~~ | ~~Alto~~ | **Mitigado (2026-07-27)** — proteção ativada via `gh api` exigindo os 5 status checks do CI, `strict: true`, força-push/deleção bloqueados. `enforce_admins: false` deliberado (preserva o fluxo atual de push direto do único mantenedor) — endurecimento completo (CODEOWNERS, revisão obrigatória, `enforce_admins: true`) registrado como TD-13, não decidido |

---

## Arquivos Críticos

| Arquivo                          | Papel                                                         | Risco de tocar |
|----------------------------------|---------------------------------------------------------------|----------------|
| `fluxoly_blueprints_api.py`      | Todos os endpoints REST (70) — núcleo do sistema (TD-01)       | Muito alto     |
| `app.py`                         | Inicialização Flask, schema DB, registro de blueprints        | Muito alto     |
| `fluxoly_os.py`                  | Lógica de negócio das Ordens de Serviço                       | Alto           |
| `fluxoly_storage.py`             | Backup automático e Google Drive                              | Alto           |
| `fluxoly_mercadophone.py`        | Integração com sistema externo MercadoPhone                   | Alto           |
| `frontend/src/api/client.js`     | Centraliza todas as chamadas de API do frontend               | Alto           |
| `frontend/src/App.jsx`           | Roteamento, guards de autenticação, layout global             | Alto           |
| `frontend/src/contexts/AuthContext.jsx` | Estado global de autenticação                          | Alto           |
| `fluxoly_core.py`                | Constantes de status e utilitários compartilhados             | Médio          |
| `frontend/src/pages/NewOrder.jsx`| Fluxo crítico de criação de OS com auto-price                 | Médio          |
| `frontend/src/pages/EditOrder.jsx`| Fluxo crítico de edição de OS                                | Médio          |

---

## Cobertura de Testes

| Camada            | Tipo                     | Ferramenta   | Cobertura medida em `main` (`pytest-cov`, 2026-07-20, pós Sprint Comercial 0.1) — branch `feat/unidades-serializadas` (ainda não mergeada) entre parênteses |
|-------------------|--------------------------|--------------|--------------------|
| Backend — API     | Smoke tests ad-hoc       | Python scripts| ~25% das rotas (não medido via `pytest-cov`) |
| Backend — Módulos | pytest (auth, sessão, usuários, permissões, segurança, estoque, OS, parsing/validação, preços, shopping list, rate limit, sessão/inatividade, auditoria, reset de senha, clientes, unidades_serializadas, produtos — Sprint 2.2 a Sprint Comercial 0.1, migração ADR-007) | pytest | `irflow_validation.py` 100% · `irflow_clientes_repository.py` 100% · `irflow_clientes_service.py` 97% · `irflow_clientes_controller.py` 97% · `irflow_produtos_service.py` 99% · `irflow_produtos_controller.py` 91% · `irflow_produtos_repository.py` 85% · `irflow_core.py` 86% · `irflow_price_tables.py` 83% · `app.py` 55% (58% na branch) · `irflow_os.py` 64% · `irflow_blueprints_api.py` 59% (60% na branch) — `irflow_estoque_unidades_service.py` 97%/`irflow_estoque_unidades_controller.py` 95% em `main`, renomeados para `irflow_unidades_serializadas_service.py` 99%/`_controller.py` 95%/`_repository.py` 86% na branch |
| Frontend — Pages  | Sem testes unitários     | —            | 0%                 |
| Frontend — E2E    | Fluxos principais        | Playwright   | ~20% dos fluxos    |
| Integração        | Script manual            | Python       | ~10%               |
| **Global (repo, `main`)** |                  |              | **50%** (`pytest --cov`, 434 testes, pós Sprint Comercial 0.1 — 2026-07-20); **50,3%** (447 testes) na branch `feat/unidades-serializadas`, ainda não mergeada |

> Meta Sprint 2: >= 40% de cobertura nas rotas críticas do backend. **Atingida** em 2026-07-11 com `test_pricing.py` e `test_shopping.py` (Sprint 2.7) — cobertura global subiu de 36% para 43%, e segue subindo com Sprint 3/P0.1 (46% agora). Gate de CI bloqueante desde a Sprint 2.7 (`fail_under = 40`). `test_os.py` (nome originalmente previsto) foi substituído por 3 módulos mais granulares na Sprint 2.4 (`test_os_creation_query.py`, `test_os_update_status.py`, `test_os_deletion_security.py`).

---

## Próximos Objetivos

### Curto prazo (Sprint 2)
1. ~~Implementar pipeline de CI com GitHub Actions~~ — já existe, ver "Estado Atual"
2. Migrar smoke tests para pytest com fixtures
3. ~~Atingir 40% de cobertura nas rotas críticas~~ — feito em 2026-07-11 (43%, `test_pricing.py`, `test_shopping.py`)
4. Documentar `.env.example`
5. Padronizar commits com Conventional Commits
6. ~~Corrigir os erros de `ruff check .` em `main` (KI-017/R-08)~~ — feito em 2026-07-20 (0 erros, branch `chore/fix-ruff-lint-ki-017`), antes do início do Épico Vendas
7. **[Backlog — process]** Adicionar critério **C-05 — Consulta incorreta em fluxo oficial** a `docs/engineering/ENGINEERING_GUIDE.md` §11 (ou ADR dedicada). Motivação: o hotfix `44be10c` (Sprint 2.5 — ordem de parâmetros SQL quebrava todo filtro de `GET /api/estoque`) não se encaixava nos critérios C-01–C-04 existentes, que cobrem mutação de dado, não leitura incorreta em rota de consulta usada pelo frontend. Rascunho de critério: *"O achado faz uma rota de consulta (GET) oficialmente usada pelo frontend retornar dado incorreto, incompleto ou vazio de forma sistemática (não um erro pontual de um registro), sem sinalizar erro ao chamador?"* Avaliar junto de C-01–C-04 na próxima ocorrência similar antes de formalizar a redação final.

### Médio prazo (Sprint 3–4)
1. Quebrar `fluxoly_blueprints_api.py` em módulos menores (TD-01 — decisão confirmada em `ADR-002`/`ADR-011`, sprint própria ainda sem data)
2. Implementar migrations formais (Alembic ou scripts versionados)
3. Adicionar rate limiting em `/api/auth/login`
4. Implementar expiração de tokens de checklist
5. Adicionar paginação na listagem de OS

### Longo prazo (Sprint 5+)
1. Avaliar migração de SQLite para PostgreSQL
2. Implementar observabilidade (Sentry ou similar)
3. Criar API pública documentada (OpenAPI/Swagger)
4. Adicionar notificações push/webhook para mudanças de status de OS
