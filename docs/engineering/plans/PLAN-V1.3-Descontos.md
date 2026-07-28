# PLAN-V1.3-Descontos — Descontos e Aprovação

**Data:** 2026-07-28
**Feature:** `docs/product/features/VENDAS.md` — "V1.3 — Descontos e Aprovação"; `docs/product/BUSINESS_RULES.md` BR-037 a BR-043
**Status:** Aprovado pelo CTO (2026-07-28, com 5 ajustes incorporados na revisão)

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — aprovada (BR-037 a BR-043, `docs/product/BUSINESS_RULES.md`)
- [x] Plano Técnico — aprovado (2026-07-28)
- [x] Implementação — schema, backend (usuários/vendas), frontend (2026-07-28)
- [x] Testes — 27 novos (612 no total), `ruff check .`/`npm run lint`/`npm run build` limpos
- [x] QA Manual — 6 cenários validados (navegador real, servidor real, banco isolado); 1 bug real
      encontrado e corrigido durante o QA (`c10fb70` — `limite_desconto_livre` ausente na resposta de
      login), 613 testes no total
- [ ] Encerramento

---

## Objetivo

Implementar descontos comerciais na venda, respeitando BR-037 a BR-043, preservando a imutabilidade da
venda (BR-034) e mantendo compatibilidade com a futura V1.4 (Comissão) e V1.5 (Garantia). Este documento
responde só "como implementar" — nenhuma regra de negócio nova é decidida aqui (Princípio da Separação de
Decisões, `ADR-010`).

---

## Escopo

- Limite de desconto livre por vendedor (BR-037).
- Validação do limite e sinalização de aprovação acima dele (BR-038).
- Motivo do desconto, opcional, na criação da venda (BR-039).
- Ajuste Comercial Autorizado — exceção controlada ao BR-034, só para `admin` (BR-043).
- Auditoria do ajuste (evento append-only, reaproveitando `audit_log`).
- Exposição dos dados de desconto no Detalhe da venda, para suportar BR-040 (recibo) quando o serviço de
  impressão existir.

## Fora de Escopo

- Comissão (V1.4) — BR-041 só exige preservar `valor_tabela`/`valor_unitario` separados, o que já é
  verdade hoje; nenhuma implementação de fórmula de comissão nesta sprint.
- Garantia (V1.5), Reserva (V1.6).
- Financeiro / caixa / estorno.
- "Preço promocional" distinto de `valor_tabela` (BR-042 explicitamente deferido a backlog).
- Serviço de documento/recibo real (hoje é placeholder de toast) — BR-040 é satisfeito nesta sprint só
  expondo os dados (`valor_tabela`, desconto, valor final) no Detalhe da venda; o documento impresso em si
  é outra sprint, já registrada no backlog (`project_fluxoly_next_phase_frontend_focus`).
- Múltiplas campanhas/promoções simultâneas.
- Mudança visual no Histórico (badge de "teve ajuste") — não pedido na discovery, fica como ideia de
  backlog, não desta sprint.

---

## Impacto no Banco

Três colunas novas, todas aditivas (`ALTER TABLE ADD COLUMN`, mesmo idioma já usado no restante do
projeto — `contextlib.suppress(sqlite3.OperationalError)`). Nenhuma tabela nova, nenhuma migração
destrutiva.

