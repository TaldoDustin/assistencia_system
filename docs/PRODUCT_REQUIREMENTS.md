# PRODUCT_REQUIREMENTS.md — Requisitos de Produto

**Status:** Formulário — a preencher pelo Product Owner.
**Última revisão:** 2026-07-08

---

Este documento é deliberadamente um formulário, não um documento pronto. Nenhuma seção abaixo foi
preenchida com suposição de mercado, posicionamento ou estratégia comercial — essas decisões pertencem
ao Product Owner, não à engenharia.

**Regra:** enquanto uma seção estiver marcada `TODO`, nenhuma decisão de arquitetura ou escopo de sprint
deve assumir uma resposta implícita para ela. Ver `docs/adr/ADR-005.md` para um exemplo concreto de
decisão técnica bloqueada por informação que só existe aqui.

---

## Público-alvo

### Persona Primária

TODO

### Persona Secundária

TODO

---

## Problemas Resolvidos

TODO

Perguntas-guia (responder objetivamente, não em abstrato):
- Qual problema principal o produto resolve?
- Quanto o cliente economiza (tempo, dinheiro, retrabalho) ao usar o sistema em vez do que usa hoje?
- Como o cliente trabalha hoje, sem o sistema? (Excel, WhatsApp, papel, outro ERP)

---

## Diferenciais

TODO

Perguntas-guia:
- Por que escolher o Assistência System em vez de um concorrente?
- Qual é a principal objeção que um cliente em potencial levanta antes de comprar?

Ver `docs/FEATURE_MATRIX_TEMPLATE.md` para comparação estruturada, a preencher após pesquisa de mercado real.

---

## Quem Decide a Compra

TODO

*(Dono da assistência, gerente, técnico influenciador — quem efetivamente assina o cartão/PIX da assinatura, e se é a mesma pessoa que vai usar o sistema no dia a dia.)*

---

## O que NÃO faz

TODO

*(Tão importante quanto o escopo incluído — evita que a engenharia trate qualquer feature adjacente como implícita.)*

---

## Modelo de Monetização

TODO

*(Assinatura mensal, por usuário, por empresa, por volume de OS, etc. Afeta diretamente decisões técnicas como a de multiempresa — ver ADR-005.)*

---

## Mercado-alvo

TODO

*(Tamanho de assistência técnica — pequena, média, rede — volume esperado de clientes simultâneos, região. Ver ADR-005: esta informação é pré-requisito para a decisão de estratégia de multiempresa.)*

---

## Documentos relacionados

- `docs/VISION.md` — missão e visão de longo prazo do produto
- `docs/FEATURE_MATRIX_TEMPLATE.md` — comparação estruturada com concorrentes (a preencher)
- `docs/adr/ADR-005.md` — decisão bloqueada por "Mercado-alvo" e "Modelo de Monetização" acima
- `docs/DOMAIN_MODEL.md` — domínios existentes no código, para contraste com o que este documento descrever como necessário
