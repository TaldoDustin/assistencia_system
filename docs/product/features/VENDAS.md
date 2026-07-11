# VENDAS.md — Feature Spec: Módulo de Vendas

**Status:** Rascunho — desenhado em conversa entre Product Owner e engenharia em 2026-07-09, antes de qualquer implementação.
**Épico:** Comercial (ver `docs/operations/ROADMAP.md` para o eixo de engenharia — este documento pertence ao eixo de produto, numeração própria a definir em `PRODUCT_BACKLOG.md`).
**Atualizado em 2026-07-11** (Claude, a pedido do CTO): adicionadas as seções "Modelo de dados",
"Wireframes conceituais" e "Dependências", que faltavam no rascunho original. Nenhuma decisão da seção
"Decisões já tomadas" foi alterada.

---

## Por que existe

O módulo de Vendas é a prioridade número um do produto: se ele for excepcional, estoque, financeiro,
assistência e inteligência se conectam naturalmente a partir dele. Hoje o sistema cobre o ciclo de
**reparo** (Ordens de Serviço) mas não tem nenhum conceito de **venda de aparelho** — nem novo, nem
seminovo, nem troca.

Este documento nasce de um desenho de fluxo real (não de uma lista de tabelas) — ver seção
"Fluxo completo" para o raciocínio passo a passo.

---

## Quem usa

**Provisório** — `docs/company/PRODUCT_REQUIREMENTS.md` (Persona Primária/Secundária) ainda está `TODO`. Até ser
preenchido, este spec assume os perfis já existentes no sistema (`docs/engineering/DOMAIN_MODEL.md` 1.2):

| Perfil | Papel em Vendas |
|---|---|
| `vendedor` | Conduz o atendimento e a venda, respeita limite de desconto próprio |
| `admin` | Aprova desconto acima do limite do vendedor (ver "Regras de negócio") |
| `tecnico` | Executa a avaliação técnica de aparelho usado na troca (checklist) |

Não existe hoje um perfil `gerente` — decisão explícita: **não criar agora**, reaproveitar `admin`
como aprovador (ver decisão registrada abaixo). Revisitar apenas quando houver mais de uma loja/equipe.

---

## Fluxo completo

Desenhado a partir da pergunta "como uma venda acontece em uma loja de iPhones", não de schema.

```
Cliente entra
      │
      ▼
  Atendimento
      │
      ▼
Escolhe aparelho ──────────────┐
      │                        │
   [aparelho novo]        [troca / dá um usado]
      │                        │
      │                        ▼
      │              Avaliação do usado
      │              (checklist técnico + tabela de referência)
      │                        │
      │                        ▼
      │              Define crédito de troca
      │                        │
      └───────────┬────────────┘
                   ▼
    Consulta / Reserva de IMEI
    (reserva expira automaticamente se a venda não fechar)
                   │
                   ▼
         Preço final (± desconto)
                   │
            [desconto > limite do vendedor?]
                   │
                  sim → aprovação do admin
                   │
                   ▼
               Pagamento
         (registro simples — sem caixa formal no V1)
                   │
                   ▼
        Cálculo de comissão (sobre margem)
                   │
                   ▼
          Emissão de garantia
        (prazo próprio por tipo de aparelho)
                   │
                   ▼
               Entrega
                   │
                   ▼
              Pós-venda
```

---

## Decisões já tomadas (2026-07-09)

Cada linha é uma decisão de negócio real, tomada em conversa — não suposição de engenharia.

| Decisão | Escolha | Por quê |
|---|---|---|
| Novo vs. usado/troca | Um único fluxo, avaliação de usado como sub-etapa | Mais simples de especificar e implementar primeiro; troca não é módulo à parte |
| Aprovação de desconto | `admin` aprova acima do limite do vendedor | Reaproveita perfil existente — zero mudança de schema de permissões agora |
| Reserva de IMEI | Reserva com expiração automática | Evita venda duplicada do mesmo aparelho sem travar estoque indefinidamente por atendimento abandonado |
| Base da comissão | Percentual sobre margem (venda − custo), não sobre valor bruto | Alinha incentivo do vendedor com rentabilidade real — desconto exagerado corta a comissão dele também |
| Garantia de venda | Prazo próprio por tipo de aparelho (não reaproveita os 90 dias hardcoded do reparo) | Desacopla desde o início da regra hardcoded de reparo, já registrada como dívida técnica |
| Avaliação de usado | Checklist técnico + tabela de referência por modelo | Estruturado e auditável — reduz avaliação "no olho" e disputa com cliente depois |
| Entidade Cliente | Cria tabela `clientes` própria no V1 | Pré-requisito estrutural já apontado em `DOMAIN_MODEL.md` — base para histórico e pós-venda |
| Caixa/Financeiro | V1 registra pagamento simples, sem caixa formal (abertura/fechamento, sangria, suprimento) | Caixa formal fica para o Épico Financeiro — evita que o módulo mais prioritário do produto dependa de construir financeiro completo primeiro |

