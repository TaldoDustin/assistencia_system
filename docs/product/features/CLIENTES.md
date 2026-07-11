# CLIENTES.md — Feature Spec: Entidade Cliente

**Status:** Rascunho — desenhado por Claude (Principal Engineer) a pedido do CTO em 2026-07-11, como
pré-requisito estrutural do Épico Vendas (P0, `docs/product/PRODUCT_BACKLOG.md`). Diferente de
`VENDAS.md`, este spec **não** nasce de uma conversa direta com o Product Owner — as decisões de negócio
abaixo estão marcadas `TODO` e não devem ser tratadas como confirmadas até validação.
**Épico:** Comercial — pré-requisito de `docs/product/features/VENDAS.md`.

---

## Por que existe

`cliente` hoje é uma coluna `TEXT` solta na tabela `os` (`docs/engineering/DOMAIN_MODEL.md` seção 1.3) —
duas OS do mesmo cliente não têm nenhuma ligação estrutural além de, por acaso, terem o mesmo texto
digitado. Isso bloqueia qualquer coisa que dependa de identidade de cliente:

- Vendas não pode existir sem cliente como entidade (`VENDAS.md`, "Decisões já tomadas" — decisão já
  tomada de criar `clientes` no V1 de Vendas).
- CRM (P2, `PRODUCT_BACKLOG.md`) depende de Clientes existir primeiro.
- Histórico consolidado de um cliente é uma dor documentada da persona primária
  (`docs/company/PRODUCT_REQUIREMENTS.md`).

Este spec cobre a entidade em si — não o módulo de CRM (pós-venda, reengajamento), que é um épico
separado e posterior.

---

## Quem usa

| Perfil | Papel |
|---|---|
| `vendedor` | Busca cliente existente ou cadastra rápido durante o atendimento de venda |
| `tecnico` | Associa cliente a uma OS (fluxo já existe hoje via texto; passa a ser busca/seleção) |
| `admin` | Resolve duplicados, edita cadastro completo |

---

## Fluxo completo

```
Início do atendimento (venda ou OS)
        │
        ▼
   Busca cliente
 (nome, telefone ou CPF)
        │
   ┌────┴────┐
 encontrado   não encontrado
   │              │
   ▼              ▼
Seleciona      Cadastro rápido
cliente        (nome + telefone,
   │           mínimo viável)
   │              │
   └──────┬───────┘
          ▼
  Segue o atendimento
  vinculado a cliente_id
```

---

## Decisões estruturais (dependência técnica, não escolha de negócio)

| Decisão | Escolha | Por quê |
|---|---|---|
| Cliente é entidade própria (`clientes`) | Sim | Pré-requisito já registrado em `DOMAIN_MODEL.md` seção 2 e `VENDAS.md` |
| Migração de `os.cliente` | Aditiva — nova coluna `os.cliente_id` (nullable); texto legado preservado | Segue regra de migração de `ENGINEERING_GUIDE.md` seção 5 (sempre aditiva); OS antigas não são resolvidas retroativamente de forma automática |
| Cadastro mínimo viável | Nome + um contato (telefone **ou** e-mail) | Sem isso não há como buscar/reencontrar o cliente depois |

## Decisões de negócio pendentes (Product Owner) — `TODO`

- **Campo de deduplicação:** telefone, CPF/CNPJ, ou ambos? Lojas premium costumam pedir CPF na nota —
  confirmar se é coleta obrigatória ou opcional no cadastro rápido.
- **O que fazer com clientes duplicados já existentes** (mesmo nome, textos diferentes, no histórico de
  `os.cliente`) — merge manual pelo admin, sugestão automática de duplicata, ou aceitar a duplicação como
  está e resolver só daqui para frente?
- **Campos além do mínimo** (endereço, data de nascimento, como conheceu a loja) — nenhum é pré-requisito
  técnico; adicionar só com valor de negócio claro (`BRAND_IDENTITY.md` seção 4 — nunca inflar cadastro
  sem propósito).
- **Edição de cliente após venda/OS existente** — a venda/OS deve manter o nome do cliente como estava no
  momento (snapshot) ou sempre refletir o cadastro atual? Mesmo tipo de decisão já resolvida para peças em
  `os_pecas` (`peca_descricao` como snapshot), mas aqui é decisão de negócio, não só técnica.

---

## Modelo de dados (proposto)

