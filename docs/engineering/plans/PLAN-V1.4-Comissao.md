# PLAN-V1.4-Comissao — Comissão (+ Reversão do modelo de aprovação de desconto da V1.3)

**Data:** 2026-07-29
**Feature:** `docs/product/features/VENDAS.md` — "Revisão do modelo de desconto (2026-07-29)" e "V1.4 — Comissão"; `docs/product/BUSINESS_RULES.md` BR-044 a BR-054
**Status:** Aprovado pelo CTO (2026-07-29, com 5 ajustes incorporados na revisão)

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Nota de organização:** a discovery cobriu duas decisões de negócio distintas na mesma sessão — a
reversão do bloqueio preventivo de desconto (V1.3) e a nova feature de Comissão (V1.4). Este plano trata
as duas juntas porque são implementadas na mesma leva de trabalho (a reversão precisa acontecer antes da
UI de comissão fazer sentido), mas cada parte é claramente delimitada abaixo e vira commits separados
(regra de "um commit por intenção").

**Estado**

- [x] Discovery — aprovada (BR-044 a BR-054, `docs/product/BUSINESS_RULES.md`, incluindo a revisão de
      BR-037/BR-038)
- [x] Plano Técnico — aprovado (2026-07-29)
- [x] Implementação — commits 1 a 6 (`3b74fb4`, `b4284a7`, `4df6b94`, `bafbc53`, `b9a7290`, `d1029f6`)
- [x] Testes — commit 7 (`116e805`), 625/625 passando
- [ ] QA Manual
- [ ] Encerramento

---

## Objetivo

**Parte A (reversão):** remover o bloqueio preventivo de desconto da V1.3 (BR-037/BR-038, revogadas) —
todo desconto passa a ser sempre permitido e sempre registrado, sem exigir aprovação nem respeitar um
limite. **Parte B (V1.4):** implementar atribuição manual de comissão por item de venda, restrita a
`admin`/novo perfil `financeiro`, nunca calculada por fórmula automática (BR-044 a BR-052). Este documento
responde só "como implementar" — nenhuma regra de negócio nova é decidida aqui.

---

## Escopo

**Parte A:**
- Remover a validação de limite/aprovação em `iniciar_venda` e toda a UI correspondente.
- Parar de ler/gravar `usuarios.limite_desconto_livre` e `vendas_itens.desconto_aprovado_em` em qualquer
  fluxo. **Colunas marcadas explicitamente como deprecadas** (comentário no schema + nota aqui): permanecem
  no banco apenas por compatibilidade histórica com vendas já feitas na V1.3, não participam mais de
  nenhuma lógica do sistema — não devem ser reaproveitadas para outra finalidade no futuro.

**Parte B:**
- Novo valor de perfil `financeiro` (`PERFIS_OPCOES`).
- `vendas_itens.comissao_valor` — atribuição manual, editável, com auditoria.
- Ocultar `comissao_valor` da resposta da API para qualquer perfil que não seja `admin`/`financeiro`.
- Zerar comissão automaticamente no cancelamento da venda (com evento de auditoria).

## Fora de Escopo

- Painel de indicadores de desconto (ranking, médias, vendas fora do padrão) — sprint própria (V1.4.1/V1.5).
- Qualquer fórmula automática de cálculo de comissão (percentual, por categoria, metas) — comissão é
  sempre valor manual.
- Módulo Financeiro completo (caixa, contas a pagar/receber, metas) — `financeiro` nesta sprint só ganha
  o que já está descrito no Escopo acima.
- Modelo de autorização por módulos (checkboxes) — registrado como `TD-14`, ADR própria futura.
- Remoção física das colunas `limite_desconto_livre`/`desconto_aprovado_em` — permanecem no schema (BR-054).
- Ajuste Comercial (BR-043) continuar exclusivo do `admin` — `financeiro` não ganha esse direito (BR-052),
  nenhuma mudança nessa rota.

---

## Impacto no Banco

**Parte A — nenhuma migração de schema.** Só código para de usar as colunas já existentes; nenhum
`ALTER TABLE` necessário.

**Parte B — uma coluna nova, aditiva:**

