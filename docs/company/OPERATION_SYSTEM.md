# OPERATION_SYSTEM.md — Sistema de Operação da Loja

Este documento descreve como a **empresa** funciona — não o software. É o mapa do ciclo completo de uma
loja de dispositivos móveis premium, do fornecedor ao pós-venda. Cada bloco abaixo é ou:

- **✅ Fundamentado** — já existe implementado no código, ou já foi decidido em conversa registrada
  (`docs/product/features/VENDAS.md`); citado com fonte.
- **`TODO`** — processo de negócio real que este documento não pode descrever sem inventar. Não escrevo
  como funciona uma entrega por motoboy, uma troca ou uma reserva na prática de vocês porque não tenho
  essa informação — só o Product Owner tem. Preencher aqui é o próximo passo, não uma tarefa de
  engenharia.

**Última revisão:** 2026-07-10
**Regra de escrita:** mesma disciplina de `docs/company/PRODUCT_REQUIREMENTS.md` — nenhum bloco marcado
`TODO` foi preenchido por suposição.

---

## Visão Geral — Ciclo Completo

```
Fornecedor
    │
    ▼
  Compra
    │
    ▼
Entrada de Estoque
    │
    ▼
 Cadastro
    │
    ▼
 Anúncio
    │
    ▼
 Cliente
    │
    ▼
  Venda
    │
    ▼
Pagamento
    │
    ▼
 Entrega
    │
    ▼
Pós-venda
```

| Bloco | Status | Onde está detalhado |
|---|---|---|
| Fornecedor | `TODO` | — |
| Compra | 🟡 Parcial | Seção "Compra" abaixo |
| Entrada de Estoque | ✅ Fundamentado | Seção "Entrada de Estoque" abaixo |
| Cadastro | `TODO` | — |
| Anúncio | `TODO` | — |
| Cliente (chega na loja) | ✅ Fundamentado (fluxo) | Seção "Venda" abaixo |
| Venda | ✅ Fundamentado (especificado) | Seção "Venda" abaixo |
| Pagamento | 🟡 Parcial | Seção "Venda" abaixo |
| Entrega | `TODO` | — |
| Pós-venda | `TODO` | Seção "Pós-venda" abaixo |

---

## Venda

**Status: ✅ Fundamentado (especificado, não implementado)** — fluxo completo já desenhado em
`docs/product/features/VENDAS.md`, decisões tomadas em 2026-07-09.

```
Cliente entra → Atendimento → Escolhe aparelho
                                   │
                    ┌──────────────┴──────────────┐
              [aparelho novo]              [troca / dá um usado]
                    │                              │
                    │                    Avaliação do usado → Define crédito de troca
                    │                              │
                    └──────────────┬───────────────┘
                                   ▼
                   Consulta/Reserva de IMEI (expira automaticamente)
                                   ▼
                        Preço final (± desconto)
                    [desconto > limite do vendedor? → aprovação admin]
                                   ▼
                              Pagamento
                                   ▼
                    Cálculo de comissão (sobre margem)
                                   ▼
                          Emissão de garantia
                                   ▼
                              Entrega
                                   ▼
                             Pós-venda
```

Regras de negócio correspondentes: `docs/product/BUSINESS_RULES.md` BR-017 a BR-022.
Casos de erro e critérios de aceite: `VENDAS.md` seções "Casos de erro" e "Critérios de aceite".

**Pagamento — 🟡 Parcial:** decisão já tomada de que a V1 registra pagamento simples, sem caixa formal
(abertura/fechamento, sangria, suprimento) — ver bloco "Caixa" abaixo. Formas de pagamento aceitas (Pix,
cartão, dinheiro, parcelado) e como cada uma é registrada: `TODO`, não decidido ainda.

**Entrega — `TODO`:** o fluxo desenhado em `VENDAS.md` posiciona "Entrega" logo após a garantia, mas não
especifica como ela acontece (retirada na loja, motoboy, os dois). Ver bloco "Motoboy" abaixo.

---

## Compra

