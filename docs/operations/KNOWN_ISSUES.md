# Known Issues

## ~~KI-001~~ — RESOLVIDO

Descrição:
Ausência de rate limiting na rota `POST /api/auth/login`. Qualquer agente podia realizar tentativas de
login ilimitadas sem bloqueio por IP ou por usuário.

Impacto:
Alto. O endpoint estava vulnerável a ataques de força bruta contra credenciais de usuários do sistema.

Status:
Resolvido em 2026-07-11 (Sprint 3, Unidade 1). Contador de tentativas em SQLite (tabela
`login_attempts`, `irflow_rate_limit.py`) — 5 tentativas/minuto por identificador, aplicado em
`POST /api/auth/login` (rota real usada pelo frontend) e `POST /login` (rota legada). Contador em SQLite
em vez de memória do processo porque o Gunicorn de produção roda com `--workers 2`
(`Dockerfile`) — memória de processo daria um limite efetivo mais fraco e contornável entre workers;
SQLite já é compartilhado entre eles via WAL. Identificador resolvido via `Fly-Client-IP` (header do
proxy da Fly.io) com fallback para `X-Forwarded-For`/`remote_addr` — nenhum desses headers era lido
antes. Coberto por `tests/test_rate_limit_login.py` (7 casos). Isolamento de teste garantido por fixture
autouse em `tests/conftest.py` (`_limpar_login_attempts`), já que o cliente de teste do Flask sempre usa
o mesmo IP.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade. Resolvido em 2026-07-11.

Responsável:
—

---

## KI-002

Descrição:
Tokens de checklist público (`GET /api/checklist/<token>`) não possuem data de expiração. Uma vez gerado, o link permanece válido indefinidamente.

Impacto:
Médio. Links compartilhados com clientes para revisão do dispositivo continuam acessíveis após o encerramento da OS, expondo informações da ordem sem controle de tempo.

Status:
Aberto.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade.

Responsável:
—

---

## ~~KI-003~~ — RESOLVIDO

Descrição:
O módulo `fluxoly_blueprints_api.py` (renomeado de `irflow_blueprints_api.py` na Sprint Housekeeping,
2026-08-03) possui ~130KB e concentra 70 rotas em 13 domínios de negócio sem separação — contagem exata
e mapeamento de acoplamento (78 dependências injetadas via `create_api_blueprint(deps)`) levantados em
`ADR-011`.

Impacto:
Alto. Dificulta manutenção, aumenta risco de regressão em qualquer alteração e torna o onboarding de novos colaboradores mais lento.

Status:
Resolvido em 2026-08-07 (TD-01 Phase 2, Extração Incremental, encerrada formalmente por decisão do
usuário — CTO). 12/12 domínios extraídos para blueprints próprios (`api_shopping.py`,
`api_garantias.py`, `api_costs.py`, `api_prices.py`, `api_users.py`, `api_auth.py`, `api_backup.py`,
`api_reports.py`, `api_mercadophone.py`, `api_system.py`, `api_stock.py`, `api_os.py`).
`fluxoly_blueprints_api.py` reduzido de ~130KB/3.368 linhas/70 rotas para 911 bytes/34 linhas/0 rotas —
só resta código morto sem consumidor (`_slug_estoque`/`_gerar_sku_estoque`, ver KI-032). Architecture
Checkpoint Final em `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md`. Remoção do arquivo e do
registro `create_api_blueprint({})` em `app.py` registrada como TD-18 (Phase 3 — Cleanup),
deliberadamente fora do escopo desta sprint.

Sprint prevista:
TD-01 — concluída (Phase 2) em 2026-08-07.

Responsável:
—

---

## ~~KI-004~~ — RESOLVIDO

Descrição:
O sistema de migrations do banco de dados utiliza `ALTER TABLE` com blocos `try/except` ad-hoc em `app.py`. Não há versionamento formal do schema.

Impacto:
Alto. Impossível determinar o estado exato do schema em diferentes ambientes (dev, prod) sem inspecionar o banco diretamente. Risco de divergência silenciosa.

Status:
Resolvido em 2026-08-08 (TD-03, 2/2 fatias). `app.py::criar_tabelas()` (695 linhas ad-hoc) substituída por
`migrations/` — registry Python de migrations com tabela de controle `schema_migrations`. Fatia 1
(`migrations/registry.py`/`runner.py`/`versions/m0001_baseline.py`, aditiva, `app.py` intocado) validada
contra um backup real de produção antes da Fatia 2 — schema/contagens de linhas idênticos entre o
mecanismo antigo e o novo, idempotência confirmada. Fatia 2 removeu `criar_tabelas()`/`SCHEMA_READY`/
`SCHEMA_LOCK` de `app.py`; `conectar()` virou conexão pura, schema garantido só pelo bootstrap
(`run_migrations()`). Ver `docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md`.

Sprint prevista:
Sprint 4 — Decomposição do Módulo API e Migrations Formais (planejamento original, nunca executado).
Resolvido via TD-03 em 2026-08-08.

Responsável:
—

---

## KI-005

Descrição:
A listagem de Ordens de Serviço (`GET /api/ordens`) não possui paginação. Retorna todos os registros em uma única resposta.

Impacto:
Médio. Com volume crescente de OS, a rota degradará em performance e o frontend consumirá memória excessiva ao renderizar listas muito grandes.

Status:
Aberto — aguardando Sprint 5.

Sprint prevista:
Sprint 5 — Paginação, Performance e Refatoração Frontend.

Responsável:
—

---

## KI-006

Descrição:
Falhas no envio de backup por e-mail não geram alertas visíveis para o operador. O sistema registra o erro internamente, mas nenhuma notificação chega ao usuário da interface.

Impacto:
Baixo. O operador pode ficar sem backup por dias sem perceber, aumentando o risco de perda de dados em caso de falha de disco.

Status:
Aberto — parcialmente endereçado. Sprint Observabilidade (2026-07-25) migrou os `print()` da thread de
backup (`irflow_storage.py`) para `logger.warning`/`logger.error` estruturado, e a integração Sentry
(gated por `SENTRY_DSN`, ainda vazia — usuário não tem conta) captura automaticamente qualquer
`logger.error(..., exc_info=True)` quando ativada. Isso dá visibilidade ao operador técnico via Sentry
depois de configurada — mas continua sem nenhuma notificação visível na interface para o usuário da
loja, que é o gap original descrito acima. Não fechar este KI só por causa da mudança de logging.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade (concluída parcialmente nesse ponto por
`docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md`, 2026-07-25).

Responsável:
—

---

## KI-007

Descrição:
Mensagens de commit sem padrão ("att", "S", "att 09/06 5"). O histórico git não comunica intenção ou escopo das mudanças.

Impacto:
Baixo. Rastreabilidade de bugs e análise de regressão ficam prejudicadas. Impossível usar `git bisect` ou `git log` para investigar quando um comportamento foi introduzido.

Status:
Aberto — mitigação via adoção de Conventional Commits a partir da Sprint 2.

Sprint prevista:
Sprint 2 — Pipeline de CI e Testes Backend.

Responsável:
—

---

## ~~KI-008~~ — RESOLVIDO

Descrição:
Auto-preenchimento de `valor_cobrado` ausente em NewOrder e EditOrder.

Impacto:
Crítico. Usuário precisava consultar a tabela de preços manualmente e preencher o campo a cada OS criada.

Status:
Resolvido na Sprint 1. Commit `fix: auto-preencher valor_cobrado pela tabela de preços`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-009~~ — RESOLVIDO

Descrição:
URL do endpoint de PDF do relatório IR Phones estava incorreta (`/irphones` ao invés de `/ir-phones`).

Impacto:
Alto. Exportação de PDF do relatório IR Phones falhava com 404.

Status:
Resolvido na Sprint 1. Correção em `frontend/src/api/client.js`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-010~~ — RESOLVIDO

Descrição:
Rota de histórico de cliente apontava para endpoint inexistente no `client.js`.

Impacto:
Médio. Consulta de histórico do cliente na tela de OS retornava erro 404.

Status:
Resolvido na Sprint 1. Correção em `frontend/src/api/client.js`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-011~~ — RESOLVIDO

Descrição:
Campo `cor` não era limpo ao trocar o modelo em `EditOrder.jsx`, podendo manter uma cor inválida para o novo modelo selecionado.

Impacto:
Médio. Dados inconsistentes entre modelo e cor em OS editadas.

Status:
Resolvido na Sprint 1. Correção em `frontend/src/pages/EditOrder.jsx`.

Sprint prevista:
Sprint 1 — concluída.

Responsável:
—

---

## ~~KI-012~~ — RESOLVIDO

Descrição:
`irflow_blueprints_api.py` continha duas funções `shopping_list()` (e as respectivas `shopping_create`,
`shopping_update`, `shopping_delete`) registradas na mesma rota `/shopping-list` — a versão atual
(tabela `shopping_list`, com paginação/prioridade/responsável) e um bloco legado de uma implementação
anterior baseada na tabela `compras`, aparentemente deixado para trás na `Merge branch
'feature/shopping-edit-os-pr'` (commit `7811846`). Como Flask não permite dois endpoints com o mesmo
nome de função no mesmo blueprint, `app.py` lançava `AssertionError` na inicialização — a aplicação
não conseguia nem ser importada.