```sql
CREATE TABLE clientes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    telefone        TEXT,
    email           TEXT,
    cpf_cnpj        TEXT,
    observacoes     TEXT NOT NULL DEFAULT '',
    criado_em       TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em   TEXT NOT NULL DEFAULT (datetime('now'))
);
-- telefone e cpf_cnpj são os campos de deduplicação mais prováveis, mas UNIQUE só deve ser
-- aplicado depois da decisão de negócio pendente acima.
CREATE INDEX idx_clientes_telefone ON clientes(telefone);
CREATE INDEX idx_clientes_cpf_cnpj ON clientes(cpf_cnpj);
CREATE INDEX idx_clientes_nome ON clientes(nome);

-- Migração aditiva em `os` (segue ENGINEERING_GUIDE.md seção 5)
ALTER TABLE os ADD COLUMN cliente_id INTEGER;  -- FK lógica para clientes.id, nullable
-- coluna `os.cliente` (TEXT) permanece — não é removida nesta migração
```

Segue a convenção de nomenclatura de `ENGINEERING_GUIDE.md` seção 5 (`snake_case`, plural,
`idx_<tabela>_<coluna>`). Sem `FOREIGN KEY` declarada, mesma convenção do restante do schema hoje
(`DATABASE.md` seção 3).

---

## Wireframes conceituais

**Busca de cliente (componente reutilizável — usado em Vendas e em OS)**
```
┌─────────────────────────────────────────┐
│ 🔍 Buscar cliente (nome, telefone, CPF)  │
├─────────────────────────────────────────┤
│ João Silva       (11) 9****-1234         │
│ João Souza       (11) 9****-5678         │
├─────────────────────────────────────────┤
│ Nenhum encontrado? [+ Cadastrar rápido]  │
└─────────────────────────────────────────┘
```

**Cadastro rápido (modal, não interrompe o atendimento)**
```
┌───────────────────────────────┐
│ Novo cliente                   │
│ Nome*      [______________]    │
│ Telefone   [______________]    │
│ E-mail     [______________]    │
│ CPF/CNPJ   [______________]    │
│             [Cancelar] [Salvar]│
└───────────────────────────────┘
```

**Ficha do cliente (histórico consolidado — coluna "Compras" depende de Vendas existir)**
```
┌───────────────────────────────────────────┐
│ João Silva — (11) 9****-1234               │
│ Cliente desde: 12/03/2026                  │
├───────────────────────────────────────────┤
│ Histórico                                  │
│  OS #1234  Finalizado   12/05/2026         │
│  OS #1198  Finalizado   03/02/2026         │
│  Venda #88 Paga         (quando existir)   │
└───────────────────────────────────────────┘
```

---

## Casos de erro

| Cenário | Comportamento esperado |
|---|---|
| Cadastro rápido sem nome | Bloqueado — nome é obrigatório |
| Cadastro rápido sem nenhum contato (nem telefone, nem e-mail) | Bloqueado — sem contato, o cliente não pode ser reencontrado depois |
| Busca retorna múltiplos clientes com nome igual | Lista todos, desambigua por telefone parcial mascarado (ver wireframe) |
| Tentativa de excluir cliente com histórico (OS ou venda vinculada) | Bloqueado — mesmo padrão de `BR-005` (item de estoque não pode ser excluído em uso) |

---

## Critérios de aceite

- [ ] `clientes` existe como tabela própria; nenhuma venda ou OS nova salva nome de cliente apenas como texto
- [ ] Cadastro rápido não é mais lento que digitar o nome livre no fluxo atual (senão o vendedor evita usar)
- [ ] Busca funciona por nome parcial, telefone parcial ou CPF
- [ ] OS existentes (com `cliente` em texto, sem `cliente_id`) continuam funcionando sem quebrar — migração é aditiva, não obrigatória retroativamente
- [ ] Cliente com histórico não pode ser excluído

---

## Dependências

- Nenhuma dependência técnica de outro domínio novo — pode ser implementado isoladamente.
- É pré-requisito de: Vendas (P0), CRM (P2), Garantia por venda.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — consumidor principal desta entidade (BR-022)
- `docs/engineering/DOMAIN_MODEL.md` seção 1.3, seção 2 — observação original do gap
- `docs/engineering/ENGINEERING_GUIDE.md` seção 3.1 — convenção de domínio novo (controller/service/repository)
- `docs/product/PRODUCT_BACKLOG.md` — priorização P0
