# SALES_DECK.md — Material de Apresentação Comercial

**Status:** Primeira versão, 2026-07-17. Base para apresentação presencial, reunião remota, PDF comercial,
slide deck e site institucional — o "livro" único de onde qualquer um desses formatos é derivado, para
garantir mensagem consistente entre canais.
**Fontes:** `docs/company/BRAND_IDENTITY.md`, `docs/company/VISION.md`, `docs/company/PRODUCT_REQUIREMENTS.md`,
`docs/company/RELEASE_STRATEGY.md`, `docs/operations/PROJECT_STATUS.md`.
**Ver também:** `docs/company/DEMO_SCRIPT.md` (roteiro cronometrado de apresentação ao vivo),
`docs/company/FAQ_COMERCIAL.md` (respostas padronizadas a objeções).

Este documento responde às três perguntas que um comprador real faz nos primeiros minutos — não às
perguntas que um engenheiro faz. Nada de ADR, Sprint ou cobertura de testes aqui; isso vive em
`docs/engineering/` e `docs/operations/` para quem precisa.

1. Isso resolve meu problema?
2. É melhor que o Mercado Phone para o meu negócio?
3. Posso confiar nessa empresa?

---

## 1. Abertura

**Fluxoly**
A plataforma inteligente para lojas especializadas em dispositivos móveis premium.

---

## 2. O problema

Hoje uma loja de iPhones, Apple Watch, AirPods e acessórios premium trabalha assim
*(fonte: Persona Primária, `PRODUCT_REQUIREMENTS.md`)*:

- WhatsApp para atendimento
- Instagram para geração de clientes
- Mercado Phone como ERP principal
- Excel para controles paralelos
- Anotações em papel
- Conversas com fornecedores espalhadas

Resultado:
- Muito trabalho.
- Pouca informação.
- O dono da loja é quem mais acompanha os números — e é o que menos tempo tem pra isso.

Dores concretas que a persona já relatou: perder vendas por demora no atendimento, não saber o lucro
exato de cada venda, estoque incorreto, IMEI perdido ou difícil de localizar, funcionário vendendo
abaixo da margem, retrabalho por controles paralelos.

---

## 3. Nossa visão

A Fluxoly nasceu para unificar toda a operação — vendas, estoque, financeiro, assistência técnica e
inteligência de negócio em uma única plataforma. *(Fonte: Missão, `VISION.md`.)*

Não queremos apenas controlar.
Queremos ajudar o dono a tomar decisões.

---

## 4. Os 6 pilares

*(Fonte: `BRAND_IDENTITY.md` seção 2 — Os 6 Pilares Macrossistêmicos.)*

```
                    Fluxoly
                       │
      ┌────────┬───────┼───────┬────────┬─────────────┐
      │        │        │       │        │             │
   Vendas  Operação  Financeiro Serviços Relacionamento Inteligência
  (balcão, (estoque, (caixa,   (OS,      (CRM,          (insights,
  checkout) IMEI,    conciliação técnico) pós-venda)     dashboards,
            compras)                                     IA)
```

Cada pilar absorve novos submódulos conforme a empresa cresce — CRM, marketplaces, WhatsApp — sem sair
da mesma plataforma.

---

## 5. O que torna a Fluxoly diferente?

**Mercado Phone**
Excelente sistema. Mas atende milhares de lojas da mesma forma — um produto padronizado para o mercado
em geral.

**Fluxoly**
Cada cliente pode evoluir junto com a gente. Nos adaptamos ao processo real da empresa, não o contrário
— um dos princípios inegociáveis da marca é que o produto nunca obriga o lojista a distorcer sua
operação para caber no sistema. *(Fonte: `BRAND_IDENTITY.md` seção 4.)*

Os primeiros clientes-parceiro não compram "um sistema pronto" — eles participam da construção dos
próximos módulos, com influência direta sobre o que é priorizado.

---

## 6. Diferenciais

- Atendimento próximo, direto com quem constrói o produto
- Ritmo vivo de evolução — atualizações constantes, não trimestrais
- Interface moderna, pensada por perfil de usuário (vendedor, técnico, admin — cada um vê só o que
  precisa para trabalhar)
- Rastreamento de estoque por IMEI individual (em desenvolvimento — ver seção 8)
- Integração já ativa com Mercado Phone (sincronização de OS)
- Inteligência de negócio: dashboards com dado real, recomendações de decisão (Fluxoly Insights)

---

## 7. Demonstração

Roteiro completo cronometrado em `docs/company/DEMO_SCRIPT.md`. Sequência de telas:

Dashboard → Clientes → Assistência (Ordens de Serviço + Kanban) → Vendas (preview) → Financeiro
(preview) → Fluxoly Insights (preview)

---

## 8. Roadmap — o que já existe vs. o que está vindo

Não escondemos o que ainda não está pronto — mostramos, com honestidade, o que é real e o que é visão.
*(Fonte: `docs/operations/PROJECT_STATUS.md`, `docs/operations/ROADMAP.md`, estado do código em 2026-07-17.)*

**✅ Em produção hoje, uso real:**
- Assistência Técnica (Ordens de Serviço, Kanban, Garantias)
- Estoque e Lista de Compras
- Clientes (cadastro, busca, histórico)
- Tabela de Preços, Custos Operacionais, Relatórios, Backup
- Integração com Mercado Phone (importação automática de OS)

**🟡 Em prévia comercial — já visível na demonstração, funcionalidade real em construção:**
- Vendas (fluxo de balcão)
- Financeiro (fluxo de caixa, contas a pagar/receber)
- Fluxoly Insights (recomendações de negócio)

**⚪ Na visão de longo prazo, ainda não iniciado:**
- CRM / Relacionamento (pós-venda, reengajamento, canais de mensageria)
- Inteligência artificial aplicada (motor preditivo real — hoje Insights é uma prévia visual do que
  essa camada vai entregar)
- Rastreamento de estoque por IMEI individual (schema e domínio de dados iniciados, sem tela ainda)

Isso não é uma fraqueza a esconder — é o que dá aos primeiros clientes-parceiro poder real de moldar
o produto.

---

## 9. Modelo comercial

Implementação → Treinamento → Mensalidade → Suporte → Evolução contínua

**Nota:** estrutura exata de precificação (por usuário, por loja, por volume) ainda não está fechada —
ver `docs/company/PRODUCT_REQUIREMENTS.md` seção "Modelo de Monetização". O que já está confirmado é o
modelo de assinatura mensal recorrente com suporte contínuo. Valores e condições comerciais são
definidos caso a caso com o Product Owner até essa estrutura ser formalizada.

---

## 10. Encerramento

Fluxoly não é apenas um sistema.
É uma plataforma construída para crescer junto com sua empresa.
