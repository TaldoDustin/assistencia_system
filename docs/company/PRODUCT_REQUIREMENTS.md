# PRODUCT_REQUIREMENTS.md — Requisitos de Produto

**Status:** Persona Primária (Cliente), Quem Decide a Compra e parte de Problemas Resolvidos/Diferenciais
preenchidos com input direto do Product Owner (2026-07-10). Personas Operacionais (Usuários — quem opera
a plataforma no dia a dia) reestruturadas como grupo próprio: Vendedor preenchido, Técnico/
Financeiro/Estoque/Administrador ainda `TODO`. Modelo de Monetização parcialmente respondido (assinatura
mensal confirmada, estrutura de precificação exata segue `TODO`).
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

Distinção conceitual (2026-07-10, Product Owner): **Cliente** (quem compra o sistema) é o Dono da Loja —
Persona Primária abaixo. **Usuários** (quem opera a plataforma no dia a dia) são um grupo de perfis
distintos — Vendedor, Técnico, Financeiro, Estoque, Administrador — ver seção "Personas Operacionais"
mais abaixo, não uma única "persona secundária".

### Persona Primária (Cliente) — Dono de Loja de Dispositivos Móveis Premium

*(Fonte: input direto do Product Owner, 2026-07-10 — descreve o cliente real, não um cliente idealizado.)*

**Perfil**

Empresário proprietário de uma loja especializada na venda de iPhones, Apple Watch, AirPods e acessórios
premium, podendo ou não possuir assistência técnica própria. Normalmente é responsável por diversas áreas
da empresa ao mesmo tempo: vendas, compras, estoque, financeiro, atendimento ao cliente e negociação com
fornecedores. Mesmo quando possui funcionários, continua sendo quem acompanha os indicadores do negócio e
toma as decisões estratégicas.

**Como trabalha hoje**

A operação está distribuída entre diversas ferramentas — cenário comum:

- WhatsApp para atendimento
- Instagram para geração de clientes
- Mercado Phone como ERP principal
- Excel para controles paralelos
- Anotações em papel
- Conversas com fornecedores via WhatsApp

As informações ficam espalhadas — o dono precisa consultar vários lugares para entender o que realmente
aconteceu na empresa.

**Principais dores**

- Responder WhatsApp durante o dia inteiro
- Perder vendas por demora no atendimento
- Não saber exatamente o lucro de cada venda
- Estoque incorreto
- IMEIs perdidos ou difíceis de localizar
- Funcionário vender abaixo do preço permitido
- Dificuldade para acompanhar indicadores
- Retrabalho causado por controles paralelos
- Falta de integração entre vendas, estoque e financeiro

> **Reforça um gap já registrado:** "IMEIs perdidos ou difíceis de localizar" é uma dor real da persona
> primária que confirma o gap técnico já apontado em `BRAND_IDENTITY.md` seção 2 e
> `docs/engineering/DOMAIN_MODEL.md` 1.4 — a tabela `estoque` hoje não rastreia por IMEI individual.

**Objetivos**

Vender mais; responder clientes mais rapidamente; controlar o estoque com precisão; acompanhar lucro em
tempo real; reduzir retrabalho; crescer sem aumentar a complexidade operacional.

**O que ele compra**

Produtos: iPhone novo, iPhone seminovo, Apple Watch, AirPods, acessórios Apple, carregadores, cabos,
películas, capinhas.

Serviços: assistência técnica, troca de tela, troca de bateria, manutenção geral, venda com aparelho
usado na troca.

**Critérios de compra**

Facilidade de uso; velocidade do atendimento; suporte rápido; possibilidade de personalização; preço
mensal; confiança no fornecedor; evolução constante do produto.

**Objeções mais comuns**

- "Já uso Mercado Phone."
- "Migrar vai dar trabalho."
- "Minha equipe vai conseguir aprender?"
- "Vou perder meus dados?"
- "Vale a pena pagar mensalidade?"
- "O suporte realmente responde?"

