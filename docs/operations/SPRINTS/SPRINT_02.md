# SPRINT 02 — Infraestrutura de Qualidade

**Status:** EM ANDAMENTO — Sprint 2.2 (T-01 a T-04) concluída em 2026-07-07 · Sprint 2.3 (T-12 a T-16) concluída em 2026-07-07 · Sprint 2.4 (T-17 a T-20) concluída em 2026-07-07, mergeada em `main` em 2026-07-10 · Sprint 2.5 (T-21 a T-25) concluída e mergeada em `main` em 2026-07-07 · Sprint 2.6 (T-26, T-27) concluída e mergeada em `main` em 2026-07-07  
**Data de criação:** 2026-07-06  
**Tipo:** Infraestrutura / Qualidade  
**Baseado em:** Auditoria de infraestrutura de 2026-07-06

---

## Objetivo

Estabelecer pipeline de CI, testes backend com isolamento e cobertura >= 40% nas rotas críticas.
Esta sprint não entrega nenhuma feature de negócio — entrega a base que garante que as próximas features não quebrem o que já existe.

## Motivação

A auditoria de 2026-07-06 revelou:
- `.github/workflows/` não existe — nenhuma automação de qualidade
- `requirements-dev.txt` não existe — sem tooling de desenvolvimento formalizado
- 7 scripts de teste ad-hoc, todos abrindo `database.db` real
- Nenhum pytest, nenhuma fixture, nenhum isolamento
- Lint backend zero configurado

Sem CI, qualquer commit pode introduzir regressões em produção sem detecção automática.

---

## Diagnóstico: Estado Atual vs. Estado-Alvo

| Área | Estado Atual | Estado-Alvo |
|------|-------------|-------------|
| CI/CD | Ausente | GitHub Actions em push/PR |
| Lint backend | Ausente | Ruff configurado + CI bloqueante |
| Lint frontend | ESLint sem enforcement | ESLint no CI bloqueante |
| Testes backend | 7 scripts ad-hoc no banco real | pytest + fixtures isoladas (in-memory) |
| Isolamento de testes | Zero | SQLite in-memory por sessão |
| Cobertura | Zero | >= 40% nas rotas críticas |
| `requirements-dev.txt` | Ausente | pytest, pytest-cov, ruff |
| `.env.example` | Ausente | Documentado completo (20 vars) |
| Pre-commit hooks | Ausente | ruff + eslint |
| `ENGINEERING_GUIDE.md` | Ausente | Criado e completo |

---

## Premissas e Decisões de Design

### P-01: Estratégia de isolamento de banco
Não será feito app factory (`create_app()`) — isso é Sprint 4. A abordagem é:
- `IR_FLOW_TEST_DB=:memory:` definido antes de qualquer `import app`
- `conftest.py` com fixture `client` e banco in-memory
- Cada sessão começa com schema limpo via `init_db()`

**Validação obrigatória antes de implementar:** `grep -n "DB_PATH\|database.db\|connect(" app.py`
Se o banco for lido em nível de módulo (fora de função), o override via env var não funcionará. Fallback: arquivo temporário `test_tmp.db` deletado no teardown.

### P-02: Ruff em vez de flake8
Ruff é 10-100x mais rápido, substitui flake8 + isort. Configurado em `pyproject.toml`.

### P-03: Escopo de cobertura prioritizado
Target de 40% aplica-se apenas a: `irflow_os.py`, auth, OS, preços, shopping list.
MercadoPhone e backup ficam fora do escopo desta sprint.

### P-04: Playwright no CI como não-bloqueante
`continue-on-error: true` no job E2E até Sprint 3. Foco desta sprint é backend.

---

## Tarefas

### T-01 — `requirements-dev.txt` ✅ CONCLUÍDA
**Arquivo:** `requirements-dev.txt` (novo)  
**Conteúdo:**
```
-r requirements.txt
pytest>=8.0,<9
pytest-cov>=5.0,<6
pytest-flask>=1.3,<2
ruff>=0.5,<1
```
**Depende de:** nada — primeira tarefa  
**Critério:** `pip install -r requirements-dev.txt` sem erros
**Status:** Entregue na infraestrutura de CI da Sprint 2 (commit `563765f`).