Impacto:
Crítico. Bloqueava toda execução da aplicação e da suíte de testes (inclusive os testes de
autenticação da Sprint 2.2). Identificado ao tentar rodar `pytest` pela primeira vez nesta sprint.

Status:
Resolvido em 2026-07-07. Removido o bloco legado duplicado (baseado em `compras`) em
`irflow_blueprints_api.py`. Confirmado via `frontend/src/pages/ShoppingList.jsx` e
`frontend/src/api/client.js` que o frontend consome apenas a implementação baseada em `shopping_list`
(campo `items`, não `compras`) — nenhuma funcionalidade em uso foi removida.

Sprint prevista:
Identificado e corrigido fora de sprint — bloqueava a Sprint 2.2.

Responsável:
—

---

## ~~KI-013~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, nove pontos de parsing de entrada (`int()`/`float()` sobre
`request.args`/corpo JSON) em `shopping_list`, `reposicao_sugerida_estoque`, `criar_ordem`,
`atualizar_ordem`, `criar_estoque`, `atualizar_estoque`, `criar_custo`, `atualizar_custo` e
`salvar_preco` não tinham tratamento de exceção — ocorriam antes de qualquer `try/except` da
rota. Um valor não numérico (ex.: `?page=abc`, `{"valor": "abc"}`) derrubava a rota com 500 não
tratado, fora do contrato JSON `{"ok": false, "erro": ...}` usado pelo resto da API.

Impacto:
Médio. Não expõe dados nem quebra integridade do banco, mas qualquer cliente (inclusive o
frontend, em caso de bug de digitação/formulário) que envie um valor não numérico nesses campos
recebe um erro de servidor genérico em vez de uma mensagem de validação utilizável.

Status:
Resolvido em 2026-07-07 (Sprint 2.6). Substituído por `parse_int`/`parse_float`
(`irflow_validation.py`), que retornam `None` para entrada presente porém inválida — o call site
rejeita explicitamente com `err(...)` e 400, em vez de mascarar como o valor default ou deixar a
exceção propagar. Coberto por `tests/test_api_parsing.py`.

Sprint prevista:
Identificado e corrigido na Sprint 2.6 — Padronização de Validação e Parsing.

Responsável:
—

---

## ~~KI-014~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, existe uma definição de `def criar_estoque():` sem decorador
`@api.route` nas linhas 220-267 (função interna solta, incluindo uma linha órfã
`return bool(session.get("usuario_id"))` que pertence a `usuario_logado()`). Ela é
imediatamente sobrescrita pela definição real e roteada de `criar_estoque()` mais abaixo
(`@api.route("/estoque", methods=["POST"])`), tornando o primeiro bloco código morto — nunca é
chamado, `ruff check .` já acusa `F811 Redefinition of unused 'criar_estoque'`. Mesmo padrão de
origem do KI-012 (bloco deixado para trás em um merge), mas sem o efeito colateral de derrubar
`app.py` na inicialização, pois não há decorador duplicado.

Impacto:
Baixo. Sem efeito em runtime — apenas ruído de manutenção (48 linhas mortas, pode confundir
leitura futura do arquivo).

Status:
Resolvido em 2026-07-20, commit `c3294a3` (branch `chore/fix-ruff-lint-ki-017`). Bloco morto
removido por completo, incluindo a linha órfã. Achado no processo de corrigir KI-017 (o `F811`
era um dos 175 erros de `ruff check .`). Rota real de `criar_estoque()` e comportamento da API
não mudam — confirmado por `pytest tests/` (407 testes) sem regressão. Fecha também TD-11
(`docs/operations/PROJECT_STATUS.md`).

Sprint prevista:
Identificado durante a Sprint 2.6 (2026-07-07); resolvido em 2026-07-20 junto de KI-017.

Responsável:
—

---

## ~~KI-015~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, `PATCH /api/ordens/<id>/status` e `PUT /api/ordens/<id>` chamavam
`normalizar_status_os(body.get("status") or "")` sem o parâmetro `status_padrao=""`. Como a função
tem `status_padrao=STATUS_EM_ANDAMENTO` por default, um `status` ausente ou inválido nunca retornava
vazio — a checagem `if not status: return err(...)` nunca disparava. Consequência em
`PATCH .../status`: um status desconhecido era silenciosamente normalizado para "Em andamento" em
vez de rejeitado com 400. Consequência mais grave em `PUT /api/ordens/<id>`: editar qualquer campo
de uma OS **Finalizada** sem reenviar `status` reabria a OS silenciosamente para "Em andamento" e
zerava `data_finalizado` — sem erro, sem aviso.

Impacto:
Crítico em `PUT /api/ordens/<id>` — perda silenciosa do dado de finalização de uma OS em rota
usada pelo frontend em produção (C-01 + C-04, `docs/engineering/ENGINEERING_GUIDE.md` §11). Médio em
`PATCH .../status` — grava estado incorreto sem erro, mesma rota real.

Status:
Resolvido em 2026-07-10 via `hotfix/status-os-padrao-vazio`. Ambos os call sites passam a usar
`normalizar_status_os(body.get("status") or "", status_padrao="")`. As correções já existiam prontas
(commits `c85a321`, `e755f25`, achados durante a Sprint 2.4 em 2026-07-07, com aprovação explícita do
usuário) mas nunca chegaram a `main` porque a branch `test/sprint-2-4-regras-negocio-os` que as
continha não havia sido mergeada — extraídas via `cherry-pick` para hotfix isolado ao retomar o
Sprint 2, conforme ADR-004. Suíte completa (180 testes) e `ruff check` confirmados sem regressão
antes do merge.

Sprint prevista:
Identificado durante a Sprint 2.4 (2026-07-07); hotfix efetivamente mergeado em 2026-07-10, ao
retomar o Sprint 2 após a frente de documentação de produto/marca.

Responsável:
—

---

## ~~KI-016~~ — RESOLVIDO

Descrição:
Em `irflow_blueprints_api.py`, `POST /api/shopping-list` calculava a quantidade solicitada com
`parse_int(body.get("quantidade_solicitada") or body.get("quantidade"), default=1)`. Como `0` é
falsy em Python, enviar `quantidade_solicitada: 0` fazia o `or` cair para
`body.get("quantidade")` (ausente), que por sua vez caía no `default=1` do `parse_int` — antes
mesmo de chegar na validação `if quantidade is None or quantidade <= 0: return err(...)`, que
nunca era alcançada com o valor real enviado pelo chamador.

Impacto:
Médio. `POST /api/shopping-list` (rota real usada por `Compras.jsx`) criava o item silenciosamente
com quantidade `1` em vez de rejeitar a entrada `0` — mutação silenciosa de dado persistido sem
erro (C-01 + C-04, `docs/engineering/ENGINEERING_GUIDE.md` §11).

Status:
Resolvido em 2026-07-11 via `hotfix/quantidade-zero-shopping-list`. Trocado o `or` por
`body.get("quantidade_solicitada", body.get("quantidade"))` — `dict.get` com fallback só usa o
segundo valor quando a chave está de fato ausente, preservando `0` explícito para a validação
existente rejeitar. Achado durante a escrita de `tests/test_shopping.py` (restante da Sprint 2).
Suíte completa (331 testes) confirmada sem regressão antes do merge.

Sprint prevista:
Identificado e corrigido fora de sprint — bloqueava o fechamento da Sprint 2 (política de
interrupção do `CLAUDE.md`).

Responsável:
—

---

## ~~KI-017~~ — RESOLVIDO

Descrição:
`ruff check .` falhava em `main` com 20 erros (`F841` variáveis não usadas em
`irflow_blueprints_api.py` linhas 28-70, `SIM105`/`SIM102` em vários pontos, `E401` imports
múltiplos em uma linha, e o `F811` já conhecido de KI-014). O job `Lint` do CI
(`.github/workflows/ci.yml`) marca o passo `ruff check .` como BLOQUEANTE, e os jobs `backend` e
`frontend` dependem de `Lint` via `needs: lint` — ou seja, nenhum desses jobs roda enquanto o lint
estiver vermelho.

Impacto:
Alto (operacional, não funcional). Nenhum dos 20 erros é bug de comportamento — não foram gerados
por nenhuma mudança desta sessão (confirmado: nenhum está nas linhas tocadas pelo hotfix
KI-016/`quantidade-zero-shopping-list`). O risco real é que o CI pode estar vermelho em `main` há
algum tempo sem que `PROJECT_STATUS.md` refletisse isso — merece verificação do histórico real de
execuções no GitHub Actions antes de assumir desde quando.