---

## O que ainda está em aberto

Não decidido nesta conversa — não assumir resposta implícita para nenhum destes:

- **Quais telas cada perfil vê** (vendedor vs. admin vs. técnico) — decisão de UX, não de fluxo de negócio
- **Valor exato do timeout de reserva de IMEI** (minutos) — TODO, decisão de Product Owner
- **Percentual de comissão sobre margem** — TODO, decisão de Product Owner
- **Limite de desconto do vendedor sem aprovação** — TODO, decisão de Product Owner
- **Prazo de garantia por tipo de aparelho** (novo vs. seminovo) — TODO, decisão de Product Owner
- **Critérios exatos do checklist de avaliação de usado** e tabela de referência por modelo — TODO, provavelmente vira `docs/product/features/AVALIACAO_USADO.md` próprio se crescer
- **Modelo de dados de `clientes`** — não está mais em aberto aqui: especificado em `docs/product/features/CLIENTES.md`, incluindo os pontos de deduplicação/unicidade ainda pendentes de decisão do Product Owner

---

## Casos de erro (derivados do fluxo acima)

| Cenário | Comportamento esperado |
|---|---|
| IMEI reservado por outro atendimento em andamento | Bloquear seleção, mostrar até quando a reserva do outro atendimento expira |
| Reserva de IMEI expira com venda em andamento | Vendedor é avisado antes de perder a reserva; se expirar, aparelho volta a ficar disponível e a venda não pode prosseguir sem nova reserva |
| Desconto acima do limite e nenhum admin disponível para aprovar | Venda fica bloqueada em "aguardando aprovação" — não implementar bypass |
| Avaliação de usado recusada pelo cliente (valor de troca não aceito) | Cliente pode prosseguir com venda sem troca (paga valor cheio) ou cancelar o atendimento |
| Aparelho escolhido sem estoque disponível no momento da confirmação | Erro explícito antes do pagamento, nunca depois |

---

## Modelo de dados (proposto)

Depende de `docs/product/features/CLIENTES.md` (`clientes`) e `docs/product/features/IMEI.md`
(`estoque_unidades`) existirem antes de fazer sentido implementar este schema.

```sql
CREATE TABLE vendas (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id                  INTEGER NOT NULL,   -- FK lógica para clientes.id (CLIENTES.md)
    vendedor_id                 INTEGER NOT NULL,   -- FK lógica para usuarios.id
    estoque_unidade_id          INTEGER NOT NULL,   -- FK lógica para estoque_unidades.id (IMEI.md) — aparelho vendido
    troca_estoque_unidade_id    INTEGER,            -- unidade recebida em troca, se houver (nullable)
    valor_bruto                 REAL NOT NULL,
    desconto                    REAL NOT NULL DEFAULT 0,
    valor_final                 REAL NOT NULL,
    custo                       REAL NOT NULL,       -- snapshot do custo no momento da venda
    margem                      REAL NOT NULL,       -- valor_final - custo; calculada no service, não editável (BR-019)
    comissao_percentual         REAL,                -- TODO: valor definido pelo Product Owner
    comissao_valor               REAL,
    forma_pagamento              TEXT,
    status                       TEXT NOT NULL DEFAULT 'aguardando_pagamento',
        -- 'aguardando_aprovacao' | 'aguardando_pagamento' | 'paga' | 'cancelada'
    aprovado_por                 INTEGER,             -- FK lógica para usuarios.id (admin), nullable — BR-018
    criado_em                    TEXT NOT NULL DEFAULT (datetime('now')),
    finalizado_em                 TEXT
);
CREATE INDEX idx_vendas_cliente_id ON vendas(cliente_id);
CREATE INDEX idx_vendas_vendedor_id ON vendas(vendedor_id);
CREATE INDEX idx_vendas_status ON vendas(status);

CREATE TABLE vendas_garantias (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id      INTEGER NOT NULL,   -- FK lógica para vendas.id
    prazo_dias    INTEGER NOT NULL,   -- TODO: valor por tipo de aparelho, definido pelo Product Owner (BR-020)
    data_inicio   TEXT NOT NULL,
    data_fim      TEXT NOT NULL,
    criado_em     TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_vendas_garantias_venda_id ON vendas_garantias(venda_id);
```

