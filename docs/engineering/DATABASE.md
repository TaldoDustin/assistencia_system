# DATABASE.md — Schema, Índices e Regras de Migração

Este documento reflete o schema **real** produzido por `criar_tabelas()` em `app.py`, incluindo as
colunas adicionadas posteriormente via `ALTER TABLE` ad-hoc. Em caso de dúvida sobre o estado real
de um ambiente, inspecione o banco diretamente — não assuma que este documento está 100% sincronizado
(ver KI-004: ausência de migrations formais é dívida técnica conhecida, planejada para Sprint 4).

**Última revisão:** 2026-07-07
**Motor:** SQLite, modo WAL (`_configurar_conexao_sqlite(conn, habilitar_wal=True)`)

---

## 1. Regras de Migração (estado atual)

- Todo schema é definido em `app.py`, função `criar_tabelas()`, executada na inicialização da
  aplicação.
- Tabelas são criadas com `CREATE TABLE IF NOT EXISTS` — idempotente.
- Colunas adicionadas após a criação inicial da tabela usam `ALTER TABLE ... ADD COLUMN` dentro de um
  bloco `try/except sqlite3.OperationalError: pass` — também idempotente, mas **sem histórico
  versionado**: não há como saber, olhando o código, em qual ordem/sprint cada `ALTER TABLE` foi
  introduzido sem checar o histórico do Git.
- Não existem migrations formais (Alembic ou scripts numerados). Isso está registrado como KI-004 /
  TD-03 e é o objetivo da Sprint 4 (`migrations/001_initial_schema.sql`, `migrations/002_shopping_list.sql`, etc.).
- **Regra para qualquer alteração futura de schema:** seguir `ENGINEERING_GUIDE.md` seção 5 —
  migrations sempre aditivas em produção, backup verificado antes de aplicar, atualização obrigatória
  deste documento.

---

## 2. Tabelas

### `usuarios`

Autenticação e perfis de acesso.

| Coluna | Tipo | Constraints | Descrição |
|--------|------|-------------|-----------|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `nome` | TEXT | NOT NULL | Nome de exibição |
| `usuario` | TEXT | UNIQUE NOT NULL | Login (usado para autenticação) |
| `senha_hash` | TEXT | NOT NULL | Hash Werkzeug (`generate_password_hash`) |
| `perfil` | TEXT | NOT NULL DEFAULT `'tecnico'` | `admin` \| `tecnico` \| `vendedor` |
| `ativo` | INTEGER | NOT NULL DEFAULT `1` | `0` desativa o login mesmo com senha correta |

**Regras de negócio:**
- Login só é bem-sucedido se `ativo = 1` e hash confere (`irflow_blueprints_auth.py`,
  `irflow_blueprints_api.py` rota `/api/auth/login`).
- Um usuário não pode desativar (`ativo = 0`) nem deletar a própria conta enquanto logado
  (checagem por `uid == session.get("usuario_id")`).
- Sem índice explícito além do `UNIQUE` em `usuario` (que já cria índice implícito no SQLite).

### `os` — Ordens de Serviço

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `tipo` | TEXT | `Assistencia` \| `Garantia` \| `Upgrade` |
| `cliente` | TEXT | |
| `aparelho` | TEXT | |
| `tecnico` | TEXT | |
| `reparo_id` | INTEGER | legado — reparo único; substituído por `os_reparos` (N:N) |
| `status` | TEXT | ver `irflow_core.py` — `STATUS_OS_VALIDOS` |
| `valor_cobrado` | REAL | |
| `valor_descontado` | REAL | |
| `custo_pecas` | REAL | |
| `data` | TEXT | |
| `data_finalizado` | TEXT | *(ALTER)* |
| `modelo` | TEXT | *(ALTER)* — normalizado via `normalizar_modelo_iphone` |
| `cor` | TEXT | *(ALTER)* |
| `imei` | TEXT | *(ALTER)* — normalizado via `normalizar_imei` |
| `vendedor` | TEXT | *(ALTER)* |
| `observacoes` | TEXT | *(ALTER)* |
| `origem_integracao` | TEXT | *(ALTER)* — origem quando criada via MercadoPhone |
| `id_externo_integracao` | TEXT | *(ALTER)* — id no sistema externo |

Sem índice declarado explicitamente (candidato a `idx_os_status_data_tecnico` — ver KI-005/Sprint 5).

### `reparos`

| Coluna | Tipo |
|--------|------|
| `id` | INTEGER PK AUTOINCREMENT |
| `nome` | TEXT |

### `os_reparos` — associação N:N entre OS e reparos

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `os_id` | INTEGER | NOT NULL, parte da PK composta |
| `reparo_id` | INTEGER | NOT NULL, parte da PK composta |

