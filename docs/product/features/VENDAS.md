# VENDAS.md — Feature Spec: Módulo de Vendas

**Status:** Vendas MVP + Sprint 1.1 (Histórico + Detalhe) implementados em 2026-07-27 — ver seção "Vendas
MVP — o que foi entregue" abaixo. V1.2 (Cancelamento) tem a discuss-phase concluída (seção "V1.2 —
Cancelamento" abaixo) mas nenhum código escrito ainda. O restante do fluxo completo desenhado neste
documento (desconto/aprovação, comissão, garantia, troca/avaliação de usado, reserva com timeout) segue
como especificação, não implementado — depende de decisões do Product Owner ainda pendentes (seção "O que
ainda está em aberto").
**Épico:** Comercial (ver `docs/operations/ROADMAP.md` para o eixo de engenharia — este documento pertence ao eixo de produto, numeração própria a definir em `PRODUCT_BACKLOG.md`).
**Atualizado em 2026-07-11** (Claude, a pedido do CTO): adicionadas as seções "Modelo de dados",
"Wireframes conceituais" e "Dependências", que faltavam no rascunho original. Nenhuma decisão da seção
"Decisões já tomadas" foi alterada.
**Atualizado em 2026-07-27** (Claude, a pedido do CTO): seção "Vendas MVP — o que foi entregue"
adicionada; "Modelo de dados" corrigido para refletir o schema real implementado (difere do proposto
originalmente em dois pontos, ver nota na própria seção).
**Atualizado em 2026-07-27** (Claude, discuss-phase com o CTO, após `ADR-009`): seção "V1.2 —
Cancelamento" adicionada — regras de negócio fechadas (BR-031 a BR-036), nenhum código escrito.

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

## Vendas MVP — o que foi entregue (2026-07-27)

Primeira fatia implementada, decisão explícita de escopo (conversa com o CTO, 2026-07-27): venda de
**um único aparelho por vez** (uma unidade serializada), sem desconto, comissão, garantia, troca ou
reserva com timeout — todos dependem de decisões do Product Owner ainda pendentes (seção "O que ainda
está em aberto" abaixo). Ver `docs/operations/SPRINTS/SPRINT_COMERCIAL_VENDAS_MVP.md` para o relatório
completo da sprint.

**Decisões de modelagem tomadas nesta sprint, à frente do necessário para o MVP** (para evitar
retrabalho quando desconto/comissão/garantia/troca forem implementados):

- **`Venda` + `ItemVenda` desde o início**, não uma tabela `vendas` só com um aparelho embutido — mesmo
  que esta fatia sempre crie exatamente um item por venda. Quando a plataforma vender múltiplos itens
  na mesma operação (aparelho + acessórios), a tabela já está pronta.
- **`status='concluida'`, não `'paga'`** — venda e pagamento são conceitos diferentes, não misturados.
  Um futuro conceito de status de pagamento (pendente/pago/estornado) não precisa ser espremido dentro
  do status da venda.
- **Snapshot de `produto_nome`/`produto_sku`** em `vendas_itens` — preserva o histórico da venda mesmo
  se o cadastro do produto/estoque for alterado depois (mesmo padrão já usado em
  `os_pecas.peca_descricao`/`peca_fornecedor`/`peca_modelo`).
- **`UNIQUE` em `vendas_itens.unidade_serializada_id`** — garante no nível do banco que a mesma unidade
  nunca aparece em duas vendas, mesmo sob concorrência real (não só uma checagem na aplicação).
- **Sem reserva com timeout**: a unidade vai direto de `disponivel` para `vendido` (sem passar por
  `reservado`) — evita decidir o valor do timeout agora; reintroduzir `reservado` fica para quando
  existir carrinho/orçamento reais.
- **Preço pré-preenchido e editável** (`valor_tabela` vs. `valor_unitario`): ao selecionar o aparelho, o
  preço de catálogo (`estoque.valor`/`produtos.preco_venda`) já vem preenchido no formulário, mas o
  vendedor pode alterar livremente — sem aprovação nesta fatia. Ambos os valores são persistidos
  separados, nunca um sobrescreve o outro.
- **`observacoes`** (texto livre em `vendas`) — cadastro/retirada/venda corporativa, campo simples e
  barato de já existir desde o início.

**Primeiro módulo a nascer com o prefixo `fluxoly_`** (`fluxoly_vendas_controller.py`/`_service.py`/
`_repository.py`), não `irflow_` — ver `docs/engineering/adr/ADR-008.md`.

**Frontend:** `frontend/src/pages/Vendas.jsx` (rota `/vendas`, sidebar visível para `admin`/`vendedor`)
— busca de cliente, busca combinada de aparelho (IMEI/modelo/SKU, reaproveitando o filtro de C1.3.3),
resumo automático assim que ambos selecionados, confirmação, e tela de sucesso com atalhos para nova
venda / conferir o registro salvo no servidor / imprimir (placeholder, ainda não implementado).

**Fora de escopo desta fatia:** desconto/aprovação de admin, comissão, garantia (`vendas_garantias` não
criada), troca/avaliação de usado, reserva com timeout, cancelamento de venda.

**Backlog documentado, não implementado:** `vendas_itens` não guarda `custo`/`margem` no momento da
venda (só `valor_unitario`/`subtotal`). Quando o cálculo de comissão sobre margem (BR-019) for
implementado, provavelmente vale adicionar essas duas colunas como snapshot histórico — mesma lógica
do snapshot de `produto_nome`/`produto_sku` — para a margem de uma venda passada não mudar se o custo
do produto for reajustado depois. Não adicionado agora porque ficaria `NULL` sem nenhum consumidor.

---

## V1.2 — Cancelamento (discuss-phase concluída em 2026-07-27; não implementado)

Antes de qualquer plano técnico, as regras de negócio de cancelamento foram fechadas em conversa direta
com o usuário (CTO), motivadas por `docs/engineering/adr/ADR-009.md` ter deixado deliberadamente em
aberto o mecanismo de unicidade de `vendas_itens.unidade_serializada_id` para "quando V1.2 for de fato
implementada". Nenhum código escrito ainda — este bloco é a especificação, `BR-031` a `BR-036`
(`docs/product/BUSINESS_RULES.md`) são as regras formais derivadas dela.

**Escopo da migração de schema (decisão explícita, não um recuo de `ADR-009`):** `ADR-009` define o
modelo-alvo de longo prazo (Estado Operacional do Ativo × Situação Comercial em eixos separados), mas não
exige que essa migração aconteça nesta sprint — uma ADR pode definir o destino arquitetural sem obrigar
toda fase subsequente a implementá-lo de imediato (mesmo padrão já usado no rebranding `ADR-008`: módulos
novos nascem `fluxoly_*`, os existentes não foram renomeados até fazer sentido). V1.2 mantém o enum único
`unidades_serializadas.status` — cancelar uma venda devolve a unidade para `disponivel`, mesma mecânica já
usada em `devolvido → disponivel` (Assistência) — através de uma função de domínio dedicada
(`liberar_unidade_para_venda`, a implementar), nunca por atribuição direta de `status` espalhada pelo
código, para que a futura migração para os dois eixos troque só essa função, não dezenas de call sites. A
migração real fica para quando Garantia/Troca precisarem de fato da ortogonalidade (`em_reparo` E
`vendido` simultaneamente) — não antes.

**Mecanismo do `UNIQUE`:** a regra de domínio está fechada — *"uma Unidade Serializada pode aparecer em
várias vendas ao longo da vida, mas só uma pode estar vigente ao mesmo tempo"* — mas a implementação
exata (coluna `ativo`, `cancelado_em IS NULL`, um campo de status no item, ou outra abordagem) fica para o
plano técnico, considerando também cancelamento parcial futuro (múltiplos itens por venda) e a eventual
integração com Garantia/Financeiro. A regra de negócio vive no `service` (valida, executa a transação);
a constraint do banco é a última linha de defesa contra corrida concorrente, nunca a representação
primária da regra.

**`cancelada` vs. `estornada`:** V1.2 implementa só `cancelada` — decisão comercial/operacional (cliente
desistiu, erro de lançamento, IMEI incorreto, venda duplicada, pagamento não concluído, produto
indisponível), sem nenhuma reversão financeira, já que Vendas MVP não tem caixa formal (`VENDAS.md`
"Decisões já tomadas": "V1 registra pagamento simples, sem caixa formal"). `estornada` (também prevista na
máquina de estados `criada → reservada → concluida → cancelada → estornada` de `ADR-009`) só existe
quando há algo financeiro real para reverter (PIX devolvido, cartão cancelado) — implementada junto do
Épico Financeiro, não antes.

**Quem pode cancelar:** `admin` cancela qualquer venda; `vendedor` só cancela vendas que ele mesmo
realizou; `tecnico` e demais perfis não podem. Sem limite de tempo nesta fase — a segurança vem de perfil
+ motivo obrigatório + auditoria, não de janela temporal. Uma janela (ex.: só no mesmo dia) pode virar
configuração por loja no futuro, quando a plataforma tiver múltiplos clientes com políticas diferentes —
não decidida nem implementada agora, para não transformar uma política operacional variável em regra fixa
do sistema.

**Motivo obrigatório:** lista fechada (`cliente_desistiu` \| `erro_lancamento` \| `imei_incorreto` \|
`venda_duplicada` \| `pagamento_nao_concluido` \| `produto_indisponivel` \| `outro`), rejeitada se fora da
lista — mesmo padrão de `categoria`/`condicao` em Produtos (BR-027), nunca normalizada. Quando `outro`,
uma descrição complementar (`observacao_cancelamento`) é obrigatória. Habilita métricas por motivo de
cancelamento sem parsing de texto (pilar de Inteligência, `BRAND_IDENTITY.md` seção 2).

**Princípio da Imutabilidade da Venda:** uma venda representa um fato histórico — cancelada é estado
terminal, nunca retorna a `concluida` ("reativação" não existe). Uma nova negociação sobre a mesma unidade
sempre gera uma venda nova, nunca reabre a cancelada. Preserva quando/por quê/quem cancelou e por quanto
tempo a venda original ficou concluída, sem perder essa informação numa reversão.

**Histórico (Sprint Vendas 1.1, já implementada):** a listagem (`GET /api/vendas`) deve mostrar vendas
canceladas por padrão, identificadas por badge de status — histórico nunca esconde fatos por padrão. O
filtro por `status`, já implementado no backend, permite restringir a visualização quando necessário.
Ajuste de frontend pendente (`Historico()` em `Vendas.jsx` ainda não tem badge de status nem filtro de
status na UI — só os filtros de forma de pagamento/data/ordenação da Sprint Vendas 1.1); a implementação
completa fica para quando V1.2 for construída.

---

## Modelo de dados (implementado — difere do proposto originalmente)

Depende de `docs/product/features/CLIENTES.md` (`clientes`) e `docs/product/features/IMEI.md`
(`unidades_serializadas`) existirem antes de fazer sentido implementar este schema — ambos entregues
antes desta sprint.

**Diferenças em relação ao schema originalmente proposto (2026-07-11), decididas em 2026-07-27:**
`status` nasce como `'concluida'` (não `'paga'`); `vendas_itens` ganhou `produto_nome`/`produto_sku`
(snapshot, não previstos na versão original) e `quantidade` (sempre `1` nesta fatia, existe para
quando itens agregados/não serializados — ex. acessórios — forem vendidos); `comissao_percentual`/
`comissao_valor`/`aprovado_por`/`desconto` e a tabela `vendas_garantias` **não foram criados** nesta
sprint — ficam para quando as decisões de negócio correspondentes existirem.

**Nota (2026-07-20, Sprint Comercial 0.1) — resolvida em 2026-07-21 (ADR-007):** este schema foi
escrito antes de existir um catálogo comercial (`produtos`, ver `docs/engineering/DATABASE.md`) —
`estoque_unidades` era, até então, a única tabela candidata a representar "o que foi vendido", o que
faria a venda de um iPhone do catálogo comercial apontar para a tabela de peças de reparo. Resolvido:
`estoque_unidades` evoluiu para `unidades_serializadas` (ADR-007,
`docs/engineering/migrations/MIGRATION_unidades_serializadas.md`) — fonte única de verdade para
qualquer unidade física, com origem em Estoque OU Produtos (`produto_id`, nullable). O campo
`estoque_unidade_id` abaixo deve apontar para `unidades_serializadas.id`, qualquer que seja a origem
real da unidade vendida.

### Schema real implementado (2026-07-27, Vendas MVP)

```sql
CREATE TABLE vendas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id      INTEGER NOT NULL,               -- FK lógica: clientes.id
    vendedor_id     INTEGER NOT NULL,               -- FK lógica: usuarios.id (sempre o usuário da sessão)
    forma_pagamento TEXT NOT NULL,                  -- 'pix' | 'cartao' | 'dinheiro' | 'transferencia'
    valor_total     REAL NOT NULL,
    status          TEXT NOT NULL DEFAULT 'concluida',  -- só 'concluida' alcançável nesta fatia
    observacoes     TEXT NOT NULL DEFAULT '',        -- livre (ex.: "retirada amanhã")
    criado_em       TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_vendas_cliente_id ON vendas(cliente_id);
CREATE INDEX idx_vendas_vendedor_id ON vendas(vendedor_id);

CREATE TABLE vendas_itens (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    venda_id                INTEGER NOT NULL,       -- FK lógica: vendas.id
    unidade_serializada_id  INTEGER NOT NULL,       -- FK lógica: unidades_serializadas.id
    produto_id              INTEGER,                -- denormalizado de unidades_serializadas.produto_id; NULL se origem é Estoque
    produto_nome            TEXT NOT NULL,          -- snapshot no momento da venda
    produto_sku             TEXT,                   -- snapshot, nullable
    quantidade              INTEGER NOT NULL DEFAULT 1,  -- sempre 1 nesta fatia
    valor_tabela            REAL,                   -- snapshot do preço de catálogo; NULL se não cadastrado
    valor_unitario          REAL NOT NULL,          -- preço efetivo da venda, pode divergir de valor_tabela
    subtotal                REAL NOT NULL,
    criado_em               TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_vendas_itens_venda_id ON vendas_itens(venda_id);
CREATE UNIQUE INDEX idx_vendas_itens_unidade_serializada_id ON vendas_itens(unidade_serializada_id);
```

Segue a convenção de `ENGINEERING_GUIDE.md` seção 5 (`snake_case`, plural, sem `FOREIGN KEY` declarada,
mesma abordagem do restante do schema hoje — `DATABASE.md` seção 3). Ver `DATABASE.md` seção 2 para a
entrada oficial destas duas tabelas.

### Schema completo original (visão futura, não implementado)

Preservado como referência do fluxo completo desenhado em 2026-07-09 — `desconto`, `comissao_*`,
`aprovado_por`, `troca_estoque_unidade_id`, `margem`/`custo` calculados e `vendas_garantias` só
existirão quando as decisões de negócio correspondentes (seção "O que ainda está em aberto") forem
tomadas pelo Product Owner. Não é o schema real hoje.

```sql
CREATE TABLE vendas (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id                  INTEGER NOT NULL,   -- FK lógica para clientes.id (CLIENTES.md)
    vendedor_id                 INTEGER NOT NULL,   -- FK lógica para usuarios.id
    estoque_unidade_id          INTEGER NOT NULL,   -- FK lógica para unidades_serializadas.id (IMEI.md, ADR-007) — aparelho vendido
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

- [ ] Fluxo completo (novo e troca) executável do início ao fim sem exigir suposição de tela não especificada — **parcial**: fluxo de venda de aparelho novo (sem troca) implementado no Vendas MVP (2026-07-27); troca/avaliação de usado não implementada
- [x] IMEI nunca pode ser vendido duas vezes simultaneamente, mesmo com dois vendedores atendendo ao mesmo tempo — **atendido no Vendas MVP**: `UNIQUE` em `vendas_itens.unidade_serializada_id` + `UPDATE ... WHERE status='disponivel'`, provado por teste com threads reais (`tests/test_vendas.py`)
- [ ] Comissão calculada sempre sobre margem, nunca sobre valor bruto — não implementado, depende do % de comissão (decisão do Product Owner)
- [ ] Desconto acima do limite do vendedor é fisicamente impossível de confirmar sem aprovação de admin — não implementado, depende do limite (decisão do Product Owner)
- [x] Cliente é uma entidade própria — nenhuma venda salva nome de cliente como texto solto — **atendido**: `vendas.cliente_id` é FK lógica para `clientes.id`, obrigatória
- [ ] Garantia emitida reflete o tipo de aparelho (novo/seminovo), nunca o valor fixo de 90 dias do reparo — não implementado, `vendas_garantias` não criada

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
- `docs/product/BUSINESS_RULES.md` — BR-017 a BR-022 (fluxo original), BR-031 a BR-036 (V1.2 — Cancelamento)
- `docs/company/OPERATION_SYSTEM.md` — blocos Venda/Troca/Reserva/Garantia posicionam este spec no ciclo completo da loja
- `docs/engineering/adr/ADR-009.md` — modelo de domínio da Unidade Serializada (eixos, `origem_tipo`, mecanismo do `UNIQUE`) que a seção "V1.2 — Cancelamento" fecha