Status:
Aberto — identificado em 2026-07-11 ao rodar `ruff check .` localmente antes de mergear o hotfix
KI-016. Fora de escopo corrigir aqui (seria refatoração de ~20 pontos em vários arquivos, viola a
regra de mudança única do `CLAUDE.md`). Candidato a uma sprint de limpeza isolada (`chore:` ou
`refactor:`, nunca junto de uma feature/fix).

**Correção de escopo (2026-07-11, Sprint 3 Unidade 1):** a contagem de "20 erros" acima media só
`irflow_blueprints_api.py`. Rodando `ruff check app.py irflow_blueprints_api.py` juntos (os dois
arquivos críticos que a Sprint 3 está tocando) o total real é **60 erros** — `app.py` sozinho
contribui um bloco grande de `F401` (imports não usados) nunca contado antes. Confirmado via
`git stash` que os 60 já existiam em `main` antes de qualquer mudança desta sessão — nenhuma unidade
da Sprint 3/P0.1 piora esse número, cada uma é checada com `ruff check <arquivos tocados>` antes do
commit para garantir isso.

**Exceção documentada (2026-07-11, Sprint P0.1 Unidade 5):** o total subiu para **61** com a adição de
`os.cliente_id` — um novo bloco `try: ALTER TABLE ... / except sqlite3.OperationalError: pass`, que
segue exatamente o idioma já documentado em `DATABASE.md`/`ENGINEERING_GUIDE.md` para migração aditiva
de coluna (repetido ~15 vezes em `app.py`, cada instância já contava para os 60 originais via `SIM105`).
Escrever esse bloco de outra forma (`contextlib.suppress`, sugestão do `ruff`) deixaria essa única
instância inconsistente com todas as outras ao redor — optado por manter consistência com o padrão
estabelecido do arquivo em vez de silenciar o lint em um ponto isolado. Confirmado: subiu para **62**
na Unidade 6 (`estoque.requer_imei`), mesma justificativa.

**Correção de escopo definitiva (2026-07-11, Sprint 3 Unidade 8):** todas as contagens acima (20 → 60 →
61 → 62) mediam apenas `app.py` + `irflow_blueprints_api.py`. `.github/workflows/ci.yml` roda
`ruff check .` — **o repositório inteiro**, não só esses dois arquivos. Rodando o comando real do CI:
**175 erros**, incluindo módulos nunca antes contados (`irflow_blueprints_orders.py`,
`irflow_mercadophone.py`, `irflow_os.py`, `irflow_price_tables.py`, `irflow_reports.py`,
`irflow_storage.py`, `irflow_reference_data.py`, `irflow_blueprints_admin.py`) e, principalmente, uma
dezena de scripts soltos na raiz do repo (`diagnose_dashboard_filter.py`, `test_sync.py`,
`validate_changes.py`, `test_dashboard_filter.py`, `test_solution.py`, `test_update_os.py`,
`test_shopping_list.py`, `test_routes.py`, `debug_shopping.py`, `smoke_test_full.py`,
`check_old_orders.py`) — scripts de debug/smoke pré-pytest (`docs/operations/SPRINTS/SPRINT_02.md` os
cita como "7 scripts ad-hoc no banco real"), fora de `tests/` e por isso nunca rodados pelo pytest, mas
ainda escaneados pelo `ruff check .` do CI. Nenhum dos 9 arquivos novos desta sprint
(`irflow_rate_limit.py`, `irflow_audit.py`, `irflow_clientes_*.py`, `irflow_estoque_unidades_*.py`,
`irflow_vendas_service.py`) aparece nessa lista — confirmado zero regressão. **62 continua sendo o
número relevante para o que a Sprint 3/P0.1 tocou**, mas **175 é o número real que bloqueia o CI**.

**Resolvido em 2026-07-20 (branch `chore/fix-ruff-lint-ki-017`, 6 commits atômicos), decisão do
usuário (CTO) de destravar o CI antes de iniciar o Épico Vendas — todo PR futuro dependeria de um
pipeline que já nascia bloqueado.** Categorização dos 175 erros reais:

- **95 (54%)** viviam em 11 scripts de debug/smoke pré-pytest soltos na raiz do repo (já citados
  acima como causa do salto de 62→175) — nenhum coletado pelo pytest (`testpaths=["tests"]`),
  nenhum invocado pelo `ci.yml`. Movidos para `scripts/` (já excluído do ruff em `pyproject.toml`,
  mesmo lugar de `diagnose_mercadophone.py`/`import_legacy_db.py`) — zero mudança de conteúdo,
  commit `94cfdb2`.
- **24** resolvidos por `ruff check --fix` (imports não usados, espaço em branco, f-strings sem
  placeholder, etc.) nos módulos de produção — commit `2cd3822`.
- **28** (`SIM105`) convertidos para `contextlib.suppress` — 18 no idioma de `ALTER TABLE` de
  `app.py` (já documentado acima como intencional; convertidas todas juntas nesta mudança, o que
  preserva a consistência interna do arquivo em vez de quebrá-la) e 10 no idioma de limpeza
  best-effort de `irflow_blueprints_api.py` — commit `f00a993`.
- **1** (`F811`) era o bloco morto de `criar_estoque()` — resolvido junto de KI-014, commit
  `c3294a3`.
- **10** (`F841`) eram bindings `deps[...]` nunca referenciados — commit `ba0edd3`.
- **17** restantes (`B904`, `B007`, `E741`, `C414`, `SIM102/103/110/115/118`) corrigidos
  pontualmente, cada um reescrito 1:1 do mesmo comportamento — commit `605b5f5`. Uma exceção
  documentada: `SIM115` em `irflow_blueprints_api.py` (restauração de backup) foi suprimida com
  `# noqa` em vez de convertida para `with`, porque fechar o handle do `NamedTemporaryFile` antes
  do `os.unlink()` manual no `finally` falharia com `PermissionError` no Windows enquanto o
  arquivo ainda está em uso por `sqlite3.connect()`/`shutil.copy2()`.

`ruff check .` → 0 erros (era exatamente o comando que o job `Lint` do CI roda). 407 testes,
100% passando, cobertura 48% (gate ≥ 40%) — confirmado após cada um dos 6 commits, não só no
final. R-08 (`docs/operations/PROJECT_STATUS.md`) mitigado junto — `backend`/`frontend` voltam a
rodar via `needs: lint` para qualquer PR novo, inclusive os do Épico Vendas.

**Correção de registro (2026-07-21):** o commit local/branch existia desde 2026-07-20, mas o merge
efetivo em `origin/main` só aconteceu em 2026-07-21, junto do merge de `feat/produtos-catalogo`
(Sprint Comercial 1.1) — a branch de lint era pré-requisito dela e nunca havia sido mesclada em
`origin/main` isoladamente. Achado ao mesclar a Tela Produtos; `ruff check .` confirmado em 0 erros
no repositório inteiro após o merge, 434 testes (407 + 27 de `test_produtos.py`) passando.

Sprint prevista:
Não definida — recomendado priorizar antes da Sprint 3, já que um lint vermelho bloqueia todo o
resto do pipeline de CI para qualquer PR. Commit criado em 2026-07-20, mergeado em `origin/main`
em 2026-07-21.

Responsável:
—

---

## ~~KI-018~~ — RESOLVIDO

Descrição:
`IPHONE_MODELS`/`IPHONE_COLORS` (`irflow_reference_data.py`) — fonte única do catálogo de modelos
usado em `GET /api/constantes` e consumido por `NewOrder.jsx`/`EditOrder.jsx`/`Stock.jsx`/
`PriceTables.jsx` — parava em "iPhone 16e", sem os modelos da linha iPhone 17 (lançamento 2025:
iPhone 17, iPhone 17 Air, iPhone 17 Pro, iPhone 17 Pro Max).

Impacto:
Alto (operacional). Impedia abrir Ordem de Serviço para qualquer aparelho da linha iPhone 17 — o
modelo simplesmente não aparecia no dropdown de seleção, já que o backend não valida `modelo` contra
uma whitelist (a lista só alimenta as opções do frontend).

Status:
Resolvido em 2026-07-21 via `fix/catalogo-iphone-17` (Hotfix H-002), branch a partir de `main`.
Adicionados os 4 modelos a `IPHONE_MODELS`. Cores em `IPHONE_COLORS` usam uma lista genérica
(`Preto`/`Branco`/`Azul`/`Verde`/`Rosa`, mesmo padrão de outras gerações) em vez de nomes específicos
do catálogo oficial Apple — decisão deliberada do usuário (CTO) em revisão: sem necessidade comercial
ainda de precisão de cor por variante, o risco de publicar um nome de cor incorreto supera o
benefício; trocar pelos nomes oficiais quando/se houver essa demanda (ex.: Vendas/Produtos). Regex de
extração de modelo por descrição livre (`extrair_modelo_da_descricao_aparelho`) ajustado para
reconhecer o sufixo "air", nunca usado antes nesta lista — sem o ajuste, uma descrição como "iPhone
17 Air 256GB" seria extraída incorretamente como "iPhone 17", perdendo a distinção do modelo.
Comentário adicionado acima de `IPHONE_MODELS` documentando que é fonte única consumida por Nova
OS/Editar OS/Estoque/Tabela de Preços/`API /api/constantes`, para reduzir o risco de o catálogo ficar
desatualizado de novo sem que o próximo desenvolvedor perceba o alcance da lista. Nenhuma mudança de
schema/endpoint/regra de negócio. Confirmado que `IPHONE_MODELS`/`IPHONE_COLORS` é fonte única, sem
lista duplicada em nenhum outro módulo, antes de editar. Suíte completa (407 testes) sem regressão.
Validado manualmente: criação real de OS com modelo "iPhone 17 Pro Max" via API e via tela
`NewOrder.jsx` (servidor local, banco isolado).