Segue a convenção de `ENGINEERING_GUIDE.md` seção 5 (`snake_case`, plural, sem `FOREIGN KEY` declarada,
mesma abordagem do restante do schema hoje — `DATABASE.md` seção 3).

---

## Wireframes conceituais

**Atendimento / checkout**
```
┌───────────────────────────────────────────────┐
│ Nova Venda                                      │
│ Cliente:  [🔍 buscar/cadastrar]                  │
│ Aparelho: [🔍 buscar por IMEI]                   │
│  IMEI 35•••4471 — iPhone 14 Pro 256GB            │
│  Preço tabela: R$ 5.200                          │
│ Troca? [ ] Sim → abre avaliação de usado         │
│ Desconto: [____] (limite do vendedor: R$ X)      │
│ Total: R$ 5.200                                  │
│              [Cancelar]   [Confirmar Venda]      │
└───────────────────────────────────────────────┘
```

**Aprovação de desconto (admin)**
```
┌─────────────────────────────────────┐
│ Aprovação de desconto necessária      │
│ Vendedor: João — desconto R$ 400      │
│ (limite: R$ 200)                      │
│            [Rejeitar]    [Aprovar]    │
└─────────────────────────────────────┘
```

---

## Dependências

- **Clientes** (P0, `docs/product/features/CLIENTES.md`) — bloqueante, BR-022.
- **IMEI Individual** (P0, `docs/product/features/IMEI.md`) — bloqueante, BR-017.
- Estoque existente — reutiliza a lógica de movimentação hoje em `irflow_os.py`, candidata a virar
  `irflow_estoque_service.py` compartilhado (`ENGINEERING_GUIDE.md` §3.1) — Vendas não deve reimplementar
  baixa de estoque.
- Autenticação/perfis existentes — nenhuma mudança de schema de permissão necessária no V1 (reaproveita
  `admin`/`vendedor`/`tecnico`).

---

## Critérios de aceite

- [ ] Fluxo completo (novo e troca) executável do início ao fim sem exigir suposição de tela não especificada
- [ ] IMEI nunca pode ser vendido duas vezes simultaneamente, mesmo com dois vendedores atendendo ao mesmo tempo
- [ ] Comissão calculada sempre sobre margem, nunca sobre valor bruto
- [ ] Desconto acima do limite do vendedor é fisicamente impossível de confirmar sem aprovação de admin
- [ ] Cliente é uma entidade própria — nenhuma venda salva nome de cliente como texto solto
- [ ] Garantia emitida reflete o tipo de aparelho (novo/seminovo), nunca o valor fixo de 90 dias do reparo

---

## Métricas de sucesso

TODO — decisão de Product Owner. Candidatas levantadas em `docs/company/VISION.md` (quando preenchido):
tempo médio de venda, número de vendas com troca, taxa de aprovação de desconto por admin.

---

## Documentos relacionados

- `docs/product/features/CLIENTES.md` — spec da entidade Cliente, pré-requisito deste módulo
- `docs/product/features/IMEI.md` — spec do rastreamento por IMEI, pré-requisito deste módulo
- `docs/company/VISION.md`, `docs/company/PRODUCT_REQUIREMENTS.md` — missão, persona e dores (parcialmente `TODO`, referenciados aqui como provisórios)
- `docs/engineering/DOMAIN_MODEL.md` — domínios existentes hoje (1.3 OS, 1.4 Estoque) e lacunas estruturais (Cliente, Financeiro) citadas nas decisões acima
- `docs/engineering/ENGINEERING_GUIDE.md` seção 3.1 — convenção de camadas obrigatória para o novo domínio Vendas quando for implementado
- `docs/operations/ROADMAP.md` — roadmap de engenharia (eixo separado deste documento)
- `docs/product/BUSINESS_RULES.md` — BR-017 a BR-022, regras extraídas das decisões deste documento
- `docs/company/OPERATION_SYSTEM.md` — blocos Venda/Troca/Reserva/Garantia posicionam este spec no ciclo completo da loja
