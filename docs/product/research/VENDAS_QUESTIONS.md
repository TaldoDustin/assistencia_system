# VENDAS_QUESTIONS.md — Perguntas em Aberto do Épico Vendas

**Tipo de documento:** lista de perguntas para o discuss-phase, não especificação. Nenhuma resposta aqui
é definitiva — respostas fechadas moram em `docs/product/features/VENDAS.md`.

**Como usar:** no dia do discuss-phase do Épico Vendas, percorrer a coluna "Status" pergunta por pergunta.
As marcadas "✅ Já respondida" só precisam de confirmação (ainda valem?); as marcadas "🟡 Aberta" são o
trabalho real da reunião.

Antes de listar perguntas novas, esse documento primeiro cruzou a lista bruta de 2026-07-22 contra o que
`VENDAS.md` já decidiu em 09/jul — várias perguntas já têm resposta de política, só falta o número exato
(esse número exato continua sendo decisão do PO, listada em `VENDAS.md` seção "O que ainda está em
aberto").

---

## Cliente

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Cliente é obrigatório na venda? | ✅ Já respondida | Schema proposto (`VENDAS.md`) tem `cliente_id INTEGER NOT NULL` — sim, obrigatório |
| Pode vender para consumidor sem cadastro? | 🟡 Aberta | O schema sugere que não (FK obrigatória), mas essa consequência nunca foi discutida como decisão de negócio explícita — vale confirmar no discuss-phase se é intencional |

## Reserva / IMEI

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Reserva de IMEI tem validade/expira? | ✅ Já respondida | Sim, expiração automática (`VENDAS.md`, "Decisões já tomadas") |
| Qual o valor exato do timeout? | 🟡 Aberta (PO) | Já listado em `VENDAS.md` "O que ainda está em aberto" |
| Pode vender aparelho sem unidade serializada/IMEI (ex.: acessório avulso)? | 🟡 Aberta | Não coberto em `VENDAS.md` — o fluxo hoje assume "aparelho" como unidade serializada |
| Quando exatamente o estoque é baixado (na reserva ou na confirmação do pagamento)? | 🟡 Aberta | Tecnicamente relevante: toca a máquina de estados de `unidades_serializadas` (`disponivel→reservado→vendido`) — ver `VENDAS_GAP_ANALYSIS.md` |

## Desconto / Aprovação

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Existe limite de desconto por vendedor? | ✅ Já respondida | Sim — acima do limite exige aprovação do `admin` |
| Qual o valor exato do limite? | 🟡 Aberta (PO) | Já listado em `VENDAS.md` "O que ainda está em aberto" |
| Existe fluxo de aprovação? | ✅ Já respondida | Sim — venda fica "aguardando_aprovacao" até admin decidir (ver "Casos de erro") |

## Pagamento / Caixa / Financeiro

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Venda gera caixa formal (abertura/fechamento, sangria, suprimento)? | ✅ Já respondida | Não no V1 — registro de pagamento simples; caixa formal fica para o Épico Financeiro |
| Venda gera nota fiscal? | 🟡 Aberta | Não coberto em `VENDAS.md` — Fiscal não é módulo hoje na Fluxoly |
| Venda "conversa" com o Épico Financeiro de alguma forma no V1? | 🟡 Aberta | `VENDAS.md` só diz que caixa formal fica para depois; não especifica se o registro simples de pagamento é consumido por algo financeiro futuro |

## Comissão

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Venda gera comissão? | ✅ Já respondida | Sim, sempre sobre margem (venda − custo), nunca sobre valor bruto |
| Qual o percentual exato? | 🟡 Aberta (PO) | Já listado em `VENDAS.md` "O que ainda está em aberto" |

## Troca / Usado

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Pode trocar aparelho (usado como parte do pagamento)? | ✅ Já respondida | Sim — avaliação de usado como sub-etapa do mesmo fluxo, não módulo à parte |
| Como funciona a entrada do usado? | ✅ Já respondida (nível de política) | Checklist técnico + tabela de referência por modelo |
| Critérios exatos do checklist / tabela de referência | 🟡 Aberta (PO) | Já listado em `VENDAS.md` "O que ainda está em aberto" — pode virar `AVALIACAO_USADO.md` próprio |

## Garantia

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Venda gera garantia? | ✅ Já respondida | Sim, prazo próprio por tipo de aparelho (não reaproveita os 90 dias hardcoded do reparo) |
| Qual o prazo exato por tipo (novo/seminovo)? | 🟡 Aberta (PO) | Já listado em `VENDAS.md` "O que ainda está em aberto" |
| Como funciona garantia + troca/RMA depois da venda? | 🟡 Aberta | Fora do fluxo descrito em `VENDAS.md` hoje — o diagrama de ciclo completo de `ADR-007` inclui `Em Garantia → Troca → Descartado`, mas nenhuma regra de negócio foi especificada ainda |

## Cancelamento / Devolução

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Pode editar venda concluída? | 🟡 Aberta | Não coberto em `VENDAS.md` |
| Como cancelar uma venda? Quem pode cancelar? | 🟡 Aberta | Não coberto — `vendas.status` proposto inclui `'cancelada'`, mas a regra de quem/quando não foi escrita |
| Devolução gera volta de estoque (unidade volta a `disponivel`)? | 🟡 Aberta | Não coberto — depende da transição inversa em `unidades_serializadas`, também não implementada hoje |

## Funcionalidades periféricas (fora de escopo até decisão em contrário)

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Como registrar acessórios na venda? | 🟡 Aberta | Não coberto — acessórios provavelmente não são unidades serializadas individuais |
| Como registrar seguro do aparelho? | 🟡 Aberta | Não coberto; sinalizado no benchmark geral (2026-07-22) como funcionalidade periférica de concorrente, candidata a "não implementar agora" |
| Como funciona "upgrade" (troca de aparelho por um cliente já existente)? | 🟡 Aberta | Não mencionado em `VENDAS.md` hoje; observado como bem avaliado no benchmark geral do concorrente — mas nenhuma evidência própria da Fluxoly ainda |

## Auditoria

| Pergunta | Status | Resposta / nota |
|---|---|---|
| Existe auditoria da venda (quem criou, quem aprovou, mudanças de status)? | 🟡 Recomendada, não fechada | `VENDAS_GAP_ANALYSIS.md` recomenda reutilizar `irflow_audit.py` (mesmo padrão de `unidades_serializadas`), mas isso não está registrado como decisão em `VENDAS.md` ainda |

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — decisões já fechadas (fonte de verdade)
- `docs/product/features/VENDAS_GAP_ANALYSIS.md` — consistência entre `VENDAS.md` e o código atual
- `docs/product/research/BENCHMARKS/MERCADO_PHONE.md` — benchmark de concorrente (pendente de walkthrough do módulo Vendas)
- `docs/product/research/VENDAS_DORES_REAIS.md` — dores reais da operação, independente de concorrente