Sprint prevista:
Fora de sprint — pedido direto do usuário (CTO), prioridade por bloqueio operacional imediato.

Responsável:
—

---

## KI-019

Descrição:
No modo "processo único" (Flask servindo o build do React — `serve_react`/`serve_react_assets`,
`app.py`), os `<script>`/`<link>` gerados pelo Vite em `frontend/dist/index.html` usam caminho
absoluto `/assets/...` (`base: '/'` em `vite.config.js`), mas a rota Flask que serve esses arquivos é
`/app/assets/<filename>` (prefixo `/app`). Toda requisição de asset (`.js`/`.css`) retorna 404, e a
SPA nunca monta — tela em branco.

Impacto:
Alto no modo processo único especificamente (torna essa forma de deploy inutilizável), mas **zero
impacto na produção real hoje** — produção roda backend (Render) e frontend (Vercel) como serviços
separados, onde a Vercel serve `frontend/dist` na sua própria raiz e o caminho absoluto `/assets/...`
funciona sem problema. Só afeta quem tentar rodar `app.py` localmente/como deploy alternativo servindo
o build React embutido.

Status:
Aberto — identificado em 2026-07-21 durante o smoke test de RC da migração `unidades_serializadas`
(`docs/engineering/migrations/MIGRATION_unidades_serializadas.md`), ao tentar validar visualmente
contra `http://.../app` local. Contornado para o smoke test usando `npm run dev` (proxy do Vite para
a API) em vez do modo processo único — não bloqueou a validação da migração. Não corrigido nesta
sessão por estar fora do escopo da migração (regra de mudança única do `CLAUDE.md`); corrigir exigiria
decidir entre alinhar `vite.config.js` (`base: '/app/'`) ou a rota Flask (`/assets/<filename>` sem
prefixo) — decisão de arquitetura pequena, mas real, não tomada unilateralmente aqui.

Sprint prevista:
Não definida — sem urgência, já que o modo afetado não é o usado em produção.

Responsável:
—

---

## ~~KI-020~~ — RESOLVIDO

Descrição:
`POST /api/estoque` (`criar_estoque`) e `PUT /api/estoque/<id>` (`atualizar_estoque`), em
`irflow_blueprints_api.py`, nunca liam `body.get("requer_imei")` — a coluna `estoque.requer_imei`
(existe desde a Sprint 3 Unidade 6, `DEFAULT 0`) não fazia parte do `INSERT`/`UPDATE` de nenhuma das
duas rotas. Por comparação, o domínio `produtos` tem o campo equivalente (`requer_rastreio_unidade`)
totalmente cabeado em `irflow_produtos_controller.py`/`_service.py`/`_repository.py` — a assimetria era
só do lado Estoque. O nome da coluna é histórico (IMEI); o conceito é rastreabilidade individual do
item (IMEI hoje, outros identificadores de série no futuro).

Impacto:
Médio/Alto (funcional, não de segurança). Não existia **nenhum caminho via API/UI** para marcar um
item de `estoque` como `requer_imei=1` — todo item criado nascia com o default `0` e nunca podia mudar.
Na prática, isso tornava o caminho "unidade serializada com origem em Estoque" (`irflow_
unidades_serializadas_service.py::criar_unidade`, parâmetro `estoque_id`) inutilizável em produção —
só o caminho com origem em `produtos` funcionava de ponta a ponta. Achado ao semear dados de teste
reais para a Sprint Comercial C1.3.1 (Tela Unidades Serializadas): setar `requer_imei` exigia escrever
direto no banco, contornando a API por completo.

Status:
Resolvido em 2026-07-27 (Sprint Comercial C1.3.5 — Rastreabilidade Individual de Itens de Estoque,
branch `feat/estoque-requer-imei`). `listar_estoque()`/`criar_estoque()`/`atualizar_estoque()` passam a
ler/gravar/expor `requer_imei`, mesmo padrão já usado em `produtos.requer_rastreio_unidade`.
`frontend/src/pages/Stock.jsx` ganhou o checkbox correspondente. 8 novos testes, incluindo o fluxo
completo via API (criar item rastreável → criar unidade serializada com sucesso) e a confirmação de que
um item sem a flag continua rejeitado (regressão). Ver `docs/operations/SPRINTS/SPRINT_COMERCIAL_1.3.5.md`.

Sprint prevista:
Sprint Comercial C1.3.5 — concluída em 2026-07-27.

Responsável:
—

---

## ~~KI-021~~ — RESOLVIDO

Descrição:
`getOrderDisplayNumber` (`frontend/src/lib/constants.js`) sempre exibia o `id` interno da OS (`#866`),
mesmo para Ordens de Serviço importadas do MercadoPhone — que deveriam mostrar o número real da
integração (`os.id_externo_integracao`) para permitir localizar a OS pelo número que o cliente/
MercadoPhone usa, sincronizar atualizações e evitar duplicidade ao importar.

Impacto:
Alto (operacional). Usado em produção real — dificultava conferência cruzada entre o sistema e o
MercadoPhone para toda OS de origem `mercado_phone`. `os.origem_integracao`/`os.id_externo_integracao`
já existiam no schema e já eram retornados por `GET /api/ordens` (`_os_row_to_dict`); o dado nunca
esteve ausente, só não era usado pela função de exibição.

