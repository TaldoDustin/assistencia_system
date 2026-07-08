# SPRINT 02 — Infraestrutura de Qualidade

**Status:** EM ANDAMENTO — Sprint 2.2 (T-01 a T-04) concluída em 2026-07-07; Sprint 2.6 (T-12, T-13) concluída em 2026-07-07  
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

### T-05 — `tests/test_os.py`
**10 casos:** listar, criar válida, criar sem campos obrigatórios, buscar por ID, 404, PATCH status, PATCH inválido, DELETE, DELETE 404, histórico cliente  
**Depende de:** T-03

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

## Sprint 2.6 — Padronização de Validação e Parsing ✅ CONCLUÍDA (2026-07-07)

Inserida fora da sequência original T-05→T-09 (não bloqueia nem é bloqueada por elas) para
resolver duplicação de parsing/validação encontrada em `irflow_blueprints_api.py` antes de
escrever as suítes de teste T-05/T-06/T-07 sobre um contrato de erro inconsistente.

### T-12 — `irflow_validation.py`
**Arquivo:** `irflow_validation.py` (novo)
**Funções:** `parse_int`, `parse_float`, `safe_json`, `validate_positive_number` — sentinel
`None` para entrada presente-mas-inválida, distinto do `default` usado para ausente/vazia.
`require_fields` foi desenhada, implementada e removida na mesma sprint: nenhum call site do
arquivo validava dict bruto sem antes derivar/stripar a variável, tornando a substituição
insegura (edge case de string só-com-espaços).
**Depende de:** nada — independente
**Status:** Concluída. 21 testes unitários em `tests/test_validation.py`, 100% de cobertura do módulo.

---

### T-13 — Aplicar a camada em `irflow_blueprints_api.py`
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
**Depende de:** T-12
**Status:** Concluída. 21 testes de regressão novos (`tests/test_api_parsing.py`,
`tests/test_api_parsing_refactor.py`) cobrindo as 9 rotas corrigidas e as rotas de
shopping-list/MercadoPhone refatoradas. Suíte completa: 56 testes, 100% passando.
`irflow_validation.py` adicionado à medição de cobertura (`pyproject.toml`).

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
