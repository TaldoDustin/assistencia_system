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

*(Exemplo do tipo de resposta esperada, não uma resposta real: quais dores hoje resolvidas com Excel/WhatsApp/papel o sistema substitui, e para qual perfil de assistência técnica.)*

---

## Diferenciais

TODO

*(O que faz uma assistência escolher o Assistência System em vez de um concorrente. Ver `docs/FEATURE_MATRIX_TEMPLATE.md` para comparação estruturada, a preencher após pesquisa de mercado real.)*

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