Status:
Resolvido em 2026-07-22 via `hotfix/os-numero-mercadophone` (Hotfix H-003, pedido do usuário — CTO).
Regressão identificada no commit `fda0929` (2026-06-09, co-autoria "Copilot", mensagem "fix shopping
list mismatch"): a versão original de `getOrderDisplayNumber` já preferia `id_externo_integracao`
quando `origem_integracao === "mercado_phone"`, com fallback para `String(order.id).slice(-5)` — o
truncamento (`.slice(-5)`) era o bug real por trás daquele commit, mas a correção da época removeu a
preferência pelo número externo inteira, não só o truncamento. Restaurada a preferência pelo número
externo, sem reintroduzir o truncamento. Nenhuma mudança de schema/backend — os dados já existiam e já
eram retornados pela API; só a exibição no frontend estava errada. Validado manualmente: OS nativa
exibe `#1` (id interno), OS com `origem_integracao='mercado_phone'` exibe `#MP-90210` (número externo
semeado via API/banco isolado para o teste).

Sprint prevista:
Fora de sprint — pedido direto do usuário (CTO), prioridade por bloqueio operacional imediato
(Hotfix H-003, junto do achado de deploy pendente descrito no Problema 1 do mesmo pedido).

Responsável:
—

---

## ~~KI-025~~ — RESOLVIDO

Descrição:
As rotas legadas de escrita baseadas em formulário HTML (`irflow_blueprints_orders.py`,
`irflow_blueprints_inventory.py`, `irflow_blueprints_admin.py`, e as views de gestão de usuário em
`irflow_blueprints_auth.py`/`POST /usuarios/novo|editar|deletar`) faziam mutações reais no banco
(criar/editar/excluir OS, estoque, custos, reparos, tabelas de preço, usuários) protegidas só por
cookie de sessão — sem nenhum token CSRF. Em produção, `SESSION_COOKIE_SAMESITE = "None"` (`app.py`,
necessário porque frontend/backend são origens diferentes — Vercel/Render) faz o cookie ser enviado em
requisições cross-site. `flask-wtf` nunca esteve instalado, não havia `CSRFProtect` em lugar nenhum, e
`tests/conftest.py` chegou a ter uma config `WTF_CSRF_ENABLED = False` sem efeito nenhum (evidência de
que alguém assumiu uma proteção que nunca existiu). Achado durante a Fase 1 (API endpoints/banco) de uma
auditoria de segurança pedida pelo usuário (CTO).

Impacto:
Crítico. Uma página maliciosa com um `<form>` auto-submit para `POST /usuarios/novo` (`perfil=admin`),
visitada por um admin autenticado, criava uma conta admin controlada pelo atacante — tomada de conta
completa. Mesma classe de ataque contra `/deletar/<id>` (OS), `/estoque/deletar/<id>`,
`/custos-operacionais`, `/backup` (criar backup/disparar e-mail), etc.

Status:
Resolvido em 2026-07-26. Removidas por completo as rotas de escrita vulneráveis, em vez de adicionar
Flask-WTF para proteger uma superfície já confirmada sem uso real: `irflow_blueprints_orders.py`,
`irflow_blueprints_inventory.py` e `irflow_blueprints_admin.py` deletados por inteiro;
`irflow_blueprints_auth.py` perdeu as views de gestão de usuário (mantidos só `login`/`logout`);
`irflow_blueprints_main.py::backup()` perdeu a lógica de escrita (POST), virando GET-only. Confirmado
antes de remover: o frontend React usa exclusivamente os equivalentes JSON em `/api/*`
(`frontend/src/api/client.js`, grep sem nenhuma chamada às rotas removidas); não existe pasta
`templates/` no repositório (os `render_template()` no fim dessas views eram código morto
inalcançável); todo redirecionamento GET dessas rotas continua idêntico via
`LEGACY_REACT_REDIRECTS`/`destino_react_legado()`, que roda no `before_request` antes da resolução de
rota e não depende da view function existir. `POST /api/backup/criar` já existe e já é o que o
frontend usa. Testes das rotas removidas (`test_auth.py::TestControleDeAcessoPorPerfil`,
`test_permissions.py::TestPermissoesEditarUsuarioLegado`/`TestPermissoesDeletarUsuarioLegado`,
`test_session_inactivity.py::TestInatividadeSessaoViewLegada`) removidos — cobertura equivalente já
existe em `test_users.py` (`/api/usuarios`) e `TestInatividadeSessaoApi`. 514 testes passando (queda em
relação à contagem anterior é esperada — testes de funcionalidade removida, não regressão),
`ruff check .` limpo.

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/csrf-rotas-legadas-escrita`.

Responsável:
—

---

## ~~KI-022~~ — RESOLVIDO

Descrição:
`POST /api/integracoes/mercadophone/{sincronizar,reprocessar,reimportar}` (`irflow_blueprints_api.py`)
só checavam `usuario_logado()` — qualquer perfil autenticado, inclusive `vendedor`, podia disparar essas
operações. O mais grave era `/reimportar` → `reimportar_todas_os_mercado_phone()`
(`irflow_mercadophone.py:1220-1255`): apaga **todas** as OS com `origem_integracao='mercado_phone'` (mais
`os_reparos`/`integracao_os_vistas` relacionados) e reimporta do zero — mesmo efeito de um
`DELETE /api/ordens` em massa, mas por um caminho de código que ficou fora da restrição já aplicada a
`/api/ordens*` em 2026-07-25 (`docs/security/SECURITY_AUDIT_2026-07.md` item 14). `/sincronizar` e
`/reprocessar` sobrescrevem campos de OS existentes a partir da API externa — mesma categoria, sem
deletar. Achado durante auditoria de segurança pedida pelo usuário (CTO), Fase 1 (integração
MercadoPhone).

Impacto:
Alto. Qualquer perfil autenticado (inclusive `vendedor`, que segundo os documentos de produto não
deveria ter acesso administrativo a Estoque/OS) podia apagar e reimportar em massa as OS de origem
MercadoPhone, ou sobrescrever campos existentes a partir da API externa, sem nenhuma confirmação de
perfil.

Status:
Resolvido em 2026-07-26. Adicionada a mesma checagem já usada em `criar_ordem`/`atualizar_ordem`/
`deletar_ordem` (`session.get("usuario_perfil") not in ("admin", "tecnico")` → 403) aos 3 endpoints de
mutação. Endpoints de status (GET, só leitura) e `salvar_config_mercadophone` (já exigia `admin`) não
alterados. Módulo não tinha nenhum teste de autorização antes (R-07) — 4 novos testes em
`tests/test_mercadophone_permissions.py` (sem sessão, `vendedor`, `tecnico`, `admin` × 3 endpoints).
529 testes no total, `ruff check .` limpo.

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/mercadophone-mutacao-em-massa-permissao`.

Responsável:
—

---

## ~~KI-023~~ — RESOLVIDO

Descrição:
`app.py`, `autenticar_integracao_mercado_phone()` (autenticação do webhook `POST
/api/integracoes/mercadophone/os`): quando `MERCADO_PHONE_WEBHOOK_TOKEN` não está configurada, a função
tinha um early-return que pulava toda a validação — o endpoint ficava aberto sem autenticação alguma.
`.env.example`/`DEPLOY.md` chegavam a documentar esse comportamento como aceitável em dev local. Achado
durante a Fase 1 (Auth/Middleware) de uma auditoria de segurança pedida pelo usuário (CTO).

Impacto:
Alto (potencial). Se a variável estivesse vazia em produção, qualquer requisição não autenticada poderia
injetar Ordens de Serviço falsas na tabela `os` real via webhook público. Confirmado com o usuário (CTO)
que a variável está configurada com valor forte em produção hoje — não houve exploração ativa.

Status:
Resolvido em 2026-07-26. Removido o early-return: sem token configurado, nenhum candidato corresponde e a
rota rejeita com 401 por padrão (fail secure). Comparação do token trocada de `in`/`==` para
`hmac.compare_digest` (constant-time), fechando também um timing side-channel teórico (CWE-208)
encontrado na mesma função. `.env.example`/`DEPLOY.md` atualizados para marcar a variável como
obrigatória. 3 testes novos (`tests/test_mercadophone_webhook_auth.py`).

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/mercadophone-webhook-fail-secure`.

Responsável:
—

---

## ~~KI-024~~ — RESOLVIDO

Descrição:
`app.py`, `verificar_autenticacao()`: `ROUTE_PERMISSIONS.get(endpoint)` retorna `None` tanto para uma
entrada explícita `None` no dict (qualquer perfil logado) quanto para uma chave ausente — um endpoint
legado novo adicionado sem entrada correspondente em `ROUTE_PERMISSIONS` ficava liberado por padrão para
qualquer usuário autenticado, em vez de negado. Achado durante a mesma auditoria de segurança do KI-023.
Confirmadas 6 entradas já mortas no dict (`sync_os_mercado_phone`, `status_sync_mercado_phone`,
`order_views.autocomplete_clientes`/`api_buscar_pecas`/`api_remover_peca`/`api_adicionar_peca`) apontando
para funções que não existem mais em nenhum blueprint — prova de que o dict já divergia do código real.

Impacto:
Médio (arquitetural, não exploit ativo). Verificado manualmente que todos os endpoints hoje registrados em
`main_views`/`order_views`/`inventory_views`/`admin_views`/`auth_views` estão cobertos no dict — nenhum
endpoint real está sendo liberado indevidamente hoje. O risco era o padrão de falha silenciosa no futuro.

Status:
Resolvido em 2026-07-26. Adicionado um sentinel em `verificar_autenticacao()` para distinguir os dois
casos — endpoint ausente do dict agora é negado por padrão (fail secure). As 6 entradas mortas
permanecem no dict sem efeito (limpeza fica para um `chore:` separado, não misturado com a correção de
segurança). 3 testes novos (`tests/test_route_permissions_fail_secure.py`).

Sprint prevista:
Fora de sprint — achado durante auditoria de segurança pedida pelo usuário (CTO), corrigido via branch
`fix/mercadophone-webhook-fail-secure`.

Responsável:
—

---

## ~~KI-026~~ — RESOLVIDO (causa 3); mitigado (governança, ver TD-13)

Descrição:
O workflow `CI` (`.github/workflows/ci.yml`) não registrava nenhum sucesso em `main` até esta revisão —
confirmado via `gh api repos/.../actions/workflows/ci.yml/runs?branch=main` (campo `total_count`
autoritativo da API, não a listagem client-side de `gh run list`, que trunca por paginação): **84 de 84
execuções em `main` terminaram em falha** (`status=failure`, `status=success` retorna `total_count: 0`),
do primeiro run (2026-07-07) até o mais recente antes desta revisão (2026-07-27). Considerando todas as
branches do repositório (não só `main`), o total sobe para 105 runs, também 0 sucessos — número usado
por engano como "105/105 em `main`" numa versão anterior desta entrada, corrigido nesta revisão. A causa
raiz mudou ao longo do tempo, sempre no mesmo job (`Frontend Quality`, que roda `npm ci` + `npm run
lint`):

1. **2026-07-07 a ~2026-07-20:** `ruff check .` vermelho (KI-017, já documentado e resolvido — mas o
   job `Frontend Quality`/ESLint nunca foi mencionado nessa investigação, então ninguém percebeu que ele
   também estava vermelho o tempo todo).
2. **~2026-07-23 a ~2026-07-26:** o próprio `npm ci` falhava antes de chegar a rodar o ESLint —
   `frontend/package-lock.json` fora de sincronia com `frontend/package.json` (`npm error Missing:
   @emnapi/core@1.9.2`, `@emnapi/runtime@1.9.2`, `@emnapi/wasi-threads@1.2.1` — dependências opcionais
   nativas do motor Oxide do Tailwind CSS v4, `@tailwindcss/vite`/`tailwindcss` em `package.json`).
   `npm ci` é estrito e falha nessa divergência; rodar `npm install` localmente (que atualiza o
   lockfile silenciosamente) mascarava o problema sem ninguém perceber.
3. **~2026-07-26 até esta revisão (2026-07-27):** `npm ci` passa, mas `npm run lint` falha de verdade —
   4 erros pré-existentes, não relacionados a nenhuma sprint recente: `Compras.jsx:20`
   (`react-hooks/set-state-in-effect`), `Compras.jsx:28`, `ShoppingModal.jsx:46`,
   `ServicesChartCard.jsx:38`, `TechnicianProfitChartCard.jsx:48` (`no-unused-vars`). Mais 2 warnings
   não bloqueantes (`react-hooks/exhaustive-deps` em `ShoppingList.jsx`/`Stock.jsx`).

Achado ao investigar o CI da branch `feat/vendas-historico-detalhe` (Sprint Vendas 1.1): o commit WIP
dessa branch falhava no `Frontend Quality` por um erro próprio (corrigido nesta sprint, ver
`PROJECT_STATUS.md`), o que levou a verificar se `main` também estava afetado — estava, e por um motivo
diferente e mais antigo, não introduzido por essa branch.

Impacto:
Alto (processo, não funcional em produção — nenhuma das três causas envolve regra de negócio ou dado). O
job `Frontend Build` depende de `Frontend Quality` (`needs: frontend`) e nunca chega a rodar enquanto ela
falhar — ou seja, **o build do frontend não é verificado pelo CI há pelo menos 20 dias**, apesar de
`PROJECT_STATUS.md` descrever o CI como saudável (`ruff check .` → 0 erros é verdade, mas cobre só o job
`Lint`/Ruff — backend). `Backend Tests`/`Coverage`/`Lint` (Ruff) não são afetados e continuam passando
normalmente em cada run — só o gate de qualidade do frontend está sistematicamente quebrado.

Status:
**Causa 3 (ESLint) resolvida em 2026-07-27, Sprint Infra 1.1** — branch `chore/frontend-eslint-cleanup`
a partir de `main` (regra de mudança única do `CLAUDE.md` preservada: só os 4 arquivos com erro, nenhuma
mudança de comportamento), mergeada em `main`. Primeiro sucesso do workflow `CI` identificado nas
execuções verificadas (`total_count` da API, run `30313428268`, commit `a86cc62`). Causas 1 (Ruff) e 2
(`npm ci`) já eram história — nenhuma das três reproduz mais.

**Achado relacionado, mais grave (2026-07-27, mesma investigação):** o motivo de 84/84 falhas nunca terem
travado um merge é que `main` **não tinha nenhuma proteção de branch configurada** — confirmado via
`gh api repos/.../branches/main/protection` retornando `404 Branch not protected` (não "sem status check
obrigatório": não existia objeto de proteção nenhum — sem revisão obrigatória, sem status check
obrigatório, sem bloqueio de force-push a nível de GitHub). O CI existia e rodava, mas nunca funcionou
como gate — qualquer PR/push podia mergear em `main` independente do resultado. **Mitigado em
2026-07-27**, mesma sessão, imediatamente após confirmar `main` verde: proteção ativada via `gh api`
exigindo os 5 status checks (`Lint`, `Backend Tests`, `Frontend Quality`, `Frontend Build`, `Coverage
Report`), `strict: true`, bloqueio de force-push/deleção. `enforce_admins` deixado em `false`
deliberadamente — não quebra o fluxo atual de merge local + push direto do usuário (CTO, único mantenedor
hoje); ver TD-13 para o endurecimento completo quando a equipe crescer. Ver R-10/R-11 em
`PROJECT_STATUS.md`.

Sprint prevista:
Sprint Infra 1.1 — concluída em 2026-07-27.

Responsável:
—

---

## ~~KI-027~~ — RESOLVIDO (causa raiz reclassificada)

Descrição:
Ambiente de automação de navegador (Chrome via ferramenta de automação) não persiste o cookie de sessão
`HttpOnly` gerado por `POST /api/auth/login`: o login retorna `200 ok:true`, mas a próxima requisição
same-origin na mesma aba (`GET /api/auth/me` ou qualquer rota autenticada) recebe `401`. Testado com
múltiplas abas/tab groups novas, cliques reais na UI e `fetch` direto via JS no console da página —
sempre o mesmo resultado. O mesmo fluxo de login, contra o mesmo backend, funciona instantaneamente via
`curl` (tanto direto na porta do Flask quanto através do proxy do Vite), e um cookie não-`HttpOnly` de
teste (`document.cookie`) persiste normalmente na mesma aba — descarta bloqueio geral de cookies do
perfil. Não há ferramenta disponível para inspecionar o cookie `HttpOnly` armazenado pelo Chrome nessa
automação (JS não pode lê-lo, por design do navegador), então não foi possível confirmar se o cookie é
rejeitado no armazenamento ou apenas não reenviado.

Impacto:
Médio, só para o processo de trabalho — impede QA Manual via navegador real dentro deste ambiente de
automação para qualquer feature que dependa de sessão autenticada. Nenhum impacto em produção nem no
código da aplicação (o mesmo fluxo funciona normalmente em `curl`, e a suíte automatizada cobre a lógica
de sessão via `flask.testing` client, que não depende deste mecanismo de cookie do navegador).

Status:
**Causa raiz real encontrada em 2026-07-30**, durante QA manual da UX-001 (Preservação de Contexto da
Navegação) — não é característica do ambiente de automação, como suposto em 2026-07-29. `app.py` liga
`IS_SERVER_RUNTIME=True` sempre que `IR_FLOW_DATA_DIR` está definido (linha ~187) — a mesma variável usada
para isolar qualquer sessão de QA local do `database.db` real. Com `IS_SERVER_RUNTIME=True`, o cookie de
sessão sai com `Secure; SameSite=None; Partitioned` (confirmado via `curl -i` contra `http://127.0.0.1:5080`
rodando com `IR_FLOW_DATA_DIR` setado: `Set-Cookie: session=...; Secure; HttpOnly; Path=/; SameSite=None;
Partitioned`). O atributo `Secure` exige HTTPS — um navegador real (Chrome via Claude in Chrome, ou
qualquer outro) descarta silenciosamente esse cookie numa conexão `http://localhost` pura, exatamente o
sintoma original (login `200`, toda requisição seguinte `401`). `curl` com `-b`/`-c` (cookie jar) é mais
permissivo que um navegador real quanto ao atributo `Secure` sobre `http://`, o que explica por que o
mesmo fluxo "funcionava instantaneamente via curl" — não é um cookie geral bloqueado, é especificamente a
combinação `Secure` + `http://`.

