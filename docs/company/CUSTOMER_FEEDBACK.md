# CUSTOMER_FEEDBACK.md — Log de Feedback de Clientes

**Que decisão este documento ajuda a tomar:** o que entra no backlog funcional (`PRODUCT_BACKLOG.md`) e
em qual ordem, com base em pedido real de cliente — não em opinião interna. Depois de algumas reuniões
registradas aqui, este documento vira a evidência que qualquer priorização de sprint deve citar.

**Status:** Ativo a partir de 2026-07-20, decisão do usuário (Product Owner/CTO) — feedback de cliente
passa a valer mais que documentação interna na priorização do que entra em cada sprint.

**Última revisão:** 2026-07-20

---

## Por que este documento existe

A Fluxoly foi aprovada na primeira reunião comercial. A partir de agora, cada reunião com um cliente
(fechado ou em negociação) segue o mesmo pipeline, sem exceção:

```
Cliente → Pedido → Discussão → Decisão → Sprint
```

- **Cliente** — quem pediu, e em que contexto (loja, segmento, quantos módulos já usa).
- **Pedido** — o que o cliente pediu, na linguagem dele, sem já traduzir para termo técnico.
- **Discussão** — o que foi avaliado: é uma dor real ou um caso isolado? Encaixa em algum épico já
  planejado (`PRODUCT_BACKLOG.md`, `RELEASE_STRATEGY.md`) ou é novo?
- **Decisão** — entra em sprint agora, entra no backlog para depois, ou não entra (com o motivo).
- **Sprint** — se entrou, qual sprint/épico veio a resolver, para fechar o ciclo depois.

**Regra de escrita:** toda reunião gera uma entrada, mesmo que a decisão seja "não entra agora". Um
pedido rejeitado sem registro se perde e volta a ser perguntado depois sem contexto. Nenhuma entrada é
apagada — se uma decisão mudar depois, registra-se uma nova entrada linkando à anterior (mesmo padrão de
`DECISION_LOG.md`).

**Meta declarada (usuário, 2026-07-20):** depois de ~10 reuniões registradas, o roadmap de
`PRODUCT_BACKLOG.md` passa a ser majoritariamente evidência (pedidos reais, repetidos entre clientes) em
vez de suposição interna.

---

## Formato de cada entrada

```
## AAAA-MM-DD — <Nome/apelido do cliente>

**Cliente:** loja, segmento, módulos já em uso.
**Pedido:** o que foi pedido, na linguagem do cliente.
**Discussão:** dor real ou caso isolado? Já existe épico relacionado? Quantos outros clientes já
  pediram algo parecido (buscar entradas anteriores antes de registrar como "novo")?
**Decisão:** entra em sprint agora / vai para o backlog / não entra — com o motivo.
**Sprint/Épico:** vinculado, se houver (referenciar `PRODUCT_BACKLOG.md` ou a sprint específica).
**Status:** aberto / planejado / entregue / recusado.
```

---

## Entradas

*Nenhuma reunião registrada ainda. A primeira entrada deve vir da próxima reunião com um dos clientes
piloto (ver `RELEASE_STRATEGY.md` e a recomendação de fechar 2–3 clientes parceiros antes de escalar
vendas).*

---

## Documentos relacionados

- `docs/product/PRODUCT_BACKLOG.md` — fila priorizada de épicos; entradas aqui devem alimentar essa
  priorização, não substituí-la.
- `docs/company/DECISION_LOG.md` — decisões executivas já tomadas (distinto: aquele é decisão interna
  registrada, este é o pedido do cliente que gerou ou não uma decisão).
- `docs/company/RELEASE_STRATEGY.md` — para qual release/épico um pedido aceito é direcionado.
- `docs/product/features/VENDAS.md` — épico ativo mais provável de receber pedidos nas próximas reuniões.