---

### T-02 — Ruff config (`pyproject.toml`) ✅ CONCLUÍDA
**Arquivo:** `pyproject.toml` (novo)  
**Regras:** `E`, `F`, `W`, `I` · `line-length = 120` · `target-version = "py311"`  
**Depende de:** T-01  
**Critério:** `ruff check .` executa (com lista de exceções baseline documentada)
**Status:** Entregue na infraestrutura de CI da Sprint 2 (commit `563765f`). Regras efetivas incluem também `UP`, `B`, `SIM`, `C4`.

---

### T-03 — `conftest.py` com banco isolado ✅ CONCLUÍDA (com desvio de P-01 documentado)
**Arquivos:** `tests/__init__.py`, `tests/conftest.py`  
**Fixtures:** `app`, `client`, `auth_client`  
**Depende de:** T-01 + validação de P-01  
**Critério:** `pytest tests/` importa sem erro, nenhum `database.db` modificado
**Status:** Entregue. **Desvio de P-01:** `DB_PATH` é lido em nível de módulo em `app.py` (confirmado — a validação prevista em P-01 se aplicou), então o plano original de `IR_FLOW_TEST_DB=:memory:` não é usado. O fallback já previsto em P-01 foi adotado: `IR_FLOW_DATA_DIR` aponta para um diretório temporário (`tempfile.mkdtemp()`) definido **antes** do `import app`, redirecionando `DB_PATH` para um arquivo SQLite isolado (não `:memory:`, mas igualmente nunca toca `database.db`).

---

### T-04 — `tests/test_auth.py` ✅ CONCLUÍDA (Sprint 2.2, 2026-07-07)
**18 casos** (mais que os 8 originalmente escopados): login via API JSON (válido, senha errada, usuário inexistente, sem body, usuário inativo, resposta não expõe hash), `/api/auth/me` (sem sessão, com sessão), `/api/auth/logout` (com e sem sessão ativa), rotas legadas `/login`/`/logout` (formulário, redirecionamentos, sessão), e controle de acesso por perfil em `/usuarios/novo` (sem sessão, não-admin, admin).
**Depende de:** T-03
**Achado durante a execução:** `irflow_blueprints_api.py` tinha um endpoint `/shopping-list` duplicado (código legado da tabela `compras`) que impedia `app.py` de sequer importar (`AssertionError` do Flask). Corrigido e documentado em KI-012 antes de rodar os testes pela primeira vez — sem essa correção, T-03/T-04 não eram executáveis.
**Revisão:** code review independente (8 ângulos, ver commit `da21d02` e `859d695`) — aprovado para merge sem bloqueios. Gaps de cobertura identificados para follow-up: `/usuarios/editar`, `/usuarios/deletar`, perfil `vendedor`, usuário duplicado em `/usuarios/novo`.
**Status:** Mergeado em `main` em 2026-07-07.

---

## Sprint 2.3 — Cobertura da API de Usuários e Autorização

**Objetivo:** fechar os gaps de cobertura deixados pela Sprint 2.2 (`/usuarios/editar`, `/usuarios/deletar`, perfil `vendedor`, usuário duplicado) e expandir para CRUD de usuários via API, matriz de permissões por perfil, sessão (expiração/cookie/logout) e resiliência de entrada (SQLi, payloads inválidos, content-type) — antes de testar qualquer regra de negócio de domínio (OS, preços, estoque).

### T-12 — Fixtures compartilhados em `tests/conftest.py` ✅ CONCLUÍDA
Move `client`, `usuario_admin`, `usuario_tecnico`, `usuario_inativo` de `test_auth.py` para `conftest.py` (DRY — 4 novos módulos precisam deles). Adiciona `usuario_vendedor` e o fixture-factory `login_como` (login via `/api/auth/login`).
**Depende de:** T-03 · **Status:** Mergeado em `main` em 2026-07-07.