**Confirmado resolvido**: rodando o backend com um override local de `app.config["SESSION_COOKIE_SECURE"] =
False` / `SESSION_COOKIE_SAMESITE = "Lax"` / `SESSION_COOKIE_PARTITIONED = False` (só no processo da sessão
de QA, nenhuma mudança em `app.py`), o cookie passou a persistir normalmente no Chrome real via Claude in
Chrome — login, navegação autenticada, scroll/filtro/destaque da UX-001 validados ponta a ponta sem
nenhum 401. Zero impacto em produção (lá é HTTPS real via Render/Vercel, `Secure` é o comportamento
correto) — o problema só existe ao rodar `IR_FLOW_DATA_DIR` + servidor real + navegador real + `http://`
simultaneamente, combinação que só acontece em QA manual local, nunca em produção nem na suíte automatizada
(`flask.testing` não depende do mecanismo de cookie do navegador).

**Não corrigido em código** — nenhuma mudança em `app.py` feita a partir deste achado; ver "Próximos
passos" abaixo para a decisão pendente sobre se vale introduzir uma flag de override para facilitar QA
manual local futura.

Sprint prevista:
Não definida.

Responsável:
—

Próximos passos (não decidido, registrado para referência futura):
Considerar uma variável de ambiente dedicada (ex.: `IR_FLOW_FORCE_INSECURE_COOKIE=1`) para permitir QA
manual local com `IR_FLOW_DATA_DIR` + navegador real sem precisar de um script wrapper ad-hoc como o usado
nesta sessão — decisão de arquitetura pequena, não tomada unilateralmente aqui.

**Observação (2026-07-30, QA Manual da V1.5 — Garantia):** login e navegação autenticada via Claude in
Chrome funcionaram normalmente nesta sessão com `IR_FLOW_DATA_DIR` setado (`IS_SERVER_RUNTIME=True`,
cookie `Secure; SameSite=None; Partitioned`), sem nenhum wrapper/override de `SESSION_COOKIE_SECURE` —
mesma combinação que reproduzia o 401 na sessão da UX-001. Hipótese não confirmada: `localhost`/`127.0.0.1`
são tratados por Chrome como origens "potencialmente confiáveis" havia algumas versões, o que satisfaria o
atributo `Secure` mesmo sem HTTPS — se essa for a causa, o sintoma pode depender da versão do Chrome usada
pela ferramenta de automação em cada sessão, não ser 100% determinístico. Não investigado a fundo (fora do
escopo da sessão de V1.5); registrado só para não assumir que o wrapper de `SESSION_COOKIE_SECURE` é
sempre necessário daqui pra frente.