**Status: 🟡 Parcial** — existe hoje como rastreamento de necessidade de reposição (Lista de Compras),
não como o processo de negociar e comprar de um fornecedor.

O que já existe: um item de estoque baixo gera necessidade de reposição
(`GET /api/estoque/reposicao-sugerida`), que vira um item de `shopping_list` com workflow de status
(`PENDENTE` → outros estados → `RECEBIDO`), auditado a cada mudança (BR-015, BR-016 em
`docs/product/BUSINESS_RULES.md`).

`TODO` — não fundamentado, processo real de negócio: como a loja de fato negocia com fornecedores, prazo
de entrega esperado, condição de pagamento ao fornecedor, o que acontece se o fornecedor entrega menos
ou diferente do pedido.

---

## Entrada de Estoque

**Status: ✅ Fundamentado.**

Um item de estoque é criado com `descricao`, `valor`, `fornecedor`, `quantidade`. Toda entrada gera um
**lote** (`estoque_lotes`) com custo próprio — o consumo futuro é debitado por lote, do mais antigo
primeiro (FIFO — BR-004). Devoluções de peça (cancelamento/exclusão de OS) criam um novo lote de retorno,
nunca reincorporam silenciosamente ao lote original (BR-006). Ver `docs/engineering/DATA_DICTIONARY.md`
tabelas `estoque`/`estoque_lotes` para o detalhe campo a campo.

**Gap conhecido:** sem rastreamento por IMEI individual — ver `docs/company/BRAND_IDENTITY.md` seção 2.

---

## Garantia

**Status: 🟡 Parcial — dois processos comerciais independentes, não confundir (discovery da V1.5,
2026-07-29, `docs/product/features/VENDAS.md` "V1.5 — Garantia").**

1. **Garantia de reparo (Assistência)** — hoje ainda usa prazo fixo de 90 dias hardcoded
   (`GARANTIA_REPARO_DIAS_PADRAO`, dívida técnica conhecida); especificado para virar um cadastro
   configurável de Tipos de Garantia, atribuído manualmente por linha de reparo na conclusão da OS
   (BR-061 a BR-065). Não implementado ainda.
2. **Garantia de venda** — especificada, não implementada: cadastro de Tipos de Garantia (política
   comercial da loja, não prazo fixo por tipo de aparelho), atribuído manualmente por item na criação da
   venda (BR-055 a BR-060).

Cobre qualquer defeito eletrônico, exclui dano físico/água (decisão de negócio confirmada). Sem vínculo
formal entre uma OS aberta por defeito coberto por garantia de venda e a venda original — decisão de
cobrar fica manual/informal (BR-066). Processo de acionamento pelo cliente continua não fundamentado além
disso — fora do escopo da V1.5.

---

## Troca

**Status: 🟡 Parcial (especificado, não implementado)** — ver `VENDAS.md` "Fluxo completo": cliente que
dá um aparelho usado passa por avaliação técnica (checklist + tabela de referência por modelo) antes de
definir o crédito de troca aplicado na venda do aparelho novo/seminovo.

`TODO` — não fundamentado: critérios exatos do checklist de avaliação (`VENDAS.md` já registra como
decisão pendente, candidato a spec próprio `AVALIACAO_USADO.md`); tabela de referência de valor por
modelo/estado de conservação; o que acontece com o aparelho usado recebido depois (vira item de estoque
para revenda? Vira sucata? Não decidido).

---

## Reserva

**Status: ✅ Fundamentado (especificado, não implementado)** — reserva de IMEI com expiração automática,
para evitar venda duplicada do mesmo aparelho sem travar estoque indefinidamente por atendimento
abandonado (BR-017). Comportamento de erro já definido: se a reserva expira com venda em andamento, o
vendedor é avisado antes de perder a reserva; se expirar, o aparelho volta a ficar disponível
(`VENDAS.md` "Casos de erro").

`TODO` — não fundamentado: valor exato do timeout de reserva em minutos (`VENDAS.md` já registra como
decisão pendente do Product Owner).

---

## Assistência