**Como a Fluxoly vence essa decisão**

Atendimento próximo ao cliente; evolução contínua baseada nas necessidades reais das lojas; possibilidade
de adaptações específicas; interface simples; módulos especializados para o mercado Apple; foco em gestão
inteligente, e não apenas registro de informações.

---

## Personas Operacionais (Usuários)

*(Fonte: input direto do Product Owner, 2026-07-10.)* Distintas do Cliente (Persona Primária, quem
**compra**): a Fluxoly é usada diariamente por diferentes profissionais dentro da loja, cada um com
objetivos, responsabilidades e dores distintas — comum em produtos SaaS B2B, onde a experiência do
usuário diário determina se o comprador culpa o sistema por atrito operacional, mesmo quando a decisão de
compra foi dele.

Isso conecta diretamente com um diferencial de produto: **interfaces diferentes por perfil**, não uma
tela única para todos. Ver princípio de UX correspondente em `docs/company/VISION.md` (Valores).

### Vendedor

**Objetivo:** Vender rapidamente e atender mais clientes.

**Responsabilidades:**
- Consultar estoque
- Reservar IMEI
- Gerar orçamento
- Finalizar venda
- Receber pagamento
- Emitir garantia

**Dores:**
- Perder tempo procurando aparelhos
- Não saber disponibilidade real
- Ter descontos bloqueados
- Cliente esperando resposta
- Digitar informações repetidas

**O que espera da Fluxoly:**
- Encontrar qualquer aparelho em segundos
- Saber exatamente onde está cada IMEI
- Fazer uma venda em menos de um minuto
- Interface extremamente simples
- Não depender de outro funcionário

### Técnico

`TODO` — perfil já existe no código hoje (`tecnico`, ver `docs/engineering/DOMAIN_MODEL.md` 1.2 Usuários),
mas a persona operacional (objetivos, responsabilidades, dores, expectativas) ainda não foi escrita pelo
Product Owner.

### Financeiro

`TODO` — perfil **não existe** no código hoje (perfis atuais: `admin`, `tecnico`, `vendedor` — ver
`docs/engineering/DOMAIN_MODEL.md` 1.2); persona operacional ainda não escrita.

### Estoque

**Atualização 2026-07-25:** o perfil `estoque` agora existe no código (`admin`/`tecnico`/`vendedor`/
`estoque` — `irflow_core.py::PERFIS_OPCOES`), criado como parte da Sprint Segurança 1.0 para restringir
mutação de itens de Estoque a `admin`/`estoque` (antes, qualquer perfil autenticado podia alterar
estoque — ver `docs/security/SECURITY_AUDIT_2026-07.md`, `docs/product/BUSINESS_RULES.md` BR-030).
`TODO` — a persona operacional completa (objetivo, responsabilidades, dores, expectativas de quem usa
esse perfil no dia a dia) ainda não foi escrita; o perfil resolve uma lacuna de segurança, não substitui
a pesquisa de produto pendente.

### Administrador

`TODO` — perfil já existe no código hoje (`admin`), mas a persona operacional ainda não foi escrita.

### Resumo — Perfil → Interface (visão de produto, não implementada)

| Perfil | Interface (foco) | Persona escrita? |
|---|---|---|
| Vendedor | Vendas, IMEI, orçamento e checkout | Sim |
| Técnico | OS, bancada e peças | `TODO` |
| Financeiro | Caixa, contas, fluxo de caixa | `TODO` |
| Estoque | Entradas, fornecedores, inventário | `TODO` |
| Administrador | Indicadores, usuários, permissões e configurações | `TODO` |

Esta tabela é visão de produto, não uma feature já implementada — hoje o sistema tem uma interface única
por perfil de sessão (`admin`/`tecnico`/`vendedor`), sem telas dedicadas por função (ver
`docs/engineering/DOMAIN_MODEL.md` 1.2 e 1.3).

---

## Problemas Resolvidos

