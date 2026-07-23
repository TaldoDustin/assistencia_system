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

**Sobre a coluna Prioridade (adicionada em 2026-07-22):** é uma **proposta**, derivada do checklist de
MVP discutido em conversa (cadastro de venda → cliente → produto → IMEI → pagamento → status →
auditoria). Não é decisão fechada — o discuss-phase pode e deve reclassificar qualquer linha.

- 🔴 **Obrigatória** — bloqueia o MVP tal como descrito no checklist
- 🟠 **Importante** — não bloqueia o MVP, mas afeta decisão de arquitetura ou promessa de produto já feita
- 🟡 **Depois** — resolvível numa iteração seguinte sem retrabalho estrutural
- 🔵 **Futuro** — fora do MVP, candidato a nem entrar no V1

---

## Cliente

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Cliente é obrigatório na venda? | ✅ Já respondida | 🔴 Obrigatória | Schema proposto (`VENDAS.md`) tem `cliente_id INTEGER NOT NULL` — sim, obrigatório |
| Pode vender para consumidor sem cadastro? | 🟡 Aberta | 🟠 Importante | O schema sugere que não (FK obrigatória), mas essa consequência nunca foi discutida como decisão de negócio explícita — vale confirmar no discuss-phase se é intencional |

## Reserva / IMEI

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Reserva de IMEI tem validade/expira? | ✅ Já respondida | — (confirmado) | Sim, expiração automática (`VENDAS.md`, "Decisões já tomadas") |
| Qual o valor exato do timeout? | 🟡 Aberta (PO) | 🔴 Obrigatória | Sem esse número, a lógica de expiração não pode ser implementada no MVP |
| Pode vender aparelho sem unidade serializada/IMEI (ex.: acessório avulso)? | 🟡 Aberta | 🟠 Importante | Não coberto em `VENDAS.md` — o fluxo hoje assume "aparelho" como unidade serializada |
| Quando exatamente o estoque é baixado (na reserva ou na confirmação do pagamento)? | 🟡 Aberta | 🔴 Obrigatória | Bloqueia a implementação da máquina de estados (`disponivel→reservado→vendido`) — ver `VENDAS_GAP_ANALYSIS.md` |

## Desconto / Aprovação

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Existe limite de desconto por vendedor? | ✅ Já respondida | 🟡 Depois | Sim — acima do limite exige aprovação do `admin`. Não está no checklist de MVP discutido |
| Qual o valor exato do limite? | 🟡 Aberta (PO) | 🟡 Depois | Só bloqueia se desconto entrar no MVP |
| Existe fluxo de aprovação? | ✅ Já respondida | 🟡 Depois | Mesma lógica — só relevante se desconto entrar no MVP |

## Pagamento / Caixa / Financeiro

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Venda gera caixa formal (abertura/fechamento, sangria, suprimento)? | ✅ Já respondida | — (confirmado) | Não no V1; caixa formal fica para o Épico Financeiro |
| Venda gera nota fiscal? | 🟡 Aberta | 🔵 Futuro | Fiscal não é módulo hoje na Fluxoly |
| Venda "conversa" com o Épico Financeiro de alguma forma no V1? | 🟡 Aberta | 🟡 Depois | Não especificado; não bloqueia MVP de checkout |

## Comissão

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Venda gera comissão? | ✅ Já respondida | 🟡 Depois | Sim, sempre sobre margem. Não está no checklist de MVP discutido |
| Qual o percentual exato? | 🟡 Aberta (PO) | 🟡 Depois | Só bloqueia se comissão entrar no MVP |

## Troca / Usado

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Pode trocar aparelho (usado como parte do pagamento)? | ✅ Já respondida | 🟡 Depois | Sim, mas não está no checklist de MVP discutido — "trocas" foi citado explicitamente como pós-MVP |
| Como funciona a entrada do usado? | ✅ Já respondida (nível de política) | 🟡 Depois | Checklist técnico + tabela de referência por modelo |
| Critérios exatos do checklist / tabela de referência | 🟡 Aberta (PO) | 🔵 Futuro | Candidato a `AVALIACAO_USADO.md` próprio, se crescer |

## Garantia

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Venda gera garantia? | ✅ Já respondida | 🟠 Importante | Conecta o placeholder "Garantia" já existente na tela de Unidades Serializadas (`C1.3.2`) |
| Qual o prazo exato por tipo (novo/seminovo)? | 🟡 Aberta (PO) | 🟠 Importante | Bloqueia a emissão automática de garantia, mas não o checkout em si |
| Como funciona garantia + troca/RMA depois da venda? | 🟡 Aberta | 🔵 Futuro | ADR-007 inclui `Em Garantia → Troca → Descartado` no diagrama de referência, mas nenhuma regra foi especificada |

## Cancelamento / Devolução

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Pode editar venda concluída? | 🟡 Aberta | 🟡 Depois | Não coberto em `VENDAS.md` |
| Como cancelar uma venda? Quem pode cancelar? | 🟡 Aberta | 🔴 Obrigatória | Mesmo um MVP mínimo precisa de um caminho de saída antes da confirmação de pagamento |
| Devolução gera volta de estoque (unidade volta a `disponivel`)? | 🟡 Aberta | 🟡 Depois | Fluxo de pós-venda, mais complexo que o MVP de checkout |

## Funcionalidades periféricas (fora de escopo até decisão em contrário)

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Como registrar acessórios na venda? | 🟡 Aberta | 🔵 Futuro | Acessórios provavelmente não são unidades serializadas individuais |
| Como registrar seguro do aparelho? | 🟡 Aberta | 🔵 Futuro | Sinalizado no benchmark geral (2026-07-22) como funcionalidade periférica de concorrente |
| Como funciona "upgrade" (troca de aparelho por cliente já existente)? | 🟡 Aberta | 🔵 Futuro | Bem avaliado no benchmark geral do concorrente, mas nenhuma evidência própria da Fluxoly ainda |

## Auditoria

| Pergunta | Status | Prioridade | Resposta / nota |
|---|---|---|---|
| Existe auditoria da venda (quem criou, quem aprovou, mudanças de status)? | 🟡 Recomendada, não fechada | 🔴 Obrigatória | O checklist de MVP discutido lista "registrar auditoria" como etapa explícita. `VENDAS_GAP_ANALYSIS.md` recomenda reutilizar `irflow_audit.py` |

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — decisões já fechadas (fonte de verdade)
- `docs/product/features/VENDAS_GAP_ANALYSIS.md` — consistência entre `VENDAS.md` e o código atual
- `docs/product/research/BENCHMARKS/MERCADO_PHONE.md` — benchmark de concorrente (pendente de walkthrough do módulo Vendas)
- `docs/product/research/VENDAS_DORES_REAIS.md` — dores reais da operação, independente de concorrente
- `docs/product/research/DISCOVERY_DECISIONS.md` — decisões tomadas durante o discuss-phase, com raciocínio