**`vendas_itens.comissao_valor` (REAL, nullable):**
Valor de comissão atribuído manualmente por `admin`/`financeiro`, em R$. `NULL` = "ainda não atribuída" —
mesma semântica de `NULL` já estabelecida no projeto (nunca confundir "não atribuída" com "atribuída como
zero"). Não existe um campo de "tipo" (fixo vs. percentual, BR-048): o valor final em R$ é sempre o que é
gravado, independentemente de como `financeiro` chegou nele mentalmente (percentual calculado à mão, valor
fixo, etc.) — isso é o que permite a mesma estrutura suportar qualquer política de comissão da loja sem
o sistema precisar modelar "tipo de comissão" como conceito.

**Auditoria (BR-049) não precisa de tabela nova.** Reaproveita `audit_log`
(`entidade='venda_item'`, `acao='comissao_alterada'`, `valor_anterior`/`valor_novo` como JSON) — mesmo
padrão do Ajuste Comercial (BR-043). Cobre os três casos (atribuição inicial, edição, zerado por
cancelamento) com o mesmo `acao`, diferenciados pelo conteúdo do JSON.

---

## Impacto no Backend

### Parte A — Reversão do bloqueio de desconto

- `irflow_core.py::PERFIS_OPCOES` — inalterado nesta parte.
- `fluxoly_vendas_service.py::iniciar_venda` — remove inteiramente o bloco de cálculo de
  `limite_efetivo`/checagem de `desconto > limite_efetivo`/rejeição com 400. `desconto_aprovado` deixa de
  ser parâmetro da função. `motivo_desconto` continua (BR-039, inalterado).
- `fluxoly_vendas_service.py::_limite_desconto_livre` — removida (código morto após a reversão).
- `fluxoly_vendas_repository.py::inserir_item` — remove o parâmetro `desconto_aprovado` e a expressão SQL
  `CASE WHEN ? THEN datetime('now') ELSE NULL END`; `desconto_aprovado_em` nunca mais é escrito (fica
  sempre `NULL` para vendas novas — BR-054).
- `fluxoly_vendas_repository.py::buscar_limite_desconto_livre` — removida (código morto).
- `fluxoly_vendas_controller.py::criar_venda` — para de ler `desconto_aprovado` do body.
- `irflow_blueprints_api.py` — `listar_usuarios`/`criar_usuario`/`atualizar_usuario` param de parar de
  ler/gravar/expor `limite_desconto_livre`; `auth_login`/`auth_me` param de expor o campo na resposta
  (BR-054 — nenhum fluxo lê ou escreve a coluna a partir de agora).
- `app.py::criar_tabelas()` — os dois `ALTER TABLE` que criaram `limite_desconto_livre`/
  `desconto_aprovado_em` ganham um comentário atualizado marcando-as **DEPRECADAS (2026-07-29)**:
  mantidas só por compatibilidade histórica com vendas da V1.3, não participam de nenhuma lógica —
  substitui o comentário original que ainda descrevia o mecanismo de aprovação revogado.

### Parte B — Comissão

**Usuários (`irflow_core.py`):**
- `PERFIS_OPCOES` ganha `"financeiro"`.

**Autorização reutilizável (preparação de baixo custo para `TD-14`):**
- Nova função em `fluxoly_vendas_controller.py`: **`usuario_pode_financeiro()`** →
  `session.get("usuario_perfil") in ("admin", "financeiro")`. Nome deliberadamente mais amplo que
  "comissão" — hoje protege só os endpoints de comissão, mas é o ponto natural para proteger qualquer
  coisa do domínio Financeiro que vier depois (caixa, contas, relatórios financeiros), sem precisar
  renomear nem duplicar a função. Usada nos dois endpoints novos abaixo — se o modelo de autorização
  migrar para módulos no futuro, só essa função muda, os call sites não.

**Vendas (`fluxoly_vendas_service.py` / `_repository.py` / `_controller.py`):**

- Nova função `atribuir_comissao_item(conectar, venda_id, item_id, usuario_id, usuario_perfil, valor)`:
  só `admin`/`financeiro` (403 para outros perfis, via `usuario_pode_financeiro`); `valor` deve
  ser `>= 0`; rejeita se a venda não está `concluida` (mesmo compare-and-swap do Ajuste Comercial —
  comissão não é editável numa venda cancelada, consistente com BR-034). Registra evento em `audit_log`
  (`valor_anterior={comissao_valor: X ou null}`, `valor_novo={comissao_valor: Y}`) na mesma transação da
  escrita.
- Novo endpoint: `PATCH /api/vendas/<venda_id>/itens/<item_id>/comissao` (atribuir/editar, mesmo endpoint
  para os dois casos — BR-049).
- Novo endpoint de leitura: `GET /api/vendas/<venda_id>/itens/<item_id>/historico-comissao` — **restrito a
  `admin`/`financeiro`** (diferente de `historico-desconto`, que é aberto a qualquer autenticado — aqui a
  restrição de leitura é a própria BR-047: vendedor não vê nada de comissão). **Confirmado endpoint
  dedicado, não embutido na resposta de `GET /api/vendas/<id>`:** o único consumidor nesta sprint é a
  seção "Comissão" do Detalhe (mesmo padrão de `historico-desconto`, carregado sob demanda quando a seção
  renderiza, não em toda leitura da venda) — embutir infligiria o histórico completo em toda chamada do
  Detalhe, mesmo para quem nunca abre a seção de comissão. Se uma consulta de histórico independente da
  venda (ex.: "todas as comissões alteradas este mês") virar necessidade real, isso pertence ao painel de
  indicadores (fora de escopo desta sprint), não a este endpoint.
- `cancelar_venda`: ao desativar os itens da venda (`desativar_itens_da_venda`), para cada item com
  `comissao_valor` não nulo, zera (`UPDATE vendas_itens SET comissao_valor = 0 WHERE ...`) e registra
  `audit_log` (`acao='comissao_alterada'`, `valor_anterior={comissao_valor: X}`,
  `valor_novo={comissao_valor: 0}`) na mesma transação do cancelamento (BR-051).
- `_item_para_dict` passa a incluir `comissao_valor` no dicionário retornado pelo service — a
  **ocultação** por perfil acontece no controller (ver abaixo), não no service, para o service continuar
  perfil-agnóstico.

**Ocultação de `comissao_valor` por perfil (BR-047), no controller — requisito do plano, não sugestão:**
Toda serialização de `comissao_valor` para o cliente HTTP **deve** passar por uma única função de
visibilidade — `_ocultar_comissao_se_necessario(itens)` em `fluxoly_vendas_controller.py` — nunca uma
checagem de perfil duplicada inline em cada rota. `obter_venda`/`listar_vendas` chamam essa função antes
de retornar a resposta (Detalhe e `itens_resumo` do Histórico, respectivamente). Isso existe
especificamente para que uma rota nova de leitura de venda, no futuro, não vaze `comissao_valor` por
alguém esquecer de repetir a checagem — quem adicionar uma rota nova só precisa lembrar de chamar essa
função, não reimplementar a regra.

---

## Impacto no Frontend

### Parte A — Reversão

- **`Vendas.jsx` (Nova Venda):** remove o bloco de aviso "Desconto acima do seu limite..." + checkbox
  "Confirmo que o admin aprovou este desconto" + toda a lógica de `excedeLimite`/`limiteEfetivo`. Campo
  "Motivo do desconto (opcional)" permanece (BR-039). Payload de `vendasApi.create` para de enviar
  `desconto_aprovado`.
- **`Users.jsx`:** remove o campo "Limite de desconto livre (R$)" do formulário (condicional
  `perfil === "vendedor"`) — não faz mais sentido expor um campo sem efeito nenhum.
- **`VendaDetalhe.jsx`:** o texto "Desconto aprovado em ..." só aparece se `desconto_aprovado_em` vier
  preenchido na resposta (histórico de vendas feitas *antes* da reversão) — nunca mais será preenchido
  para vendas novas, mas não apagamos fato histórico real de vendas já existentes.

### Parte B — Comissão

- **`Users.jsx`:** adiciona `"financeiro"` à lista `PERFIS`.
- **`VendaDetalhe.jsx`:** nova seção "Comissão", visível só quando `user.perfil` é `admin`/`financeiro`
  (mesmo padrão de `podeAjustar` do Ajuste Comercial) — mostra o valor atual (ou "Não atribuída"),
  formulário para atribuir/editar (só valor, sem motivo — BR-050), e histórico de alterações (via
  `historico-comissao`). Vendedor/técnico/estoque não veem a seção — nem um placeholder, ela
  simplesmente não renderiza (BR-047).
- **`client.js`:** `atribuirComissaoItem(vendaId, itemId, data)`, `historicoComissaoItem(vendaId, itemId)`.

---

## Estratégia de Migração

Parte A é puramente remoção de código — nenhuma migração de banco. Parte B é uma única
`ALTER TABLE ADD COLUMN` aditiva (`vendas_itens.comissao_valor REAL`), mesmo idioma já padronizado. Sem
janela de manutenção, sem backfill.

---

## Testes

**Parte A (reversão) — cada teste de bloqueio removido vira um teste positivo da regra atual, nunca
apagado sem substituto:**
- ✓ `test_desconto_de_qualquer_valor_e_sempre_aceito` — desconto grande (ex.: R$ 2.000 numa venda de
  R$ 3.000) é aceito sem exigir nenhum campo de aprovação (substitui
  `test_desconto_acima_do_limite_sem_aprovacao_e_rejeitado`/`test_desconto_acima_do_limite_com_aprovacao_e_aceito`)
- ✓ `test_venda_nunca_exige_aprovacao_mesmo_sem_limite_configurado` — vendedor sem `limite_desconto_livre`
  configurado (default) vende com desconto sem qualquer bloqueio (substitui
  `test_limite_nao_configurado_trata_como_zero`)
- ✓ `test_valor_do_desconto_continua_persistido` — `desconto` calculado e exposto no Detalhe/Histórico
  continua correto (`valor_tabela - valor_unitario`), dado que indicadores futuros (V1.4.1/V1.5)
  dependem dele existir
- ✓ `motivo_desconto` continua funcionando normalmente (BR-039, regressão — testes existentes mantidos)
- ✓ `POST`/`PUT /api/usuarios` ignoram silenciosamente um `limite_desconto_livre` enviado no payload —
  nunca mais persistido (substitui os testes que verificavam persistência)
- ✓ `GET /api/auth/me`/`POST /api/auth/login` não expõem mais `limite_desconto_livre`

**Parte B (Comissão):**
- ✓ admin atribui comissão pela primeira vez (era `NULL`) → sucesso, `audit_log` registra
  `valor_anterior=null`
- ✓ financeiro atribui/edita comissão → sucesso, mesmo comportamento que admin
- ✓ vendedor/tecnico/estoque tentam atribuir comissão → 403
- ✓ comissão editada duas vezes → `audit_log` tem dois eventos, cada um com valor anterior/novo corretos
- ✓ comissão com valor negativo → rejeitado (400)
- ✓ tentativa de atribuir comissão numa venda cancelada → rejeitado (400, mesmo padrão de estado obsoleto
  do Ajuste Comercial)
- ✓ cancelar uma venda com comissão já atribuída → comissão zerada automaticamente, evento em `audit_log`
- ✓ `GET /api/vendas/<id>` chamado por vendedor não inclui `comissao_valor` na resposta; chamado por
  admin/financeiro inclui
- ✓ `GET /api/vendas` (histórico) — mesma ocultação aplicada a `itens_resumo`
- ✓ `GET .../historico-comissao` chamado por vendedor → 403 (diferente de `historico-desconto`, que é
  aberto)
- ✓ criação de usuário com `perfil="financeiro"` — aceito, mesmo padrão dos perfis existentes

---

## Critérios de Aceite

- [ ] Todos os casos de teste acima implementados e passando
- [ ] `ruff check .` / `npm run lint` / `npm run build` sem erros novos
- [ ] Nenhuma regressão nos 613 testes existentes (menos os removidos deliberadamente pela reversão)
- [ ] QA manual (navegador real, servidor real, banco isolado): criar venda com desconto alto sem
      qualquer bloqueio → admin atribui comissão → financeiro edita comissão → vendedor não vê nada de
      comissão em lugar nenhum → cancelar venda → comissão zerada

## Riscos

| Risco | Mitigação |
|---|---|
| Remover testes de `TestDescontoEAprovacao` sem substituto, perdendo cobertura da regra atual | Cada teste de bloqueio removido tem um teste positivo equivalente listado em "Testes" acima — revisão item a item antes de apagar, nunca remoção em massa da classe |
| `comissao_valor` vazar para um perfil sem permissão por um novo endpoint futuro esquecer o filtro | Centralizar a ocultação numa função só (`_ocultar_comissao_se_necessario`), chamada nos dois pontos de leitura de item hoje — documentar a regra para quem adicionar um novo endpoint de leitura de venda no futuro |
| Comissão atribuída, depois venda cancelada, depois alguém tenta editar a comissão já zerada | `atribuir_comissao_item` já rejeita por `status != 'concluida'`, mesmo path do Ajuste Comercial |
| Auditoria incompleta (zerar comissão no cancelamento sem registrar) | Mesma transação/cursor do cancelamento, mesmo padrão de `marcar_como_vendida`/Ajuste Comercial |

## Rollback

Parte A: reverter o código (revert do PR) restaura o comportamento de bloqueio — as colunas nunca saíram
do schema, então nada precisa ser recriado. Parte B: aditiva — reverter o código é suficiente; a coluna
`comissao_valor` pode permanecer no schema sem uso se o revert acontecer, mesmo padrão já aceito no
projeto.

---

## Questões em Aberto

Nenhuma questão de **negócio** nova encontrada durante este plano. Duas decisões de implementação (não
regra de negócio) foram tomadas aqui sem precisar voltar para Discovery, por serem implicações diretas de
regras já fechadas:
- Comissão só editável em venda `concluida` (decorre de BR-034/BR-051, não é regra nova).
- `comissao_valor` sem campo "tipo" (fixo/percentual) — decorre de BR-048 (sem fórmula automática, o
  valor final é sempre o que importa).
