# Known Issues

## KI-001

Descrição:
Ausência de rate limiting na rota `POST /api/auth/login`. Qualquer agente pode realizar tentativas de login ilimitadas sem bloqueio por IP ou por usuário.

Impacto:
Alto. O endpoint está vulnerável a ataques de força bruta contra credenciais de usuários do sistema.

Status:
Aberto.

Sprint prevista:
Sprint 3 — Segurança e Observabilidade.

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