PK composta `(os_id, reparo_id)`. Populada retroativamente a partir de `os.reparo_id` (migração de
dados feita inline em `criar_tabelas()` via `INSERT OR IGNORE`).

### `estoque`

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `descricao` | TEXT | |
| `valor` | REAL | |
| `fornecedor` | TEXT | |
| `quantidade` | INTEGER | quantidade agregada (ver `estoque_lotes` para rastreio por lote) |
| `data_compra` | TEXT | |
| `sku` | TEXT | *(ALTER)* — gerado como `ITEM-<id>` quando ausente |
| `modelo` | TEXT | *(ALTER)* — normalizado via `normalizar_modelo_iphone` |
| `tipo` | TEXT | *(ALTER)* |
| `qualidade` | TEXT | *(ALTER)* |

**Índices:**
- `idx_estoque_sku` em `(sku)`
- `idx_estoque_tripla` em `(modelo, tipo, qualidade)` — suporta busca de peça compatível por
  modelo/tipo/qualidade

### `estoque_lotes`

Rastreio de lotes de compra por item de estoque (FIFO de custo).

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `estoque_id` | INTEGER | NOT NULL — FK lógica para `estoque.id` (sem `FOREIGN KEY` declarado) |
| `fornecedor` | TEXT | |
| `valor_compra` | REAL | |
| `quantidade` | INTEGER | quantidade original do lote |
| `quantidade_disponivel` | INTEGER | decrementada ao consumir peça em uma OS |
| `data_compra` | TEXT | |
| `observacoes` | TEXT | |
| `criado_em` | TEXT | |

**Índice:** `idx_lotes_estoque_id` em `(estoque_id)`.

Lotes iniciais são criados retroativamente para itens de `estoque` com `quantidade > 0` que ainda não
tinham lote (migração inline em `criar_tabelas()`, `observacoes = 'lote inicial legado'`).

### `os_pecas` — peças aplicadas a uma OS

| Coluna | Tipo | Observação |
|--------|------|------------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `os_id` | INTEGER | FK lógica para `os.id` |
| `estoque_id` | INTEGER | FK lógica para `estoque.id` |
| `quantidade` | INTEGER | |
| `valor` | REAL | *(ALTER)* |
| `peca_descricao` | TEXT | *(ALTER)* — snapshot da descrição no momento do consumo |
| `peca_fornecedor` | TEXT | *(ALTER)* — snapshot do fornecedor |
| `peca_modelo` | TEXT | *(ALTER)* — snapshot do modelo |

As colunas `peca_*` existem para preservar o histórico mesmo se o item de estoque original for
editado ou removido depois.

### `movimentacoes`

Log de entradas/saídas de estoque.

| Coluna | Tipo |
|--------|------|
| `id` | INTEGER PK AUTOINCREMENT |
| `estoque_id` | INTEGER |
| `tipo` | TEXT |
| `quantidade` | INTEGER |
| `data` | TEXT |

### `custos_operacionais`

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `descricao` | TEXT | NOT NULL |
| `categoria` | TEXT | |
| `valor` | REAL | NOT NULL |
| `data` | TEXT | |
| `observacoes` | TEXT | |

### `compras` — lista de compras (versão legada/simplificada)

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `produto` | TEXT NOT NULL | |
| `os_id` | INTEGER | |
| `quantidade` | INTEGER NOT NULL | `1` |
| `status` | TEXT | `'PENDENTE'` |
| `criado_em` | TEXT | `''` |
| `atualizado_em` | TEXT | `''` |

> Nota: coexiste com `shopping_list` (mais completa, com workflow de status e log). `compras` parece
> ser a versão anterior — confirmar com o time antes de assumir qual é a fonte de verdade atual para
> novas features.

### `shopping_list`

Lista de compras com workflow de status (entregue na Sprint 1).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `os_id` | INTEGER | |
| `produto_id` | INTEGER | |
| `produto_nome` | TEXT | |
| `quantidade_solicitada` | INTEGER NOT NULL | `1` |
| `quantidade_comprada` | INTEGER NOT NULL | `0` |
| `quantidade_recebida` | INTEGER NOT NULL | `0` |
| `prioridade` | TEXT | `'NORMAL'` |
| `status` | TEXT | `'PENDENTE'` |
| `responsavel_id` | INTEGER | |
| `observacao` | TEXT | `''` |
| `created_at` | TEXT NOT NULL | `datetime('now')` |
| `updated_at` | TEXT NOT NULL | `datetime('now')` |
| `purchased_at` | TEXT | |
| `received_at` | TEXT | |
| `cancelled_at` | TEXT | |

