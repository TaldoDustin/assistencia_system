# product/research/ — Pesquisa e Descoberta de Produto

**O que é:** evidência coletada antes de decidir — benchmark de concorrente, perguntas em aberto, dores
reais da operação, decisões de discuss-phase com seu raciocínio. **O que não é:** especificação. Nada
nesta pasta vira requisito automaticamente — decisões maduras são formalizadas em
`docs/product/features/*.md` (fluxo de negócio) ou `docs/engineering/adr/` (decisão arquitetural).

Essa separação existe por decisão explícita do usuário (CTO, 2026-07-22): evita que uma observação de
pesquisa seja lida como se já fosse decisão aprovada.

---

## Critérios válidos para qualquer documento desta pasta

1. **Fato antes de interpretação** — registrar o que foi observado antes de analisar o valor da decisão.
2. **Observação separada de recomendação** — nunca misturar as duas na mesma frase.
3. **Nenhuma decisão implícita** — o que depende de estratégia de produto vira "decisão pendente do PO",
   nunca é assumido como aprovado.
4. **Contexto registrado** — data, versão/ambiente observado, quais fluxos foram percorridos.

---

## Estrutura atual

| Caminho | Conteúdo | Status |
|---|---|---|
| `BENCHMARKS/MERCADO_PHONE.md` | Benchmark de concorrente, por módulo | Seção Vendas aguardando walkthrough completo |
| `VENDAS_QUESTIONS.md` | Perguntas em aberto do Épico Vendas, com prioridade proposta | Pronto para o discuss-phase |
| `VENDAS_DORES_REAIS.md` | Dores reais da operação (não depende de concorrente) | Vazio, aguardando coleta de campo |
| `DISCOVERY_DECISIONS.md` | Decisões tomadas durante o discuss-phase, com raciocínio | Vazio, nenhuma sessão ocorreu ainda |

**Categorias cogitadas e ainda não criadas** (`INTERVIEWS/`, subpastas por concorrente além de Mercado
Phone): propositalmente não existem ainda — mesma regra do item "Fato antes de interpretação": não criar
estrutura para conteúdo que ainda não existe. Criar quando houver a primeira entrevista real ou o
primeiro benchmark de um segundo concorrente, não antes.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — especificação de negócio aprovada (fonte de verdade)
- `docs/product/FEATURE_MATRIX_TEMPLATE.md` — matriz de funcionalidades e comparação com concorrentes, consome esta pasta como fonte
- `docs/product/PRODUCT_BACKLOG.md` — fila priorizada de épicos
