# PRODUCT_REQUIREMENTS.md — Requisitos de Produto

**Status:** Parcialmente preenchido a partir de `docs/company/BRAND_IDENTITY.md` V1.0 (Mercado-alvo,
O que NÃO faz, Diferenciais, parte de Problemas Resolvidos). Persona, Quem Decide a Compra e Modelo de
Monetização permanecem `TODO` — o documento de marca não os responde.
**Última revisão:** 2026-07-10

---

Este documento é deliberadamente um formulário, não um documento pronto. As seções ainda marcadas `TODO`
não foram preenchidas com suposição de mercado, posicionamento ou estratégia comercial — essas decisões
pertencem ao Product Owner, não à engenharia. As seções já preenchidas citam a fonte explicitamente.

**Regra:** enquanto uma seção estiver marcada `TODO`, nenhuma decisão de arquitetura ou escopo de sprint
deve assumir uma resposta implícita para ela. Ver `docs/engineering/adr/ADR-005.md` para um exemplo concreto de
decisão técnica bloqueada por informação que só existe aqui.

---

## Público-alvo

### Persona Primária

TODO

### Persona Secundária

TODO

---

## Problemas Resolvidos

Elimina a dependência de controles paralelos (planilhas, anotações manuais, blocos de notas, conversas
dispersas) que hoje obrigam o lojista a consultar múltiplos sistemas para entender o próprio negócio.
*(Fonte: `BRAND_IDENTITY.md` seção 1.)*

Ainda `TODO` — não respondido pelo documento de marca, requer input direto do Product Owner:
- Quanto o cliente economiza (tempo, dinheiro, retrabalho), em termos concretos e mensuráveis?
- Como o cliente trabalha hoje sem o sistema, especificamente? (Excel, WhatsApp, papel, outro ERP —
  qual combinação é mais comum na persona real, ainda não definida abaixo)

---

## Diferenciais

Os seis pilares macrossistêmicos (Vendas, Operação, Financeiro, Relacionamento, Serviços, Inteligência —
`BRAND_IDENTITY.md` seção 2) tratados como um ecossistema único e verticalizado, não como módulos
avulsos — e o escopo negativo explícito da seção 4 (nunca genérico, nunca inflado, nunca difícil de
aprender) como critério de diferenciação frente a ERPs horizontais.

Ainda `TODO`:
- Qual é a principal objeção que um cliente em potencial levanta antes de comprar? (não coberto pelo
  documento de marca — é uma pergunta de venda real, não de posicionamento)

Ver `docs/product/FEATURE_MATRIX_TEMPLATE.md` para comparação estruturada com concorrentes nomeados
(Mercado Phone, Nextsi, SisAssist), a preencher após pesquisa de mercado real.

---

## Quem Decide a Compra

TODO

*(Dono da assistência, gerente, técnico influenciador — quem efetivamente assina o cartão/PIX da assinatura, e se é a mesma pessoa que vai usar o sistema no dia a dia.)*

---

## O que NÃO faz

- Não é um ERP genérico ou horizontal — não atende varejo geral, alimentar ou indústria.
- Não adiciona módulos sem propósito claro e dor real de gestão comprovada.
- Não exige treinamento exaustivo ou burocrático para operar.
- Não obriga o cliente a distorcer sua operação para caber no sistema.

*(Fonte: `BRAND_IDENTITY.md` seção 4 — Princípios Inegociáveis.)*

---

## Modelo de Monetização

TODO

*(Assinatura mensal, por usuário, por empresa, por volume de OS, etc. Afeta diretamente decisões técnicas como a de multiempresa — ver ADR-005.)*

---

## Mercado-alvo

Lojas especializadas em dispositivos móveis premium. *(Fonte: `BRAND_IDENTITY.md` seções 1 e 3.)*

Ainda `TODO` — o documento de marca define o segmento, mas não o tamanho/volume operacional:
- Tamanho de assistência técnica dentro desse segmento — pequena, média, rede — e volume esperado de
  clientes simultâneos. Ver `docs/engineering/adr/ADR-005.md`: esta informação continua sendo
  pré-requisito para a decisão de estratégia de multiempresa, que o recorte de mercado (premium) por si
  só não resolve.

---

## Documentos relacionados

- `docs/company/BRAND_IDENTITY.md` — fonte de Mercado-alvo, O que NÃO faz e Diferenciais acima
- `docs/company/VISION.md` — missão e visão de longo prazo do produto
- `docs/product/FEATURE_MATRIX_TEMPLATE.md` — comparação estruturada com concorrentes (a preencher)
- `docs/engineering/adr/ADR-005.md` — decisão bloqueada por "Quem Decide a Compra" e "Modelo de Monetização" acima
- `docs/engineering/DOMAIN_MODEL.md` — domínios existentes no código, para contraste com o que este documento descrever como necessário
