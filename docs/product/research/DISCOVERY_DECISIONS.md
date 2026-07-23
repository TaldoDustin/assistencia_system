# DISCOVERY_DECISIONS.md — Decisões do Discuss-Phase

**Tipo de documento:** registro de raciocínio, não especificação final. Guarda o **porquê** de uma
decisão no momento em que ela foi tomada — a decisão em si, quando madura, é formalizada em
`docs/product/features/*.md` (fluxo de negócio) ou em uma ADR (`docs/engineering/adr/`, se for decisão
arquitetural). Este documento não substitui nenhum dos dois; existe para que o raciocínio e as
alternativas descartadas não se percam.

**Status:** vazio — nenhuma sessão de discuss-phase ainda ocorreu para o Épico Vendas.

---

## Como preencher

Uma entrada por decisão, em ordem cronológica (mais recente no topo):

```
## AAAA-MM-DD — <título curto da decisão>

**Pergunta original:** (referência a `VENDAS_QUESTIONS.md`, se aplicável)

**Decisão:** o que foi decidido, em uma frase.

**Motivo:** por que essa opção, não as outras.

**Alternativas consideradas:** lista curta, com o porquê de cada uma ter sido descartada.

**Formalizado em:** onde a decisão final foi registrada (`VENDAS.md` seção X, ou ADR-00N) — preencher
depois que a formalização acontecer, não no mesmo dia se ainda estiver em rascunho.
```

---

## Documentos relacionados

- `docs/product/research/VENDAS_QUESTIONS.md` — perguntas que originam essas decisões
- `docs/product/features/VENDAS.md` — onde decisões maduras são formalizadas
- `docs/engineering/ARCHITECTURE_DECISIONS.md` — índice de ADRs, para decisões arquiteturais