**Status: ✅ Fundamentado** — este é o domínio mais maduro do sistema hoje. Ciclo completo de Ordem de
Serviço: abertura, seleção de reparo(s), consumo de peça do estoque, mudança de status, finalização,
cancelamento (com devolução automática de peças — BR-008, BR-009, BR-010). Ver
`docs/engineering/DOMAIN_MODEL.md` seção 1.3 e `docs/product/BUSINESS_RULES.md` BR-008 a BR-014 para o
detalhe completo.

---

## Financeiro

**Status: `TODO` — decisão explícita de adiar.** `VENDAS.md` já registra a decisão: "V1 registra
pagamento simples, sem caixa formal... Caixa formal fica para o Épico Financeiro — evita que o módulo
mais prioritário do produto dependa de construir financeiro completo primeiro." Ou seja, isto não é uma
lacuna de documentação — é uma decisão de sequenciamento já tomada. Existe hoje apenas
`custos_operacionais` (despesas simples: descrição, categoria, valor, data), sem conceito de contas a
pagar/receber ou fluxo de caixa consolidado (ver `docs/engineering/DOMAIN_MODEL.md` seção 2).

`TODO` — não fundamentado: como funciona contas a pagar/receber, fluxo de caixa, cálculo de lucro
consolidado por período — tudo isso é conteúdo de negócio real, a ser escrito pelo Product Owner quando
o Épico Financeiro for priorizado.

---

## Caixa

**Status: `TODO` — mesma decisão explícita de adiar do bloco Financeiro.** Abertura/fechamento de caixa,
sangria, suprimento, conciliação por forma de pagamento (Pix, dinheiro, cartão, parcelado) — nenhum desses
conceitos existe no código ou em spec hoje. Não fundamentado, não inventado aqui.

---

## Motoboy

**Status: `TODO` — sem nenhuma informação disponível.** Não há menção a entrega/motoboy em nenhum
documento ou decisão registrada além do nome do bloco no diagrama geral. Não sei se a Fluxoly (ou as
lojas que ela atende) faz entregas, se é terceirizado, se é só retirada em loja. Preciso desta informação
do Product Owner antes de escrever qualquer coisa aqui — inventar seria pior que deixar em branco.

---

## Pós-venda

**Status: `TODO`.** Aparece como último passo do fluxo de Venda em `VENDAS.md`, mas sem processo
definido. "Métricas de sucesso" de Vendas também está `TODO` em `VENDAS.md` (candidatas levantadas:
tempo médio de venda, número de vendas com troca, taxa de aprovação de desconto — nenhuma delas é,
estritamente, pós-venda). O que a loja faz depois da venda (contato de satisfação, garantia proativa,
reengajamento) não está descrito em nenhum lugar ainda — ver Pilar "Relacionamento" em
`docs/company/BRAND_IDENTITY.md` seção 2 (CRM de reengajamento, pós-venda), que é aspiração de marca, não
processo especificado.

---

## Cadastro e Anúncio

**Status: `TODO` — sem nenhuma informação disponível**, além de "Instagram para geração de clientes"
citado na Persona Primária (`docs/company/PRODUCT_REQUIREMENTS.md`) como canal usado hoje, fora do
sistema. Não sei como a loja decide o que fotografar, que informação incluir num anúncio, ou se isso é
algo que a Fluxoly deveria assumir como feature própria ou continuar sendo trabalho manual em outra
ferramenta (Instagram). Decisão de escopo, não de implementação.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — fonte principal do bloco Venda/Troca/Reserva/Garantia de venda
- `docs/product/BUSINESS_RULES.md` — regras citadas em cada bloco
- `docs/engineering/DOMAIN_MODEL.md` — o que já existe implementado, por domínio
- `docs/engineering/DATA_DICTIONARY.md` — campos e governança de dados dos blocos já fundamentados
- `docs/company/PRODUCT_REQUIREMENTS.md` — Persona Primária, fonte de "Cadastro"/"Anúncio" (Instagram)
- `docs/company/BRAND_IDENTITY.md` — pilares que ainda não têm processo especificado (Relacionamento, Financeiro)