### T-13 — `tests/test_users.py` ✅ CONCLUÍDA
**18 casos:** listar/criar/atualizar/excluir em `/api/usuarios` — caso feliz, usuário duplicado, campos obrigatórios ausentes, perfil desconhecido (fallback `tecnico`), auto-desativação/auto-exclusão bloqueadas, acesso por perfil não-admin, uid inexistente em PUT/DELETE.
**Depende de:** T-12 · **Status:** Mergeado em `main` em 2026-07-07.

### T-14 — `tests/test_permissions.py` ✅ CONCLUÍDA
**13 casos:** matriz de acesso por perfil (admin/tecnico/vendedor) em `/usuarios`, `/usuarios/editar`, `/usuarios/deletar` (rotas legadas) e `/api/usuarios`, `/api/ordens/<id>` (API) — cobre 200/401/403/404. Inclui caso de perfil desconhecido gravado direto no banco tentando rota admin-only.
**Achado durante a execução:** a suposição inicial de que `GET /usuarios` aplicava `ROUTE_PERMISSIONS` estava errada — esse path é interceptado por `LEGACY_REACT_REDIRECTS` antes do `before_request` de autenticação (mesmo padrão já documentado para `/login`). Testes ajustados para caracterizar o comportamento real.
**Depende de:** T-12 · **Status:** Mergeado em `main` em 2026-07-07.

### T-15 — `tests/test_session.py` ✅ CONCLUÍDA
**10 casos:** acesso sem sessão, acesso após logout, logout chamado duas vezes seguidas, cookie com assinatura adulterada, cookie não assinado, sessão expirada. Sessão expirada é simulada forjando um cookie assinado (mesmo segredo/serializer da aplicação) com timestamp no passado, já que não há `PERMANENT_SESSION_LIFETIME` configurado explicitamente (default do Flask, 31 dias) — não seria viável esperar tempo real decorrer.
**Depende de:** T-12 · **Status:** Mergeado em `main` em 2026-07-07.

### T-16 — `tests/test_security.py` ✅ CONCLUÍDA (com desvio de escopo documentado)
**14 casos:** SQL injection no login (tautologia, `DROP TABLE`, comentário SQL, `UNION SELECT`), campos obrigatórios ausentes, payload vazio, corpo ausente, JSON malformado, Content-Type incorreto (form-urlencoded, `text/plain`, ausente).
**Desvio:** um caso do escopo original (JSON sintaticamente válido mas de tipo errado — array no lugar de objeto) foi removido da suíte por expor uma exceção não tratada em `auth_login()` (`AttributeError: 'list' object has no attribute 'get'`). Por orientação do usuário, a Sprint 2.3 não registra achados em `KNOWN_ISSUES.md` nem mantém testes deliberadamente falhos — o achado foi reportado separadamente para decisão.
**Depende de:** T-12 · **Status:** Mergeado em `main` em 2026-07-07.

**Cobertura ao final da Sprint 2.3:** 73 testes (18 da Sprint 2.2 + 55 novos), todos passando. `pytest --cov`: `irflow_blueprints_auth.py` 83%, `app.py` 52%, `irflow_core.py` 68%, `irflow_blueprints_api.py` 19% (arquivo de ~3100 linhas — só a fatia de `/api/usuarios`, `/api/auth/*` e `/api/ordens/<id>` usada pelos testes está coberta). Cobertura global do repositório 19% (inclui scripts ad-hoc fora de escopo — `smoke_test_full.py`, `test_routes.py`, etc. — que a Sprint 2 nunca pretendeu cobrir; ver P-03). A meta de 40% do Definition of Done desta sprint segue dependendo de T-05/T-06/T-07 (`test_os.py`, `test_pricing.py`, `test_shopping.py`), ainda não iniciadas.

---

## Sprint 2.4 — Cobertura das Regras de Negócio de Ordens de Serviço

**Objetivo:** expandir a cobertura automatizada das regras de negócio de OS (criação, consulta, atualização, status, exclusão, segurança), sem alterar comportamento da aplicação — exceto correções mínimas de bugs encontrados durante a investigação, com aprovação explícita do usuário antes de cada uma.