**`usuarios.limite_desconto_livre` (REAL, nullable):**
Onde vive o limite do vendedor (BR-037) — individual por usuário, não uma tabela de configuração separada
(KISS — é um único valor por usuário, não justifica uma tabela nova). A coluna em si guarda dois
significados distintos, deliberadamente não colapsados no schema: **`NULL` sempre significa "limite não
configurado"** — nunca "configurado como zero", que é um conceito diferente. É o **service** (nunca uma
query SQL com `COALESCE`) quem interpreta `NULL` como **limite efetivo de R$ 0** ao decidir se um desconto
exige aprovação — mesmo princípio fail-secure já usado em KI-024. Isso responde a pendência que a própria
discovery já delegou ao plano técnico ("Pendente para o plano técnico: comportamento quando o vendedor não
possuir limite configurado" — `VENDAS.md`/BR-037) sem misturar os dois conceitos no dado persistido, e sem
fechar a porta para um comportamento futuro diferente sem precisar de migração.

**`vendas_itens.motivo_desconto` (TEXT, nullable, default `''`):**
Motivo do desconto na criação da venda — opcional, texto livre (BR-039). Vive no item, não na venda,
porque o desconto e o `valor_tabela`/`valor_unitario` já vivem no item (consistente com o modelo atual,
que suporta múltiplos itens por venda mesmo com quantidade=1 nesta fatia).

**`vendas_itens.desconto_aprovado_em` (TEXT, nullable):**
Confirmação de que houve aprovação administrativa quando o desconto excede o limite livre do vendedor
(BR-038) — timestamp em vez de booleano: `NULL` = nunca precisou de aprovação (desconto dentro do
limite); preenchido (`datetime('now')`) = foi aprovado, e quando. Mais rico que um `0`/`1` sem custo
adicional, e continua **sem guardar qual admin aprovou** (decisão consciente de produto já registrada em
BR-038, não uma omissão desta implementação).

**Ajuste Comercial Autorizado (BR-043) não precisa de tabela nova.** Reaproveita `audit_log`
(`entidade='venda_item'`, `entidade_id=vendas_itens.id`, `acao='ajuste_desconto'`, `valor_anterior`/
`valor_novo` como JSON) — mesmo padrão já usado em `unidades_serializadas` (`status_change`). O valor
efetivo (`vendas_itens.valor_unitario`/`subtotal`, `vendas.valor_total`) é atualizado in-place, mas nunca
sem o evento de auditoria correspondente na mesma transação — a mutação nunca é silenciosa. **O ajuste é
sempre aplicado ao item da venda, nunca à venda como um todo — `vendas.valor_total` é sempre recalculado
como a soma dos `subtotal` de todos os itens ativos**, nunca escrito diretamente. Isso é o que evita
inconsistência quando uma venda futura tiver múltiplos itens (ex.: aparelho + acessório) e só um deles
sofrer ajuste.

---

## Impacto no Backend

### Usuários (`irflow_blueprints_api.py`, rotas `/api/usuarios*` já existentes)

- `POST`/`PUT /api/usuarios` passam a ler/gravar `limite_desconto_livre` (só `admin`, mesmo padrão de
  autorização já existente nessas rotas). `GET /api/usuarios` passa a expor o campo.

### Vendas (`fluxoly_vendas_service.py` / `_repository.py` / `_controller.py`)

**Validação (na criação da venda):**
- `iniciar_venda`: calcula `desconto = valor_tabela - valor_unitario` (só se `valor_tabela` existir e
  desconto > 0); resolve o limite efetivo do vendedor (`limite_desconto_livre` do usuário, `0` se `NULL` —
  ver "Impacto no Banco"); se o desconto exceder o limite, exige `desconto_aprovado=true` explícito no
  payload — rejeita com 400 caso contrário.

**Aprovação:**
- Quando aprovado, persiste `desconto_aprovado_em = datetime('now')` em `vendas_itens` (nunca `NULL` para
  descontos que exigiram aprovação); persiste `motivo_desconto` se enviado (BR-039, opcional).

**Ajuste Comercial (BR-043):**
- Nova função `ajustar_desconto_item(conectar, venda_id, item_id, usuario_id, usuario_perfil,
  valor_unitario_novo, motivo)`: só `admin` (403 para outros perfis); `motivo` obrigatório (400 se
  ausente/vazio — diferente do motivo opcional da criação); rejeita se a venda não está `concluida`
  (protege contra corrida com cancelamento — ver Riscos). **Recálculo transacional, tudo na mesma
  transação/cursor:**
  1. Atualiza `vendas_itens.valor_unitario`/`subtotal` do item ajustado.
  2. Recalcula `vendas.valor_total` como a soma dos `subtotal` de **todos** os itens ativos da venda
     (nunca apenas o delta do item ajustado — evita divergência se a venda tiver mais de um item no
     futuro).
  3. Grava evento em `audit_log` (`entidade='venda_item'`, `acao='ajuste_desconto'`,
     `valor_anterior={valor_unitario: X}`, `valor_novo={valor_unitario: Y, motivo: Z}`).
  Os três passos acontecem atomicamente — se qualquer um falhar, nenhum é persistido (mesmo padrão de
  `iniciar_venda`/`marcar_como_vendida`). Nunca a mutação sem o log, nunca o log sem a mutação.
- Novo endpoint: `PATCH /api/vendas/<venda_id>/itens/<item_id>/ajuste-desconto`.
- Novo endpoint de leitura: `GET /api/vendas/<venda_id>/itens/<item_id>/historico-desconto` (só leitura,
  mesmo padrão de `GET /api/unidades-serializadas/<id>/historico`).

### Auditoria

- Nenhuma mudança em `irflow_audit.py` — `registrar_log_auditoria(cursor, entidade, entidade_id,
  usuario_id, acao, antes, depois)` já suporta o caso de uso sem alteração de assinatura.

---

## Impacto no Frontend

Pontos tocados, sem mockup ainda:

- **Nova Venda** (`Vendas.jsx`): quando o preço editado gerar desconto acima do limite do vendedor logado,
  exibir confirmação "Desconto acima do seu limite — aprovado pelo admin?" (checkbox) + campo opcional
  "Motivo do desconto" antes de habilitar "Confirmar Venda". Precisa expor `limite_desconto_livre` do
  vendedor logado (via `GET /api/auth/me` ou endpoint equivalente).
- **Detalhe da venda** (`VendaDetalhe.jsx`): exibir motivo do desconto (se houver) e se foi aprovado;
  bloco "Ajuste Comercial" visível só para `admin` — formulário com novo valor + motivo obrigatório — e
  histórico de ajustes já feitos (lido do novo endpoint de leitura).
- **`client.js`**: novas chamadas (`ajustarDescontoItem`, `historicoDescontoItem`).
- **Histórico** (`Vendas.jsx`, aba Histórico): sem mudança nesta sprint (fora de escopo, ver acima).

---

## Estratégia de Migração

Puramente aditiva — três `ALTER TABLE ADD COLUMN`, todas com `DEFAULT` seguro (`NULL`, `''`, `0`),
seguindo o idioma já padronizado em `criar_tabelas()`. Sem janela de manutenção, sem backfill necessário
(linhas existentes recebem o default automaticamente), sem impacto em dado já gravado.

---

## Testes

Cada BR vira uma lista objetiva de casos:

**BR-037 (limite):**
- ✓ limite não configurado (`NULL` em `usuarios.limite_desconto_livre`) → service trata como limite
  efetivo R$ 0, coluna continua `NULL` (nunca escrita como `0` pelo sistema)
- ✓ desconto zero (sem desconto) → sempre permitido, nunca exige aprovação
- ✓ desconto abaixo do limite → permitido sem aprovação, `desconto_aprovado_em` permanece `NULL`
- ✓ desconto exatamente no limite → permitido sem aprovação (limite é inclusive)
- ✓ desconto acima do limite, sem `desconto_aprovado=true` no payload → rejeitado (400)

**BR-038 (aprovação):**
- ✓ desconto acima do limite, com `desconto_aprovado=true` → aceito, `desconto_aprovado_em` gravado com
  timestamp
- ✓ nenhum campo grava identidade do admin aprovador (confirma BR-038 por ausência)

**BR-039 (motivo):**
- ✓ venda sem `motivo_desconto` → aceita normalmente (campo opcional)
- ✓ venda com `motivo_desconto` → persistido e exposto no Detalhe

**BR-043 (ajuste comercial):**
- ✓ admin ajusta desconto de venda concluída → sucesso, `audit_log` registra valor anterior/novo/quem/quando/motivo
- ✓ vendedor tenta ajustar → 403
- ✓ ajuste sem motivo → rejeitado (400, motivo obrigatório neste caso — diferente de BR-039)
- ✓ ajuste em venda cancelada → rejeitado (protege contra a corrida do risco abaixo)
- ✓ **estado obsoleto:** admin abre o Ajuste Comercial de uma venda concluída; antes de confirmar, o
  vendedor cancela a mesma venda; ao confirmar, o `PATCH` deve falhar (revalida `status='concluida'` no
  momento da escrita, não confia no estado lido quando a tela foi aberta)
- ✓ ajuste não altera cliente/IMEI/forma de pagamento/vendedor/data/status/outros itens (regressão)
- ✓ `vendas.valor_total` recalculado como soma dos `subtotal` de todos os itens ativos após o ajuste
  (não só o delta do item ajustado)

---

## Critérios de Aceite

- [ ] Todos os casos de teste acima implementados e passando
- [ ] `ruff check .` / `npm run lint` / `npm run build` sem erros novos
- [ ] Nenhuma regressão nos 592 testes existentes
- [ ] QA manual (navegador real, servidor real, banco isolado) do fluxo completo: venda com desconto
      dentro do limite → venda com desconto acima do limite (aprovado) → ajuste comercial pelo admin →
      histórico do ajuste visível

## Riscos

| Risco | Mitigação |
|---|---|
| Corrida entre ajuste comercial e cancelamento da venda | `ajustar_desconto_item` valida `status='concluida'` antes de aplicar; rejeita se já cancelada |
| **Estado obsoleto** — admin abre a tela de Ajuste Comercial vendo a venda `concluida`, vendedor cancela nesse meio-tempo, admin confirma o ajuste sobre um estado que já não é real | A validação de `status='concluida'` acontece **no momento da escrita** (dentro da transação do `PATCH`), nunca confiando no estado que a tela carregou — mesma classe de proteção já usada em `marcar_como_vendida` (`UPDATE ... WHERE status='disponivel'`) |
| Auditoria incompleta (mutação sem log, ou vice-versa) | Mutação + `registrar_log_auditoria` na mesma transação/cursor, mesmo padrão já usado em `marcar_como_vendida` |
| Incompatibilidade futura com Comissão (V1.4) | `valor_tabela`/`valor_unitario` continuam separados e imutáveis na criação — nenhuma decisão desta sprint fecha portas para V1.4 |

*(Vendedor alterar desconto durante a "edição" não é um risco real nesta fatia — não existe edição de
venda pelo vendedor; o único caminho de mutação pós-venda é o Ajuste Comercial, restrito a `admin`.)*

## Rollback

Mudança é aditiva — reverter o código (revert do PR) é suficiente. As três colunas novas podem permanecer
no schema sem uso (nenhuma tem custo de manutenção nem quebra comportamento existente); não é necessário
`DROP COLUMN` (custoso em SQLite). Dados já gravados em `motivo_desconto`/`desconto_aprovado_em`/
`limite_desconto_livre` ficam órfãos, mas inofensivos.

---

## Questões em Aberto

Nenhuma questão de **negócio** nova encontrada durante este plano. O único ponto que poderia parecer uma
questão de negócio ("o que fazer quando o vendedor não tem limite configurado") já havia sido
explicitamente delegado ao plano técnico pela própria discovery (`VENDAS.md`/BR-037) — resolvido acima
("Impacto no Banco") como decisão de implementação (fail-secure: trata como R$ 0), não como regra de
negócio nova.