---

## KI-029

Descrição:
Dois arquivos de backup de banco de dados estão versionados no git e presentes em `main` até hoje:
`backup-20260429-015724.db` (commit `8b69767`, 2026-04-28) e
`database-pre-cleanup-20260517-123834.db` (commit `252815a`, 2026-05-17). Ambos parecem conter dados
operacionais reais — o primeiro tem 74 linhas em `os` e 2 em `usuarios`; nesse snapshot a tabela
`clientes` ainda não existia, então nomes de cliente ficavam em campo de texto livre dentro de `os`.
Achado incidentalmente durante `AUDIT_LEGACY.md` (Sprint Housekeeping, Fase 1), ao buscar por
`assistencia-system` como parte da varredura de nomenclatura legada.

**Atualização (2026-07-31, `AUDIT_REPOSITORY.md`):** mesmo padrão encontrado em mais dois arquivos,
ainda presentes em `main`: `database.db-shm` (32KB — índice de memória compartilhada do modo WAL do
SQLite, pode conter fragmentos de dados de transações recentes) e `database.db-wal` (0 bytes no momento
da auditoria, mas já foi commitado com conteúdo em algum ponto do histórico — commits `4fef090`
2026-06-09 e `f20521f` 2026-05-05). `database.db` em si já está no `.gitignore`, mas o padrão exato não
cobre os sidecars `-shm`/`-wal` do modo WAL, então eles vazaram pela mesma lacuna.

Impacto:
Alto em potencial (dado operacional/possivelmente PII no histórico do git, acessível a qualquer clone
do repositório), mas sem exploração confirmada — não é uma vulnerabilidade explorável remotamente, é
exposição de dado em um artefato versionado. Contraria diretamente os princípios "O banco é sagrado" e
"sempre manter testes isolados" do `CLAUDE.md`. As regras de `.gitignore` adicionadas depois
(`database.db`, `backups/`) não cobrem esses nomes de arquivo específicos (nem os dois backups, nem os
sidecars `-shm`/`-wal`) e não afetam arquivos já commitados de qualquer forma.

Status:
Aberto — identificado em 2026-07-31. **Nenhuma ação foi tomada** (nem remoção do working tree, nem
reescrita de histórico) — decisão explícita necessária do usuário antes de qualquer mudança, dado que
remover do working tree (`git rm`) não apaga do histórico, e reescrever histórico (`git filter-repo`/BFG
+ force-push) é uma operação destrutiva que exige aprovação explícita à parte, fora do fluxo normal da
Sprint Housekeeping.

Sprint prevista:
Não definida — decisão pendente sobre remover do working tree vs. reescrever histórico vs. avaliar
se os dados ainda são sensíveis o suficiente para justificar a operação destrutiva. Para os dois
sidecars `-shm`/`-wal`, a ação de baixo risco (destrackear + ajustar `.gitignore` para `database.db-*`)
pode ser feita independentemente da decisão maior sobre os dois backups.

Responsável:
—

---

## ~~KI-028~~ — RESOLVIDO

Descrição:
Datas "puras" (`YYYY-MM-DD`, sem componente de horário) são exibidas um dia antes do valor real gravado
no banco em qualquer tela que use o padrão `new Date(string).toLocaleDateString("pt-BR")`. Causa:
`new Date("2027-07-30")` é interpretado pelo JavaScript como meia-noite UTC; `.toLocaleDateString()`
renderiza no fuso horário local do navegador — em `America/Sao_Paulo` (UTC-3), isso sempre volta um dia
(`29/07/2027`). Confirmado via `Intl.DateTimeFormat().resolvedOptions().timeZone` (`America/Sao_Paulo`,
offset 180min) e comparação direta com o valor cru da API (`garantia_data_fim: "2027-07-30"` no banco vs.
"29/07/2027" na tela). O dado persistido está sempre correto — o problema é exclusivamente de exibição.

Impacto:
Médio. Achado durante o QA Manual da V1.5 (Garantia) em `VendaDetalhe.jsx` (`garantia_data_fim`), mas o
mesmo padrão (`new Date(<campo_date_only>).toLocaleDateString("pt-BR")`) já existe em outras telas com
campos que podem ser data pura: `Garantias.jsx` (`data_finalizado`), `Clientes.jsx` (`o.data`),
`OperationalCosts.jsx` (`c.data`), `Reports.jsx` (`item.data`), `Stock.jsx` (`item.data_compra`) — nem
todos esses campos são necessariamente gravados sem horário (alguns podem ter
`datetime('now')`/`HH:MM:SS`, o que mitigaria o efeito), não auditado campo a campo nesta sessão. Os
campos novos da V1.5 (`garantia_data_inicio`/`garantia_data_fim`, sempre `date.isoformat()`, nunca com
horário) são afetados 100% das vezes, para qualquer usuário em fuso UTC-negativo — relevante para uma
feature de garantia, onde a data de vencimento exibida importa para a decisão de cobrir ou não um reparo.
Nenhum critério objetivo de interrupção de `ENGINEERING_GUIDE.md` §11 é atendido (não é mutação de dado
persistido — só exibição; não há perda de dado nem bypass de autorização), por isso não interrompeu a
sessão — caracterizado e registrado aqui, conforme o fluxo "não interrompa" da mesma seção.

Status:
Resolvido em 2026-07-30, no Encerramento da V1.5 (decisão do usuário — CTO, de corrigir dentro do escopo
da própria feature em vez de adiar). Escopo cirúrgico: só o único ponto onde `garantia_data_fim` é
exibido (`VendaDetalhe.jsx`) — as outras telas com o mesmo padrão (`Garantias.jsx`, `Clientes.jsx`,
`OperationalCosts.jsx`, `Reports.jsx`, `Stock.jsx`) usam campos que não são exclusivos da V1.5 e ficam
fora do escopo desta correção, registradas acima como conhecidas. Corrigido reaproveitando
`formatDateTime()`, helper já existente no próprio arquivo (usado para `criado_em`/`cancelado_em`/eventos
de auditoria) que já fazia o parse manual de ano/mês/dia em vez de `new Date(string)` — zero código novo,
só trocar a chamada. Validado: venda criada com `garantia_data_fim: "2027-07-30"` (confirmado via API)
agora exibe "até 30/07/2027" (antes: "29/07/2027").

Sprint prevista:
Não definida.

Responsável:
—

---

## KI-030

Descrição:
`tests/test_sentry_init.py::test_com_sentry_dsn_valido_inicializa_sem_erro` falha localmente em ambiente
Windows com Python 3.14: `import app` (via subprocess) carrega `sentry_sdk`, que importa `asyncio`, que
em `asyncio/windows_events.py` tenta importar `_overlapped` e recebe `OSError: [WinError 10106] O
provedor de serviços solicitado não pôde ser carregado ou inicializado` — falha ao inicializar um
provedor de rede do Winsock nesta máquina, não um bug de código. Achado durante a suíte completa rodada
antes do commit do Lote 4a (Sprint Housekeeping, rename `irflow_os.py` → `fluxoly_os.py`); confirmado via
`git stash` que o teste já falhava da mesma forma em `main` antes do rename — não é uma regressão
introduzida por ele.

Impacto:
Baixo. Nenhum critério objetivo de `ENGINEERING_GUIDE.md` §11 é atendido — não muta dado, não perde dado,
não faz bypass de autorização, e o código do teste em si (`import asyncio` dentro do `sentry_sdk`) não é
um caminho de produção real acessado pelo frontend. CI roda em runner Linux (GitHub Actions), onde
`asyncio/windows_events.py` nunca é importado — não deve reproduzir lá. Efeito prático: mais um teste
"vermelho" a ignorar mentalmente ao rodar a suíte localmente nesta máquina, o que atrapalha
`ENGINEERING_GUIDE.md` "nunca ignorar testes falhando" se não for documentado.

Status:
Aberto — não investigado a fundo. Atualização (2026-08-04, bootstrap de ambiente Windows nesta mesma
máquina): reproduzido de forma idêntica (`WinError 10106` no mesmo ponto) numa `.venv` nova criada com
Python 3.12.10, não só 3.14.

Hipótese descartada: o problema não é específico do Python 3.14, pois foi reproduzido também em uma
instalação limpa com Python 3.12.10. Aponta mais para driver/serviço Winsock ausente ou desabilitado
nesta instalação Windows especificamente (afeta qualquer versão de Python nesta máquina, não é por
versão). Nenhuma ação tomada; suíte segue sendo tratada como "681 passed, 1 failed (ambiente)" nesta
máquina até confirmação em CI ou outro ambiente.

Sprint prevista:
Não definida — não bloqueia a Sprint Housekeeping (achado incidental, caracterizado e reportado aqui,
conforme o fluxo "não interrompa" de `ENGINEERING_GUIDE.md` §11).

Responsável:
—

## KI-031