### T-17 — Fixtures compartilhados de OS em `tests/conftest.py` ✅ CONCLUÍDA
`reparo_padrao_id`/`dois_reparos_ids` (lêem reparos já semeados por `sincronizar_reparos_padrao()`), `payload_os_valido` (factory de payload mínimo válido), `criar_os` (factory que insere OS direto no banco, com limpeza automática), `criar_item_estoque` (factory de item de estoque).
**Depende de:** T-12 (fixtures da Sprint 2.3) · **Status:** Mergeado em `main` em 2026-07-10.

### T-18 — `tests/test_os_creation_query.py` ✅ CONCLUÍDA
**41 casos:** criação válida, status/valores/data padrão, tipo upgrade→assistência, `interna_ir_phones`, múltiplos reparos, campos obrigatórios, reparo/vendedor/peça inválidos, técnico fora da whitelist (aceito — caracterização), consumo de peça do estoque, listagem com filtros (status/tipo/técnico/vendedor/modelo/texto/data), ausência de paginação (caracterização), obter por id, 404, histórico de cliente.
**Achado durante a implementação:** bug no próprio fixture `criar_os()` — preenchia a coluna `aparelho` mas esquecia `modelo` (colunas distintas no schema). Corrigido no teste, não em produção.
**Depende de:** T-17 · **Status:** Mergeado em `main` em 2026-07-10.

### T-19 — `tests/test_os_update_status.py` ✅ CONCLUÍDA (com 2 correções de produção aprovadas)
**26 casos:** atualização de dados básicos/técnico/observações/modelo, 404, campos obrigatórios, reparo/vendedor inválido, sem sessão, `data_finalizado` ao finalizar/reabrir, troca de peça, matriz completa das 16 transições entre os 4 status válidos (todas permitidas — não há máquina de estados), status desconhecido/vazio rejeitado, idempotência, cancelar devolve peças ao estoque.
**Achados durante a investigação (antes de qualquer teste escrito), corrigidos com aprovação explícita do usuário:**
- `PATCH /api/ordens/<id>/status` aceitava status desconhecido/lixo e o normalizava silenciosamente para "Em andamento" em vez de rejeitar com 400 — commit `c85a321`.
- `PUT /api/ordens/<id>` sem o campo `status` reabria silenciosamente uma OS Finalizada para "Em andamento" e apagava `data_finalizado` — commit `e755f25`. Confirmado com reprodução manual antes e depois do fix.

Ambos os fixes seguem o mesmo padrão: `normalizar_status_os(valor, status_padrao="")` — mesma abordagem já usada pela rota legada `POST /atualizar_status`. **Nota de merge (2026-07-10):** estes dois commits ficaram presos nesta branch por 3 dias sem chegar a `main` — extraídos via `hotfix/status-os-padrao-vazio` (KI-015, B-14) antes do restante desta branch, ao retomar o Sprint 2.
**Achado caracterizado, não corrigido:** reativar uma OS Cancelada via `PATCH /api/ordens/<id>/status` (API) não re-consome peças do estoque, diferente da rota legada `POST /atualizar_status`, que re-consome e valida estoque suficiente. Reportado para decisão — já registrado como exemplo em `docs/engineering/ENGINEERING_GUIDE.md` §11.
**Depende de:** T-17 · **Status:** Mergeado em `main` em 2026-07-10.

### T-20 — `tests/test_os_deletion_security.py` ✅ CONCLUÍDA
**21 casos:** exclusão válida com devolução de peças ao estoque, exclusão de OS finalizada permitida (caracterização — não há essa proteção), exclusão inexistente sem erro (caracterização — não há 404), sem sessão, sem restrição de perfil (caracterização — tecnico e vendedor podem excluir qualquer OS), parâmetros inválidos no roteamento, SQL injection (tautologia, `DROP TABLE`, em campos de texto e query params), payload vazio e JSON malformado em POST/PUT/PATCH.
**Depende de:** T-17 · **Status:** Mergeado em `main` em 2026-07-10.

