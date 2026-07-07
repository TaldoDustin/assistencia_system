# SPRINT 02 — Infraestrutura de Qualidade

**Status:** EM ANDAMENTO — Sprint 2.2 (T-01 a T-04) concluída em 2026-07-07 · Sprint 2.3 (T-12 a T-16) concluída em 2026-07-07 · Sprint 2.4 (T-17 a T-20) concluída em 2026-07-07  
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
**Depende de:** T-12 (fixtures da Sprint 2.3) · **Status:** Mergeado em `main` em 2026-07-07.

### T-18 — `tests/test_os_creation_query.py` ✅ CONCLUÍDA
**41 casos:** criação válida, status/valores/data padrão, tipo upgrade→assistência, `interna_ir_phones`, múltiplos reparos, campos obrigatórios, reparo/vendedor/peça inválidos, técnico fora da whitelist (aceito — caracterização), consumo de peça do estoque, listagem com filtros (status/tipo/técnico/vendedor/modelo/texto/data), ausência de paginação (caracterização), obter por id, 404, histórico de cliente.
**Achado durante a implementação:** bug no próprio fixture `criar_os()` — preenchia a coluna `aparelho` mas esquecia `modelo` (colunas distintas no schema). Corrigido no teste, não em produção.
**Depende de:** T-17 · **Status:** Mergeado em `main` em 2026-07-07.

### T-19 — `tests/test_os_update_status.py` ✅ CONCLUÍDA (com 2 correções de produção aprovadas)
**26 casos:** atualização de dados básicos/técnico/observações/modelo, 404, campos obrigatórios, reparo/vendedor inválido, sem sessão, `data_finalizado` ao finalizar/reabrir, troca de peça, matriz completa das 16 transições entre os 4 status válidos (todas permitidas — não há máquina de estados), status desconhecido/vazio rejeitado, idempotência, cancelar devolve peças ao estoque.
**Achados durante a investigação (antes de qualquer teste escrito), corrigidos com aprovação explícita do usuário:**
- `PATCH /api/ordens/<id>/status` aceitava status desconhecido/lixo e o normalizava silenciosamente para "Em andamento" em vez de rejeitar com 400 — commit `c85a321`.
- `PUT /api/ordens/<id>` sem o campo `status` reabria silenciosamente uma OS Finalizada para "Em andamento" e apagava `data_finalizado` — commit `e755f25`. Confirmado com reprodução manual antes e depois do fix.

Ambos os fixes seguem o mesmo padrão: `normalizar_status_os(valor, status_padrao="")` — mesma abordagem já usada pela rota legada `POST /atualizar_status`.
**Achado caracterizado, não corrigido:** reativar uma OS Cancelada via `PATCH /api/ordens/<id>/status` (API) não re-consome peças do estoque, diferente da rota legada `POST /atualizar_status`, que re-consome e valida estoque suficiente. Reportado para decisão.
**Depende de:** T-17 · **Status:** Mergeado em `main` em 2026-07-07.

### T-20 — `tests/test_os_deletion_security.py` ✅ CONCLUÍDA
**21 casos:** exclusão válida com devolução de peças ao estoque, exclusão de OS finalizada permitida (caracterização — não há essa proteção), exclusão inexistente sem erro (caracterização — não há 404), sem sessão, sem restrição de perfil (caracterização — tecnico e vendedor podem excluir qualquer OS), parâmetros inválidos no roteamento, SQL injection (tautologia, `DROP TABLE`, em campos de texto e query params), payload vazio e JSON malformado em POST/PUT/PATCH.
**Depende de:** T-17 · **Status:** Mergeado em `main` em 2026-07-07.

**Cobertura ao final da Sprint 2.4:** 161 testes (73 da Sprint 2.2+2.3 + 88 novos), todos passando, estáveis em 3 execuções consecutivas. `pytest --cov`: `irflow_blueprints_auth.py` 83%, `irflow_core.py` 88%, `app.py` 52%, `irflow_os.py` 60% (subiu de 15%), `irflow_blueprints_api.py` 32% (subiu de 19%). Cobertura global do repositório 26% (subiu de 19%). A meta de 40% do Definition of Done da Sprint 2 segue dependendo de `test_pricing.py`/`test_shopping.py` (T-06/T-07), ainda não iniciadas. `test_os.py` (T-05, abaixo) foi substituído pelos 3 módulos desta sprint — mais granulares que o originalmente escopado.

---

### ~~T-05~~ — `tests/test_os.py` — SUBSTITUÍDA pela Sprint 2.4
**Escopo original (10 casos)** foi absorvido e ampliado pelos 3 módulos da Sprint 2.4 (T-18/T-19/T-20 acima, 88 casos no total) — granularidade maior (criação/consulta, atualização/status, exclusão/segurança em arquivos separados) do que o único `test_os.py` originalmente previsto.

---

### T-06 — `tests/test_pricing.py`
**7 casos:** listar preços, sugerir com modelo/reparo existentes, modelo inexistente, sem parâmetros, múltiplos reparos (valida soma), criar como admin, criar como não-admin (403)  
**Depende de:** T-03

---

### T-07 — `tests/test_shopping.py`
**8 casos:** listar, criar, criar sem campos, atualizar, PATCH status válido, PATCH status inválido, deletar, listar agrupado  
**Depende de:** T-03

---

### T-08 — Coverage config
**Arquivo:** `pyproject.toml` (seção `[tool.coverage]`)  
**Threshold:** `fail_under = 40` nos módulos alvo  
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

- [ ] `pytest tests/` passa sem falhas em máquina limpa
- [ ] Cobertura >= 40% nos módulos alvo
- [ ] `ruff check .` passa (com baseline documentado)
- [ ] `npm run lint` passa sem erros
- [ ] GitHub Actions CI verde em push para `main`
- [ ] Nenhum teste cria ou modifica `database.db`
- [ ] `.env.example` com todas as variáveis
- [ ] `ENGINEERING_GUIDE.md` permite setup local sem ajuda
- [ ] `PROJECT_STATUS.md` atualizado com novo score e cobertura
- [ ] `KNOWN_ISSUES.md`: KI-007 (commits) marcado como mitigado