**Índice:** `idx_shopping_list_os_produto` em `(os_id, produto_id, produto_nome)`.

### `shopping_list_logs`

Auditoria de mudanças em itens da lista de compras.

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `id` | INTEGER | PK AUTOINCREMENT |
| `shopping_list_id` | INTEGER | NOT NULL |
| `usuario_id` | INTEGER | quem executou a ação |
| `acao` | TEXT | NOT NULL — ex.: `create`, `update` |
| `valor_anterior` | TEXT | snapshot antes da mudança |
| `valor_novo` | TEXT | snapshot depois da mudança |
| `created_at` | TEXT NOT NULL | `datetime('now')` |

### `os_checklists`

Checklist de diagnóstico do aparelho, acessível publicamente via token (rota
`/checklist/:token` no frontend, sem autenticação — ver `ARCHITECTURE.md` seção 5).

| Coluna | Tipo | Default |
|--------|------|---------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `os_id` | INTEGER NOT NULL UNIQUE | uma checklist por OS |
| `access_token` | TEXT UNIQUE | token de acesso público — **não expira** (ver KI-002) |
| `status_touch` | TEXT NOT NULL | `'nao_testado'` |
| `status_audio` | TEXT NOT NULL | `'nao_testado'` |
| `status_microfone` | TEXT NOT NULL | `'nao_testado'` |
| `status_camera` | TEXT NOT NULL | `'nao_testado'` |
| `status_botoes` | TEXT NOT NULL | `'nao_testado'` |
| `observacoes` | TEXT NOT NULL | `''` |
| `executado_por` | TEXT NOT NULL | `''` |
| `origem` | TEXT NOT NULL | `''` |
| `resultado_json` | TEXT NOT NULL | `'{}'` |
| `criado_em` | TEXT NOT NULL | `''` |
| `atualizado_em` | TEXT NOT NULL | `''` |

### `integracao_sync_estado`

Estado key-value da sincronização com integrações externas (MercadoPhone).

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `chave` | TEXT | PK |
| `valor` | TEXT | |

### `integracao_os_vistas`

Deduplicação de OS já importadas de sistemas externos.

| Coluna | Tipo | Constraint |
|--------|------|------------|
| `origem` | TEXT | NOT NULL, parte da PK composta |
| `id_externo` | TEXT | NOT NULL, parte da PK composta |
| `primeira_visualizacao` | TEXT | |

PK composta `(origem, id_externo)`.

---

## 3. Relacionamentos (lógicos — sem `FOREIGN KEY` declarado no schema)

```
usuarios ──< shopping_list.responsavel_id
usuarios ──< shopping_list_logs.usuario_id

os ──< os_pecas.os_id
os ──< os_checklists.os_id (1:1, UNIQUE)
os ──< compras.os_id
os ──< shopping_list.os_id
os >─< reparos  (via os_reparos, N:N)
os ── reparos.reparo_id (legado, 1:N — ver os_reparos para o modelo atual)

estoque ──< estoque_lotes.estoque_id
estoque ──< os_pecas.estoque_id
estoque ──< movimentacoes.estoque_id
estoque ──< shopping_list.produto_id
```

**Nota:** nenhuma constraint `FOREIGN KEY` é declarada no schema — integridade referencial é mantida
apenas pela lógica da aplicação. Isso é dívida técnica implícita não listada individualmente em
`KNOWN_ISSUES.md`; ao adicionar `FOREIGN KEY` no futuro, documentar como ADR (mudança de schema com
potencial de rejeitar dados legados órfãos).

---

## 4. Isolamento em Testes

- Testes **nunca** usam `database.db`. `tests/conftest.py` define `IR_FLOW_DATA_DIR` como um
  diretório temporário (`tempfile.mkdtemp()`) **antes** de importar `app.py`, já que `DB_PATH` é
  resolvido na carga do módulo.
- `criar_tabelas()` é chamada explicitamente na fixture `app` (escopo `session`) para garantir o
  schema no banco temporário.
- Isso significa que os testes usam SQLite em arquivo (dentro de um diretório temp), não
  `:memory:` — mas o isolamento de `database.db` real está garantido.

---

## 5. Convenções (ver também `ENGINEERING_GUIDE.md` seção 5)

- Tabelas: `snake_case` no plural.
- Colunas: `snake_case`.
- Foreign keys lógicas: `<tabela_singular>_id`.
- Índices: `idx_<tabela>_<coluna(s)>`.
- Datas armazenadas como `TEXT` (não há tipo `DATE`/`DATETIME` nativo usado) — formato observado:
  `YYYY-MM-DD HH:MM:SS` ou `datetime('now')` (UTC, formato SQLite padrão).