**Status desta sprint:** aprovada e **mergeada em `main` em 2026-07-10** (merge com resolução manual de conflitos — a branch divergiu antes da reorganização de `docs/` e do rename de marca; conflitos de documentação, sem impacto em código além dos 2 hotfixes já extraídos separadamente). 88 testes novos (161 na branch original: 73 pré-existentes + 88). `test_os.py` (T-05, ver abaixo) foi substituído pelos 3 módulos desta sprint.

---

### ~~T-05~~ — `tests/test_os.py` — SUBSTITUÍDA pela Sprint 2.4
**Escopo original (10 casos)** foi absorvido e ampliado pelos 3 módulos da Sprint 2.4 (T-18/T-19/T-20 acima, 88 casos no total) — granularidade maior (criação/consulta, atualização/status, exclusão/segurança em arquivos separados) do que o único `test_os.py` originalmente previsto.

---

## Sprint 2.5 — Cobertura das Regras de Negócio de Estoque

**Objetivo:** expandir a cobertura automatizada do módulo de Estoque — cadastro, consulta, movimentação, integração com OS e segurança — partindo de `main` (não da Sprint 2.4, ainda não revisada), para manter a branch independente.

### T-21 — Fixtures compartilhados de estoque em `tests/conftest.py` ✅ CONCLUÍDA
`reparo_padrao_id` e `criar_item_estoque` (factory com limpeza de lotes/movimentações/os_pecas). Recriados nesta branch — os equivalentes da Sprint 2.4 não estão em `main`.
**Depende de:** T-12 · **Status:** Mergeada em `main` em 2026-07-07.

### T-22 — `tests/test_stock_creation_query.py` ✅ CONCLUÍDA
**25 casos:** criação válida, lote inicial + movimentação de entrada, quantidade zero sem lote, campos obrigatórios, peça duplicada (caracterização: permitida, sem constraint de unicidade), fornecedor livre, tipo/qualidade desconhecidos normalizam para "Outros"/"Padrao", modelo desconhecido aceito como texto livre (diferente da rota legada, que rejeita), quantidade decimal trunca, quantidade extremamente alta aceita com precisão, listagem com filtros, itens zerados ocultos por padrão, totais agregados.
**Decisão de escopo (ajuste do usuário):** limitações de contrato que não são regra de negócio (ausência de `GET /api/estoque/<id>` individual, paginação, ordenação customizável) não geraram teste dedicado — só registro no relatório final.
**Achado durante a implementação:** os testes de filtro revelaram um bug real de produção — ordem de parâmetros SQL trocada em `listar_estoque()`, fazendo todo filtro (modelo/tipo/qualidade) retornar lista vazia. Corrigido via `hotfix/estoque-ordem-parametros-filtro` (commit `44be10c`) antes de continuar — ver B-12 em `PROJECT_STATUS.md`.
**Depende de:** T-21 · **Status:** Mergeada em `main` em 2026-07-07.

### T-23 — `tests/test_stock_movement.py` ✅ CONCLUÍDA
**10 casos:** ajuste positivo via PUT (entrada, novo lote), ajuste negativo via PUT (saida correta, consumo FIFO de lotes, nunca deixa saldo negativo — teste de regressão para o hotfix do saldo negativo), saldo final após sequência de ajustes, ajuste para o mesmo valor não gera movimentação, forma da resposta de `GET /api/estoque/movimentacoes`.
**Critério de isolamento (pedido do usuário):** nenhum teste depende da ordem cronológica das movimentações globais — saldo/histórico por item são verificados via consulta direta ao banco filtrada por `estoque_id`; o endpoint global (últimas 30 movimentações do sistema inteiro) só é testado quanto à forma da resposta.
**Depende de:** T-21 · **Status:** Mergeada em `main` em 2026-07-07.

