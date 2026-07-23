# Benchmark — Mercado Phone

**Tipo de documento:** pesquisa de produto, não especificação. Nada aqui vira requisito automaticamente —
ver `docs/product/features/` para o que de fato foi aprovado para a Fluxoly.

**Sistema analisado:** Mercado Phone (ERP vertical para lojas de dispositivos móveis)
**Versão/ambiente observado:** não registrado ainda — TODO ao iniciar o walkthrough de um módulo
**Análises realizadas:**

| Módulo | Status | Data |
|---|---|---|
| Visão geral (menus, telas principais, impressão de navegação) | Concluída — superficial, não é walkthrough de fluxo | 2026-07-22 |
| Vendas | Pendente — próximo módulo a percorrer | — |
| OS | Pendente | — |
| Financeiro | Pendente | — |
| Fiscal | Pendente | — |

---

## Critérios deste documento

Combinados em conversa (2026-07-22), valem para qualquer módulo analisado aqui:

1. **Fato antes de interpretação** — registrar exatamente o que o sistema faz antes de analisar o valor da decisão.
2. **Observação separada de recomendação** — cada achado tem um bloco "Observado" e um bloco "Análise"/"Impacto na Fluxoly" distintos, nunca misturados na mesma frase.
3. **Nenhuma decisão implícita** — qualquer conclusão que dependa de estratégia de produto vira "Decisão pendente do PO", nunca é assumida como aprovada.
4. **Contexto registrado** — versão observada, data da análise e quais fluxos foram percorridos, para permitir revisão quando o concorrente evoluir.

---

## Vendas

*Aguardando walkthrough completo do fluxo (cadastro → orçamento → PDV → histórico → estoque → garantia →
cancelamento). A visão geral de 2026-07-22 cobriu apenas menus/telas principais, não o fluxo de venda em
si — por isso as subseções abaixo estão vazias por decisão deliberada, não por esquecimento.*

### Objetivo observado
TODO

### Fluxo observado
TODO

### Campos existentes
TODO

### Regras percebidas
TODO

### Integrações
TODO

### Pontos positivos
TODO

### Pontos negativos
TODO

### Perguntas em aberto
TODO

### Impacto para Fluxoly

#### Reaproveitar
TODO

#### Adaptar
TODO

#### Não implementar
TODO

#### Decisão pendente do PO
TODO

---

## OS, Financeiro, Fiscal

Ainda não percorridos — seções a adicionar quando cada módulo for analisado em sessão própria.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — especificação de negócio da Fluxoly (fonte de verdade, não este documento)
- `docs/product/features/VENDAS_GAP_ANALYSIS.md` — consistência entre VENDAS.md e o código atual
- `docs/product/research/VENDAS_QUESTIONS.md` — perguntas em aberto para o discuss-phase do Épico Vendas
- `docs/product/research/VENDAS_DORES_REAIS.md` — dores reais observadas na operação, independente de concorrente
