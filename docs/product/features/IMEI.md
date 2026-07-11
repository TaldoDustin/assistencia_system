# IMEI.md — Feature Spec: Rastreamento Individual por IMEI

**Status:** Rascunho — desenhado por Claude (Principal Engineer) a pedido do CTO em 2026-07-11, como
pré-requisito estrutural do Épico Vendas (P0). Assim como `CLIENTES.md`, ainda sem validação direta do
Product Owner — decisões de negócio abaixo marcadas `TODO`.
**Épico:** Comercial/Operação — extensão do domínio Estoque existente (`DOMAIN_MODEL.md` seção 1.4),
pré-requisito de `docs/product/features/VENDAS.md`.

---

## Por que existe

Gap já documentado em dois lugares antes deste spec:
- `docs/company/BRAND_IDENTITY.md` seção 2: a marca promete rastreamento individual por IMEI; a tabela
  `estoque` hoje só controla quantidade agregada.
- `docs/company/PRODUCT_REQUIREMENTS.md`, Persona Primária: "IMEIs perdidos ou difíceis de localizar" é
  uma dor real citada pelo Product Owner.

Também é pré-requisito direto de `VENDAS.md` — BR-017 ("um IMEI só pode estar reservado ou vendido em um
atendimento por vez") não pode ser implementada sem uma unidade individual para reservar.

---

## Quem usa

| Perfil | Papel |
|---|---|
| `vendedor` | Busca disponibilidade por IMEI, reserva durante o atendimento |
| `admin`/estoque | Cadastra entrada de unidade com IMEI, consulta status |
| `tecnico` | Associa IMEI a um aparelho recebido em troca/avaliação |

---

## Escopo: nem todo item de estoque precisa de IMEI

Decisão estrutural, não de negócio: peças de reparo (tela, bateria, conector) continuam controladas por
quantidade agregada, como hoje — não faz sentido rastrear uma tela por IMEI. Rastreamento por IMEI se
aplica a **aparelhos completos** (iPhone, Apple Watch — AirPods normalmente não têm IMEI, têm número de
série, ver "Decisões de negócio pendentes"). Isso é uma extensão do domínio Estoque, não sua substituição.

---

## Fluxo completo

```
Compra de aparelho chega
        │
        ▼
Cadastro da unidade
(IMEI + vínculo ao lote de compra)
        │
        ▼
   status = disponível
        │
        ▼
Vendedor busca/consulta IMEI
        │
   ┌────┴─────┐
 disponível   reservado/vendido
   │              │
   ▼              ▼
Reserva        Bloqueado
(expira        (mostra até quando a
automaticamente) reserva atual expira)
   │
   ▼
Venda confirmada → status = vendido
   │
   ▼
(cancelamento de venda → status volta a disponível)
```

---

## Decisões estruturais

| Decisão | Escolha | Por quê |
|---|---|---|
| Unidade por IMEI é entidade própria, não coluna em `estoque` | Nova tabela `estoque_unidades` | `estoque` representa o item/SKU agregado; a unidade física é uma instância dele — mesma relação que `estoque_lotes` já tem hoje |
| Nem todo item de estoque tem unidades por IMEI | Sim — flag no cadastro do item (`estoque.requer_imei`) | Evita forçar peças de reparo a terem IMEI, que não existe para elas |
| Reserva com expiração automática | Sim (mesma decisão já tomada em `VENDAS.md`, BR-017) | Evita venda duplicada sem travar estoque indefinidamente |

## Decisões de negócio pendentes (Product Owner) — `TODO`

- **AirPods e acessórios têm IMEI?** Não — têm número de série (formato diferente). O campo deve ser
  genérico ("identificador de unidade") ou o V1 assume só iPhone/Apple Watch e AirPods continuam
  agregados? Afeta o nome do campo e a validação.
- **Validação de formato de IMEI** (15 dígitos, checksum Luhn) — validar no cadastro ou aceitar qualquer
  texto por enquanto e corrigir depois?
- **Duração do timeout de reserva** — mesma pendência já registrada em `VENDAS.md` ("O que ainda está em
  aberto"), não duplicar decisão aqui.
- **Estoque físico já existente sem IMEI cadastrado** (itens `quantidade > N` sem unidade individual) —
  migração retroativa de dados é decisão de operação, fora de escopo deste spec, ou o V1 assume que só
  entradas novas ganham IMEI?

---

## Modelo de dados (proposto)

```sql
CREATE TABLE estoque_unidades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    estoque_id      INTEGER NOT NULL,   -- FK lógica para estoque.id (SKU agregado)
    lote_id         INTEGER,            -- FK lógica para estoque_lotes.id
    imei            TEXT UNIQUE,        -- validação de formato: TODO (decisão pendente)
    status          TEXT NOT NULL DEFAULT 'disponivel',
        -- 'disponivel' | 'reservado' | 'vendido' | 'em_reparo' | 'devolvido'
    reservado_por   INTEGER,            -- FK lógica para usuarios.id
    reservado_ate   TEXT,               -- timestamp; NULL quando não reservado
    venda_id        INTEGER,            -- FK lógica para vendas.id (só preenchível quando VENDAS.md existir)
    criado_em       TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_estoque_unidades_estoque_id ON estoque_unidades(estoque_id);
CREATE INDEX idx_estoque_unidades_status ON estoque_unidades(status);
CREATE INDEX idx_estoque_unidades_imei ON estoque_unidades(imei);

-- Extensão aditiva em `estoque` para distinguir item agregado de item rastreado por unidade
ALTER TABLE estoque ADD COLUMN requer_imei INTEGER NOT NULL DEFAULT 0;
```

Segue a mesma convenção de `estoque_lotes` (relação lógica sem `FOREIGN KEY` declarada, `DATABASE.md`
seção 3).

---

## Wireframes conceituais

**Busca por IMEI (barra única, digitação parcial)**
```
┌─────────────────────────────────────┐
│ 🔍 Buscar por IMEI (últimos dígitos) │
├─────────────────────────────────────┤
│ iPhone 14 Pro 256GB   ...4471        │
│ status: disponível                   │
└─────────────────────────────────────┘
```

**Detalhe da unidade**
```
┌───────────────────────────────────────┐
│ IMEI 35•••••••••••4471                 │
│ iPhone 14 Pro 256GB — Grafite          │
│ Status: reservado até 15:42 (vendedor  │
│ João)                                  │
├───────────────────────────────────────┤
│ Histórico                              │
│  Entrada    12/06/2026 (lote #34)      │
│  Reservado  11/07/2026 15:12           │
└───────────────────────────────────────┘
```

---

## Casos de erro

| Cenário | Comportamento esperado |
|---|---|
| IMEI duplicado no cadastro | Bloqueado — `UNIQUE` na coluna |
| Busca sem resultado | Mensagem explícita, nunca lista vazia sem explicação |
| Reservar unidade já reservada por outro atendimento | Bloqueado, mostra até quando a reserva atual expira (mesmo comportamento de `VENDAS.md`, "Casos de erro") |
| Reservar unidade com status `vendido` ou `em_reparo` | Bloqueado |

---

## Critérios de aceite

- [ ] Toda unidade rastreável (iPhone/Apple Watch, conforme decisão pendente acima) tem IMEI único cadastrado
- [ ] Busca por IMEI (parcial ou completo) retorna a unidade rapidamente
- [ ] Duas reservas simultâneas do mesmo IMEI são impossíveis, mesmo com dois vendedores digitando ao mesmo tempo (mesma garantia exigida em `VENDAS.md`)
- [ ] Itens que não requerem IMEI (peças) continuam funcionando exatamente como hoje — nenhuma regressão em `BR-004` a `BR-007`

---

## Dependências

- Estende o domínio Estoque existente (`DOMAIN_MODEL.md` 1.4) — não é domínio isolado novo.
- É pré-requisito de: Vendas (reserva de IMEI, BR-017).
- `venda_id` na tabela proposta só é preenchível depois que `VENDAS.md` for implementado — nullable até lá.

---

## Documentos relacionados

- `docs/company/BRAND_IDENTITY.md` seção 2 — gap de marca original
- `docs/company/PRODUCT_REQUIREMENTS.md` — dor da persona primária
- `docs/engineering/DOMAIN_MODEL.md` seção 1.4 — domínio Estoque hoje
- `docs/product/features/VENDAS.md` — BR-017, consumidor principal desta entidade