### T-24 — `tests/test_stock_os_integration.py` ✅ CONCLUÍDA (escopo ampliado)
**15 casos:** consumo automático (peça única, múltiplas peças, sem peças), mesma peça em mais de uma OS (duas OS consomem enquanto há estoque, terceira falha ao esgotar), devolução ao estoque (cancelamento via status, exclusão de OS em andamento, exclusão de OS finalizada não devolve), alteração de quantidade da peça numa OS, remoção de peça, substituição de peça por outra, compatibilidade (universal, específica, incompatível bloqueia, atualização via PUT muda consumos futuros).
**Escopo ampliado a pedido do usuário** além do plano original: alteração/remoção/substituição de peças e concorrência entre OS pela mesma peça — cenários que "costumam revelar muitos bugs" segundo a revisão do plano.
**Depende de:** T-21 · **Status:** Mergeada em `main` em 2026-07-07.

### T-25 — `tests/test_stock_security.py` ✅ CONCLUÍDA
**19 casos:** sem sessão, `DELETE /api/estoque/<id>` (exclusão válida, bloqueada quando peça em uso em OS aberta — regra real —, permitida quando OS finalizada, inexistente sem erro, sem restrição de perfil — caracterização, mesmo padrão de `DELETE /api/ordens/<id>` na Sprint 2.4), payload vazio, JSON malformado, item inexistente em PUT (404), Content-Type incorreto, SQL injection.
**Depende de:** T-21 · **Status:** Mergeada em `main` em 2026-07-07.

**Hotfixes aplicados durante a Sprint 2.5 (ADR-004):**
1. `hotfix/estoque-diff-quantidade-negativa` (commit `584c501`) — diff de movimentação em `PUT /api/estoque/<id>` usava quantidade não limitada a zero, inflando o histórico de saída. Critérios C-01 (mutação silenciosa) + C-04 (caminho real de produção) confirmados.
2. `hotfix/estoque-ordem-parametros-filtro` (commit `44be10c`) — ordem de parâmetros SQL errada quebrava todo filtro de `GET /api/estoque`. **Não se encaixa perfeitamente** nos critérios C-01–C-04 do `ENGINEERING_GUIDE.md` §11 (é leitura incorreta, não mutação de dado) — aplicado o mesmo tratamento pela severidade. **Backlog registrado:** critério novo C-05 — "Consulta incorreta em fluxo oficial" — ver `PROJECT_STATUS.md` § Próximos Objetivos (curto prazo, item 6) para o rascunho.

**Status desta sprint:** aprovada e **mergeada em `main` em 2026-07-07** (merge fast-forward, sem conflitos). Os 2 hotfixes já estavam em `main` desde a investigação; o restante (fixtures + 4 módulos de teste) entrou junto neste merge.

**Cobertura medida em `main` pós-merge (`pytest-cov`):** 142 testes (73 pré-existentes + 69 novos), todos passando. Números idênticos aos medidos na branch antes do merge, confirmando que o fast-forward não alterou nada: `irflow_blueprints_auth.py` 83%, `irflow_core.py` 78%, `app.py` 52%, `irflow_os.py` 55%, `irflow_blueprints_api.py` 34%. Cobertura global do repositório 26%. A meta de 40% do Definition of Done da Sprint 2 segue dependendo de `test_pricing.py`/`test_shopping.py` (não iniciadas) e do merge da Sprint 2.4.

---

### T-06 — `tests/test_pricing.py` ✅ CONCLUÍDA (2026-07-11, escopo ampliado)
**27 casos** (planejado: 7) — unitários de `irflow_price_tables.py` (normalização de modelo/serviço,
`sugerir_preco_tabela` com soma/dedup de serviços, `encontrar_servico_tabela` com correspondência
fuzzy por token, round-trip `salvar_tabelas_preco`/`carregar_tabelas_preco`) mais integração de
`/api/precos*` (autenticação, autorização admin, `sugerir` com parâmetros ausentes/inválidos).
**Depende de:** T-03

---

