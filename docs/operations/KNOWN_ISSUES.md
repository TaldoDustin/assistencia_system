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

## KI-003

Descrição:
O módulo `irflow_blueprints_api.py` possui ~130KB e concentra mais de 80 endpoints sem separação por domínio de negócio.

Impacto:
Alto. Dificulta manutenção, aumenta risco de regressão em qualquer alteração e torna o onboarding de novos colaboradores mais lento.

Status:
Aberto — aguardando Sprint 4.

Sprint prevista:
Sprint 4 — Decomposição do Módulo API e Migrations Formais.

Responsável:
—

---

## KI-004

Descrição:
O sistema de migrations do banco de dados utiliza `ALTER TABLE` com blocos `try/except` ad-hoc em `app.py`. Não há versionamento formal do schema.

Impacto:
Alto. Impossível determinar o estado exato do schema em diferentes ambientes (dev, prod) sem inspecionar o banco diretamente. Risco de divergência silenciosa.

Status:
Aberto — aguardando Sprint 4.

Sprint prevista:
Sprint 4 — Decomposição do Módulo API e Migrations Formais.

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
Aberto.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade.

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

## KI-014

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
Aberto — identificado durante a Sprint 2.6, fora do escopo desta sprint (que é
parsing/validação, não limpeza de código morto). Candidato a remoção pontual e isolada em sprint
futura ou junto da decomposição do módulo (Sprint 4).

Sprint prevista:
Não definida — candidato a Sprint 4 (Decomposição do Módulo API) ou remoção avulsa antes disso.

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

## KI-017

Descrição:
`ruff check .` falha atualmente em `main` com 20 erros (`F841` variáveis não usadas em
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

Sprint prevista:
Não definida — recomendado priorizar antes da Sprint 3, já que um lint vermelho bloqueia todo o
resto do pipeline de CI para qualquer PR.

Responsável:
—