Descrição:
As 6 rotas do domínio Relatórios (`GET /api/relatorios/ir-phones`, `/tecnicos`, `/custos-operacionais` e
as 3 variantes `/pdf/*`) não têm nenhum teste dedicado — `grep -rl "relatorio" tests/` retorna vazio.
Achado durante a Discovery de extração de `api_reports.py` (TD-01 Phase 2, 8º domínio, 2026-08-06):
diferente dos 7 domínios já extraídos, a suíte completa (683 testes) passar não é evidência de que essas
6 rotas continuam funcionando após a extração, porque nenhum teste as exercita.

Impacto:
Baixo a médio. Nenhum critério objetivo de `ENGINEERING_GUIDE.md` §11 é atendido pela ausência de teste
em si (não é um bug de comportamento, é uma lacuna de cobertura). Mas significa que qualquer regressão
futura nessas 6 rotas (nesta extração ou em qualquer mudança seguinte) não será pega pela suíte —
depende de verificação manual ou de uso real em produção para ser detectada.

Status:
Aberto. Decisão do CTO (2026-08-06): não misturar escrita de testes novos com a extração de blueprint
(escopo cirúrgico da TD-01) — a extração segue verbatim, e esta lacuna fica registrada aqui para ser
endereçada em sprint própria de cobertura de testes.

Sprint prevista:
Não definida — candidata a sprint de cobertura de testes, fora do escopo da TD-01.

Responsável:
—

---

## ~~KI-032~~ — RESOLVIDO

Descrição:
Em `fluxoly_blueprints_api.py`, `_slug_estoque()`/`_gerar_sku_estoque()` (linhas 79-109) geram um SKU
automaticamente a partir de modelo/tipo/qualidade/descrição, mas nunca são chamados por nenhuma das 6
rotas do domínio Estoque — `criar_estoque()`/`atualizar_estoque()` usam `body.get("sku")` enviado pelo
cliente diretamente, sem gerar. Achado durante a Discovery de extração de `api_stock.py` (TD-01 Phase 2,
11º domínio, 2026-08-07): não capturado pela matriz de dependências da Phase 1
(`docs/engineering/API_DEPENDENCY_MATRIX.md`), que listava só os 4 helpers efetivamente usados
(`_normalizar_tipo_estoque`, `_normalizar_qualidade_estoque`, `_recalcular_custo_medio`,
`_status_item_estoque`).

Impacto:
Baixo. Sem efeito em runtime — código morto (mesmo padrão de KI-014), só ruído de manutenção (~30
linhas). Não migrado para `api_stock.py` nesta extração, para não misturar refatoração estrutural com
limpeza de código (mesma regra já seguida para a dep morta `garantir_pasta_backup_google_drive` na
extração de Backup) — permanece em `fluxoly_blueprints_api.py`.

Status:
Resolvido em 2026-08-08 (TD-18 — TD-01 Phase 3, Cleanup). `fluxoly_blueprints_api.py` removido por
inteiro (continha só o `Blueprint("api")` vazio, sem nenhuma rota registrada, mais estes dois helpers
mortos) — confirmado por Discovery que nenhum código consumia `_slug_estoque`/`_gerar_sku_estoque`
(geração de SKU real vive só em `api_stock.py`, via `body.get("sku")`). Único consumidor do arquivo
(`app.register_blueprint(create_api_blueprint({}))` em `fluxoly_blueprint_registry.py`) removido junto.
`app.url_map` idêntico antes/depois (122 rotas), 683 testes passando, `ruff check .` limpo. Ver
`docs/operations/PROJECT_STATUS.md` (TD-18).

Sprint prevista:
Não definida — candidato a Phase 3 (Cleanup) da TD-01
(`docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md`). Resolvido via TD-18 em 2026-08-08.

Responsável:
—

---

## KI-033

Descrição:
As 4 rotas do catálogo de Reparos (`GET/POST /reparos`, `PUT/DELETE /reparos/<id>`) não têm nenhum
teste dedicado — grep por `criar_reparo`/`atualizar_reparo`/`deletar_reparo`/`/api/reparos` em `tests/`
não retorna nada. Achado durante a Discovery de extração de `api_os.py` (TD-01 Phase 2, 12º e último
domínio, 2026-08-07): diferente do domínio OS propriamente dito (boa cobertura real — 8 módulos de
teste), essas 4 rotas nunca foram exercitadas por teste automatizado. Mesmo padrão de KI-031
(Relatórios).

Impacto:
Baixo a médio. Nenhum critério objetivo de `ENGINEERING_GUIDE.md` §11 é atendido (não é bug de
comportamento, é lacuna de cobertura). Mas significa que a suíte completa passar não é evidência de que
essas 4 rotas continuam funcionando após a extração — depende de verificação manual para ser detectada.

Status:
Aberto. Decisão do CTO (2026-08-07): não misturar escrita de testes novos com a extração final de
blueprint (escopo cirúrgico da TD-01) — a extração segue verbatim, validada por smoke test manual
(mesma técnica já usada em Relatórios/Sistema/MercadoPhone), e esta lacuna fica registrada aqui para
ser endereçada em sprint própria de cobertura de testes.

Sprint prevista:
Não definida — candidata a sprint de cobertura de testes, fora do escopo da TD-01 (mesmo destino de
KI-031).

Responsável:
—

---

## KI-034

Descrição:
`fluxoly_vendas_service.py::ajustar_desconto_item()` (BR-043 — Ajuste Comercial Autorizado, admin-only,
permite corrigir o preço de um item já vendido) recalcula e grava `vendas.valor_total` via
`repo.recalcular_valor_total_venda(cursor, venda_id)`, mas **nunca chama `fluxoly_caixa_service`** — os
únicos dois pontos de integração Vendas↔Caixa são `iniciar_venda()` e `cancelar_venda()`
(`fluxoly_vendas_service.py`, comentários "Financeiro Mínimo (BR-069)"). Achado durante a Revisão
Arquitetural do ciclo ADR-010 do Financeiro Mínimo (2026-08-10), ao rastrear todo ponto de escrita de
`vendas.valor_total` e cruzar com todo ponto de integração com `movimentacoes_caixa`.

Não é só uma divergência visual — é uma inconsistência real de dado entre `vendas.valor_total` e a
`movimentacoes_caixa` correspondente (`origem='venda'`, `origem_id=vendas.id`):

1. A movimentação de caixa é criada em `iniciar_venda()` com o `valor_unitario` da venda no momento da
   criação — um snapshot, nunca resincronizado.
2. Se um admin usa o Ajuste Comercial (BR-043) para corrigir o preço de uma venda já `concluida` (ex.:
   R$1.000 → R$800), `vendas.valor_total` passa a refletir R$800, mas a movimentação de caixa continua
   registrada com R$1.000 — o saldo do Caixa (`SOMA(entradas não estornadas) − SOMA(saídas não
   estornadas)`) fica sistematicamente R$200 maior do que deveria, sem qualquer erro ou aviso.
3. Se essa mesma venda for cancelada depois do ajuste, `cancelar_venda()` → `estornar_entrada_de_venda()`
   estorna a movimentação pelo valor original registrado nela (R$1.000), não pelo `valor_total` corrigido
   (R$800) — o estorno também carrega o valor desatualizado.

BR-043 já existia desde a V1.3 (Descontos e Aprovação, antes do Financeiro Mínimo) — este não é um
comportamento introduzido nesta sprint, é uma interação nova entre uma regra de negócio antiga
(permissão explícita de editar o preço de uma venda concluída) e uma feature nova (Caixa reagindo por
snapshot ao valor da venda no momento da criação).

Impacto:
Médio. Não atende C-03 (sem bypass de autorização) nem C-02 (nenhum dado é perdido, a movimentação
original continua íntegra no histórico), mas atende parcialmente C-01 (mutação indireta: o `valor_total`
da venda muda, mas o valor correspondente no Caixa não acompanha, e ninguém é avisado) em um caminho real
de produção (C-04 — Ajuste Comercial é uma rota ativa, usada por admin). O gatilho exige uma ação
deliberada e pouco frequente (Ajuste Comercial pós-venda), não o fluxo padrão de venda/cancelamento — por
isso não foi classificado como bloqueante para o encerramento do ciclo do Financeiro Mínimo.

Status:
Aberto. Decisão do CTO (2026-08-10, Revisão Arquitetural do ADR-010 do Financeiro Mínimo): não corrigir
nesta sprint — ampliaria o escopo justamente no encerramento do ciclo. Registrado aqui para correção em
sprint própria. A correção futura deve preservar a atomicidade já estabelecida pelo padrão do domínio:
atualizar `vendas.valor_total` e resincronizar/ajustar a `movimentacoes_caixa` correspondente na mesma
transação (mesmo cursor), nunca em dois commits separados — mesmo princípio já usado em
`iniciar_venda()`/`cancelar_venda()` com `unidades_service`/`caixa_service`.

Sprint prevista:
Não definida — candidata a sprint de correção do domínio Vendas/Financeiro, fora do escopo do
Encerramento do ADR-010 do Financeiro Mínimo.

Responsável:
—