### T-07 — `tests/test_shopping.py` ✅ CONCLUÍDA (2026-07-11, escopo ampliado)
**34 casos** (planejado: 8) — CRUD completo, paginação/filtros, matriz de transição de status
(válida/inválida/idempotente/estado terminal), bloqueio de compra simultânea, cancelamento (soft
delete), agrupamento e auditoria (`/logs`, BR-016). Achado durante a escrita: bug real em
`POST /api/shopping-list` (quantidade `0` normalizada silenciosamente para `1`) — corrigido via
`hotfix/quantidade-zero-shopping-list` (KI-016) antes de continuar, conforme política de
interrupção de sprint do `CLAUDE.md`/`ENGINEERING_GUIDE.md` §11.
**Depende de:** T-03

---

### T-08 — Coverage config ✅ CONCLUÍDA (2026-07-11)
**Arquivo:** `pyproject.toml` (seção `[tool.coverage.report]`)  
**Threshold:** `fail_under = 40` — aplicado após cobertura real medida em 43%, com aprovação
explícita do usuário para antecipar do cronograma original (Sprint 3=20%, Sprint 4=40%).
`.github/workflows/ci.yml` também atualizado — removido `continue-on-error` do job `Coverage`.
**Depende de:** T-04, T-05, T-06, T-07

---

### T-09 — GitHub Actions CI
**Arquivo:** `.github/workflows/ci.yml`  
**Jobs:** `backend-lint` → `backend-test` · `frontend-lint` → `frontend-build` · `e2e` (não-bloqueante)  
**Depende de:** T-02, T-08

---

### T-10 — `.env.example`
**20 variáveis** documentadas com comentários e defaults seguros  
**Depende de:** nada — independente

---

### T-11 — `ENGINEERING_GUIDE.md`
Criado na sessão de 2026-07-06 como parte da reestruturação de documentação.  
**Status:** Entregue antecipadamente.

---

## Sprint 2.6 — Padronização de Validação e Parsing ✅ CONCLUÍDA (2026-07-07)

Inserida fora da sequência original T-05→T-09 (não bloqueia nem é bloqueada por elas) para
resolver duplicação de parsing/validação encontrada em `irflow_blueprints_api.py` antes de
escrever as suítes de teste T-05/T-06/T-07 sobre um contrato de erro inconsistente.

### T-26 — `irflow_validation.py`
**Arquivo:** `irflow_validation.py` (novo)
**Funções:** `parse_int`, `parse_float`, `safe_json`, `validate_positive_number` — sentinel
`None` para entrada presente-mas-inválida, distinto do `default` usado para ausente/vazia.
`require_fields` foi desenhada, implementada e removida na mesma sprint: nenhum call site do
arquivo validava dict bruto sem antes derivar/stripar a variável, tornando a substituição
insegura (edge case de string só-com-espaços).
**Depende de:** nada — independente
**Status:** Concluída. 17 testes unitários em `tests/test_validation.py`, 100% de cobertura do módulo.

---

### T-27 — Aplicar a camada em `irflow_blueprints_api.py`
**Auditoria:** 22 ocorrências idênticas de `request.get_json(silent=True) or {}`, ~65
conversões `int()` e ~35 `float()` sobre `request.args`/corpo JSON, ~13 checagens
`if not X or Y <= 0`. `Decimal` não é usado no projeto — nenhum utilitário criado para ele.
**Achado durante a auditoria:** 9 desses pontos de parsing (em `shopping_list`,
`reposicao_sugerida_estoque`, `criar_ordem`, `atualizar_ordem`, `criar_estoque`,
`atualizar_estoque`, `criar_custo`, `atualizar_custo`, `salvar_preco`) ocorriam **antes** de
qualquer `try/except` da rota — um valor não numérico derrubava a rota com 500 não tratado.
Corrigido em commit `fix:` isolado (KI-013), com checagem explícita do sentinel `None` dobrada
sobre a validação de negócio já existente em cada rota (não silenciava o erro como valor
default). Os ~30 pontos restantes, já protegidos por `try/except` genérico, foram substituídos
em commit `refactor:` separado, sem mudança de comportamento observável — exceto o parsing de
`os_id` em `shopping_create`, que trocou uma mensagem de erro genérica com exceção Python vazada
(`Erro ao criar item: invalid literal for int()...`, violava `CODE_STYLE.md`) por uma mensagem
de validação explícita; ambas retornam 400.
**Achado colateral:** bloco `def criar_estoque():` duplicado e morto (nunca roteado, linhas
220-267) — mesma origem do KI-012, mas sem efeito em runtime. Registrado como KI-014, não
corrigido nesta sprint (fora de escopo — parsing/validação, não limpeza de código morto).
**Escopo:** apenas `irflow_blueprints_api.py`. Blueprints HTML (`admin`, `inventory`, `orders`,
`auth`) usam `flash()`/`redirect()`, contrato de resposta diferente — não tocados.
**Depende de:** T-26
**Status:** Concluída. 21 testes de regressão novos (`tests/test_api_parsing.py`,
`tests/test_api_parsing_refactor.py`) cobrindo as 9 rotas corrigidas e as rotas de
shopping-list/MercadoPhone refatoradas. `irflow_validation.py` adicionado à medição de
cobertura (`pyproject.toml`). Suíte completa pós-merge com Sprint 2.3/2.5: ver
`docs/operations/PROJECT_STATUS.md`.