Elimina a dependência de controles paralelos (planilhas, anotações manuais, blocos de notas, conversas
dispersas) que hoje obrigam o lojista a consultar múltiplos sistemas para entender o próprio negócio.
*(Fonte: `BRAND_IDENTITY.md` seção 1.)*

Como o cliente trabalha hoje, sem o sistema: WhatsApp para atendimento, Instagram para geração de
clientes, Mercado Phone como ERP principal, Excel para controles paralelos, anotações em papel — ver
Persona Primária acima ("Como trabalha hoje"). *(Fonte: Product Owner, 2026-07-10.)*

Ainda `TODO`:
- Quanto o cliente economiza (tempo, dinheiro, retrabalho), em termos concretos e mensuráveis? — a
  persona lista as dores (perda de vendas por demora, lucro desconhecido, retrabalho) mas não quantifica
  o ganho esperado.

---

## Diferenciais

Os seis pilares macrossistêmicos (Vendas, Operação, Financeiro, Relacionamento, Serviços, Inteligência —
`BRAND_IDENTITY.md` seção 2) tratados como um ecossistema único e verticalizado, não como módulos
avulsos — e o escopo negativo explícito da seção 4 (nunca genérico, nunca inflado, nunca difícil de
aprender) como critério de diferenciação frente a ERPs horizontais.

Objeções mais comuns antes de comprar (ver Persona Primária): "já uso Mercado Phone", "migrar vai dar
trabalho", "minha equipe vai conseguir aprender?", "vou perder meus dados?", "vale a pena pagar
mensalidade?", "o suporte realmente responde?". A Fluxoly responde com atendimento próximo, evolução
contínua guiada por necessidade real das lojas, adaptação específica, interface simples, módulos
especializados para o mercado Apple e foco em gestão inteligente (não apenas registro de dados).
*(Fonte: Product Owner, 2026-07-10.)*

Ver `docs/product/FEATURE_MATRIX_TEMPLATE.md` para comparação estruturada com concorrentes nomeados
(Mercado Phone, Nextsi, SisAssist), a preencher após pesquisa de mercado real.

---

## Quem Decide a Compra

O dono da loja (Persona Primária) — é quem acompanha os indicadores do negócio, avalia os critérios de
compra (facilidade de uso, suporte, preço mensal, confiança no fornecedor) e assina a assinatura, mesmo
quando tem funcionários. **Não é necessariamente quem vai operar o sistema no dia a dia** — ver Persona
Secundária (Vendedor) acima: é o usuário diário quem determina, na prática, se o dono continua satisfeito
com a decisão de compra ou passa a culpar o sistema por atrito operacional.
*(Fonte: Product Owner, 2026-07-10.)*

---

## O que NÃO faz

- Não é um ERP genérico ou horizontal — não atende varejo geral, alimentar ou indústria.
- Não adiciona módulos sem propósito claro e dor real de gestão comprovada.
- Não exige treinamento exaustivo ou burocrático para operar.
- Não obriga o cliente a distorcer sua operação para caber no sistema.

*(Fonte: `BRAND_IDENTITY.md` seção 4 — Princípios Inegociáveis.)*

---

## Modelo de Monetização

Assinatura mensal confirmada como modelo (a persona trata "preço mensal" como critério de compra e "vale
a pena pagar mensalidade?" como objeção comum — ambos pressupõem um modelo de assinatura recorrente).

Ainda `TODO` — estrutura exata de precificação:
- Por usuário, por loja/empresa, por volume de OS/vendas, ou plano fixo com faixas? Afeta diretamente
  decisões técnicas como a de multiempresa — ver `docs/engineering/adr/ADR-005.md`.

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
- `docs/engineering/adr/ADR-005.md` — decisão ainda bloqueada por "Mercado-alvo" (volume) e "Modelo de Monetização" (estrutura) acima; "Quem Decide a Compra" já respondido
- `docs/engineering/DOMAIN_MODEL.md` — domínios existentes no código; seção 1.4 (Estoque) confirma o gap de rastreamento por IMEI citado na Persona Primária