---

## Sequência de Execução

```
T-01 ──┬──► T-02
       └──► T-03 ──┬──► T-04 ──┐
                   ├──► T-05 ──┤
                   ├──► T-06 ──┤
                   └──► T-07 ──┴──► T-08 ──► T-09

T-10 (independente, qualquer momento)
T-11 (concluída antecipadamente)
```

---

## Riscos

| ID | Risco | Prob. | Impacto | Mitigação |
|----|-------|-------|---------|-----------|
| RS-01 | `app.py` lê DB path em nível de módulo | Média | Alto | **Materializado** — confirmado via grep. Mitigado com fallback de arquivo temporário (`IR_FLOW_DATA_DIR`), conforme previsto |
| RS-02 | Ruff encontra centenas de erros legados | Alta | Médio | Rodar baseline primeiro. `--select` restritivo inicialmente |
| RS-03 | Playwright flaky no CI | Alta | Médio | `continue-on-error: true` até Sprint 3 |
| RS-04 | 40% de cobertura inatingível sem tocar módulos acoplados | Média | Médio | Restringir alvo às 4 áreas. Ajustar threshold se necessário |
| RS-05 | Background jobs não desativados — threads abertas nos testes | Média | Baixo | Mitigado — `IR_FLOW_ENABLE_BACKGROUND_JOBS=0` e `MERCADO_PHONE_SYNC_ENABLED=0` em `conftest.py` |
| RS-06 (novo) | Endpoint duplicado em arquivo de 3000+ linhas pode travar o boot do Flask sem aviso até alguém rodar a suíte | Média | Crítico | Materializado uma vez (KI-012). Sem guarda dedicada ainda — candidato a `test_smoke_app_boots` explícito na Sprint 2.3 |

---

## Definition of Done

- [x] `pytest tests/` passa sem falhas em máquina limpa — 331 testes, 2026-07-11
- [x] Cobertura >= 40% nos módulos alvo — 43% global, gate bloqueante em `pyproject.toml`
- [ ] `ruff check .` passa (com baseline documentado) — **vermelho em `main`, 20 erros pré-existentes não introduzidos nesta sprint, registrado como KI-017/R-08, corrigir antes da Sprint 3**
- [ ] `npm run lint` passa sem erros
- [ ] GitHub Actions CI verde em push para `main` — bloqueado por KI-017 (job `Lint` falha, `backend`/`frontend` não rodam)
- [x] Nenhum teste cria ou modifica `database.db` — isolamento via `IR_FLOW_DATA_DIR`
- [ ] `.env.example` com todas as variáveis
- [ ] `ENGINEERING_GUIDE.md` permite setup local sem ajuda
- [ ] `PROJECT_STATUS.md` atualizado com novo score e cobertura — cobertura atualizada (43%); recálculo formal do score fica para a próxima revisão, mesma disciplina já aplicada em revisões anteriores (não decidir unilateralmente aqui)
- [ ] `KNOWN_ISSUES.md`: KI-007 (commits) marcado como mitigado
