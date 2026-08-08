# SPRINT TD-03 — Migrations Formais

**Status:** EM ANDAMENTO (Phase 1 aprovada em 2026-08-08 — Phase 2 Fatia 1 é o próximo passo)
**Início:** 2026-08-08
**Tipo:** Refatoração (arquitetura)

---

## Objetivo

Substituir o mecanismo ad-hoc de schema (`app.py::criar_tabelas()`, 695 linhas de `CREATE TABLE`/
`ALTER TABLE`/`CREATE INDEX` idempotentes, sem versionamento) por um sistema formal de migrations
Python, sem redesenhar o schema em si e sem reescrever o histórico de mudanças já aplicadas.

## Motivação

KI-004 (`docs/operations/KNOWN_ISSUES.md`): "sistema de migrations usa `ALTER TABLE` com `try/except`
ad-hoc em `app.py`. Não há versionamento formal do schema... Impossível determinar o estado exato do
schema em diferentes ambientes sem inspecionar o banco diretamente." TD-03 é o item de dívida técnica
que resolve KI-004 — registrado desde a Sprint 4 original (nunca executada), reavaliado agora que TD-01
e TD-02 já fecharam os outros dois itens estruturais de `app.py` (decomposição de blueprints e bootstrap).
A TD-02 (Phase 1, seção 3) já havia deixado esse bloco deliberadamente fora de escopo, para não confundir
"organizar o bootstrap" com "redesenhar o mecanismo de schema" — essa fronteira é respeitada aqui.

## Método

Mesmas quatro fases da TD-01/TD-02, mesmo compromisso — nenhuma migration criada nem código alterado
antes da Phase 1 estar aprovada:

```
Phase 0 — Architecture Discovery   (concluída, 2026-08-08)
Phase 1 — Architecture Design      (concluída/aprovada, 2026-08-08)
Phase 2 — Incremental Extraction   (Fatia 1: mecanismo novo + rede de segurança;
                                     Fatia 2: remoção da rede de segurança)
Phase 3 — Cleanup                  (se sobrar algo, avaliar ao final da Phase 2)
```

---

## Phase 0 — Architecture Discovery (concluída em 2026-08-08)

**Método:** leitura completa de `app.py::criar_tabelas()`/`forcar_migracao_schema()`/`criar_admin_padrao()`
+ `grep` determinístico (não estimativa), mesma disciplina da TD-01/TD-02.

### Estado atual e tamanho real do bloco

| Função | Linhas | Observação |
|---|---|---|
| `criar_tabelas()` | `app.py:476-1170` | **695 linhas**, 30% do `app.py` pós-TD-02 (1.749 linhas) |
| `forcar_migracao_schema()` | `app.py:1173-1177` | Reset de `SCHEMA_READY` + rechamada de `criar_tabelas()` |
| `criar_admin_padrao()` | `app.py:1192-1209` | Seed de dado (usuário admin), não é migração — fora de escopo |

Confirmado por grep: **24** `CREATE TABLE IF NOT EXISTS`, **37** `ALTER TABLE` (todos em
`contextlib.suppress(sqlite3.OperationalError)`), **22** `CREATE INDEX`/`CREATE UNIQUE INDEX`, **1**
`DROP INDEX` (troca de índice único incondicional por parcial, V1.2 Vendas). **Zero** mecanismo de
versionamento existente — nenhum `PRAGMA user_version`, nenhuma tabela `schema_version`.

### Achado central: `criar_tabelas()` roda em toda chamada a `conectar()`

```python
def conectar():
    criar_tabelas()          # toda conexão passa por aqui
    conn = sqlite3.connect(DB_PATH, ...)
    ...
```

Mitigado por guard de dupla checagem (`SCHEMA_READY` + `SCHEMA_LOCK`, double-checked locking) — custo real
após a primeira execução por processo é um `bool` check. Ainda assim, é um acoplamento arquitetural real
entre a camada de conexão (bloco F) e a camada de schema (bloco G) que a Phase 1 decidiu romper
deliberadamente (ver seção "Transição", abaixo).

### Ordem física de execução dentro de `criar_tabelas()` (9 blocos)

1. 17 `CREATE TABLE` "base" (schema mínimo original, sem colunas aditivas).
2. 3 `CREATE TABLE` de domínios comerciais (`unidades_serializadas`, `produtos`, `vendas`/`vendas_itens`).
3. Cascata de `ALTER TABLE` do Épico Vendas (V1.2 → V1.3 → V1.4 → V1.5, ordem cronológica de sprint).
   Inclui 2 colunas hoje deprecadas mas nunca removidas (`usuarios.limite_desconto_livre`,
   `vendas_itens.desconto_aprovado_em`).
4. Migração de índice via `DROP INDEX` + `CREATE UNIQUE INDEX` — único ponto "substituir", não "adicionar".
5. `tipos_garantia` + 10 `ALTER TABLE` de Garantia (espelhadas em `vendas_itens` e `os_reparos`).
6. 19 `ALTER TABLE` de OS/Estoque legados + `UNIQUE INDEX idx_os_origem_id_externo` (INC-002) + 3 índices
   de Estoque.
7. Primeiro `conn.commit()` + **migração de dados (DML, não só DDL)**: normalização de `estoque.modelo`/
   `os.modelo`, backfill de `estoque.sku`, backfill de `estoque_lotes`, backfill de `os_reparos` a partir
   do FK legado `os.reparo_id`.
8. Shopping List (2 tabelas + 1 índice, sem `ALTER TABLE`).
9. `conn.commit()` final + `SCHEMA_READY = True`.

### Precedente já validado no próprio repositório

`scripts/migrate_unidades_serializadas.py` (168 linhas) — migração estrutural não-aditiva (recriar tabela:
`CREATE` → copiar dado → `DROP` → `RENAME`, ADR-007), fora de `criar_tabelas()`, com checagem de
idempotência própria (`ja_migrado()`) e suíte de teste dedicada
(`tests/test_migration_unidades_serializadas.py`, 6 testes). Evidência concreta de que o time já resolveu
esse problema uma vez, informando o design da Phase 1.

### Riscos identificados

- Nenhum ambiente sabe "em que versão de schema está" sem inspecionar o banco.
- Migração de dados (bloco 7) misturada com DDL.
- Guard `SCHEMA_READY`/`SCHEMA_LOCK` é por processo — corrida entre workers Gunicorn mitigada hoje por
  `except OperationalError, "locked" → retorno silencioso`.
- **Produção pode estar atrasada em relação a `main`** (já documentado em `PROJECT_STATUS.md` — RC de
  `unidades_serializadas`, 2026-07-21, achou produção ~10 dias atrás). Risco central que guiou a decisão
  da baseline (ver Phase 1).
- Duas colunas deprecadas nunca removidas — risco de "aproveitar" a migração de mecanismo para limpar,
  misturando cleanup com mudança estrutural.

### Cobertura de testes e lacunas

`criar_tabelas()` não tem teste dedicado — exercitada indiretamente por toda a suíte via fixture `app`
(`tests/conftest.py`). Um caso de comportamento de schema tem teste real
(`tests/test_inc002_unique_index_os_mercado_phone.py`, verifica a `UNIQUE INDEX` de INC-002 a nível de
banco). Lacunas: nenhum teste de idempotência do bloco inteiro (só de uma tabela isolada, indiretamente);
nenhum teste do caminho `except OperationalError "locked"`.

### Impacto em `app.py`, blueprints e services

Único consumidor externo de `forcar_migracao_schema()`: `api_backup.py` (fluxo de restauração de backup,
via `deps["forcar_migracao_schema"]`, já presente em `RuntimeDeps` desde a TD-02 Fatia 3). Nenhum outro
blueprint/service chama `criar_tabelas()`/`forcar_migracao_schema()` diretamente — todos passam por
`conectar()`.

### Opções arquiteturais levantadas

| Opção | Descrição |
|---|---|
| A — Arquivos SQL numerados | `migrations/001_initial_schema.sql`, controle via `schema_migrations` |
| B — Alembic (ou equivalente) | Dependência externa, pensada para SQLAlchemy — projeto usa `sqlite3` puro |
| **C — Registry Python de migrations** | Formaliza o padrão já validado em `scripts/migrate_unidades_serializadas.py` |
| D — Manter aditivo, só versionar | Menor mudança, não resolve o caso "substituir" nem separa DDL/DML |

### Definition of Done da Phase 0

- [x] Inventário completo de `criar_tabelas()` (tabelas, colunas aditivas, índices), por grep determinístico
- [x] Mapa de dependências e ordem de execução
- [x] Riscos de uma migração formal levantados
- [x] Cobertura de testes atual e lacunas identificadas
- [x] Impacto em `app.py`/blueprints/services mapeado
- [x] Relação com KI-004 confirmada
- [x] Opções arquiteturais A/B/C/D levantadas, sem escolha nesta fase
- [x] Aprovação do usuário (CTO) para avançar para a Phase 1, com Opção C como candidata principal

---

## Phase 1 — Architecture Design (aprovada em 2026-08-08)

**Opção escolhida: C — Registry Python de migrations.** Justificativa do CTO: o projeto usa `sqlite3`
diretamente (Alembic adicionaria uma camada inexistente hoje); há precedente real e testado
(`scripts/migrate_unidades_serializadas.py`); permite DDL+DML quando inseparáveis; permite migrations
não-aditivas; facilita teste unitário por migration; sem dependência externa nova; mantém o controle
explícito já buscado nas TDs anteriores.

### 1. Estrutura de diretórios

```
migrations/
├── __init__.py
├── runner.py                    # run_migrations(conn=None) -- orquestra tudo
├── registry.py                  # lista explícita, ordenada, das migrations
└── versions/
    ├── __init__.py
    ├── m0001_baseline.py         # = criar_tabelas() de hoje, movida verbatim
    └── (m0002_<slug>.py quando a próxima mudança real de schema acontecer)
```

`migrations/` como pacote top-level (não `fluxoly_migrations.py`) — mesmo raciocínio já usado para
`fluxoly_blueprint_registry.py` na TD-02 (módulo de composição, não domínio de negócio), mas aqui cresce
por natureza (uma versão por mudança futura), pedindo pacote com submódulo `versions/`. É exatamente o que
`ROADMAP.md` original já antecipava, adaptado de SQL cru para Python.

### 2. Tabela de controle

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    id TEXT PRIMARY KEY,
    aplicada_em TEXT NOT NULL DEFAULT (datetime('now'))
)
```

Deliberadamente mínima (KISS) — sem coluna de checksum/hash nesta Phase 1. Detecção de drift de conteúdo
de uma migration já aplicada não é um problema que a TD-03 precisa resolver agora.

### 3. Contrato de cada migration

Módulo Python simples, sem classe, sem decorator — mesmo estilo funcional do resto do projeto:

```python
# migrations/versions/m0001_baseline.py
"""Baseline do schema conhecido em 2026-08-08 (TD-03) -- verbatim de
app.py::criar_tabelas() antes da TD-03."""

ID = "0001"
DESCRICAO = "Baseline do schema conhecido (24 tabelas, 22 índices, 4 blocos de backfill)"


def apply(cursor) -> None:
    cursor.execute("CREATE TABLE IF NOT EXISTS reparos (...)")
    ...  # as 695 linhas atuais, organizadas pelos mesmos 9 blocos da Discovery
```

Contrato: `ID` (string zero-padded), `DESCRICAO` (texto livre), `apply(cursor)` (obrigatório).

### 4. Registry — explícito, sem descoberta automática

```python
# migrations/registry.py
from migrations.versions import m0001_baseline

MIGRATIONS = [
    m0001_baseline,
    # nova migration entra no fim da lista, nunca no meio
]
```

Mesma decisão deliberada da TD-02: lista explícita, sem `importlib`/reflexão sobre `versions/`.

### 5. Runner

```python
# migrations/runner.py
import sqlite3

from fluxoly_config import DB_PATH
from migrations.registry import MIGRATIONS


def run_migrations(conn: sqlite3.Connection | None = None) -> list[str]:
    """Aplica migrations pendentes em ordem. Idempotente -- seguro em banco
    vazio, atrasado, ou já atualizado. conn=None abre conexão própria contra
    DB_PATH (mesmo padrão de criar_tabelas() hoje); conn explícito existe só
    para testes (:memory:/tmp)."""
    conn_propria = conn is None
    if conn_propria:
        conn = sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT_SECONDS)
        _configurar_conexao_sqlite(conn, habilitar_wal=True)

    try:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(id TEXT PRIMARY KEY, aplicada_em TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        conn.commit()

        cursor.execute("SELECT id FROM schema_migrations")
        aplicadas = {row[0] for row in cursor.fetchall()}

        executadas = []
        for modulo in MIGRATIONS:
            if modulo.ID in aplicadas:
                continue
            modulo.apply(cursor)
            cursor.execute("INSERT INTO schema_migrations (id) VALUES (?)", (modulo.ID,))
            conn.commit()
            executadas.append(modulo.ID)
        return executadas
    except sqlite3.OperationalError as exc:
        if "locked" in str(exc).lower():
            return []  # outro worker migrando agora -- mesmo padrão de hoje
        raise
    finally:
        if conn_propria:
            conn.close()
```

Preserva **exatamente** o tratamento de erro já existente em `criar_tabelas()`
(`except OperationalError, "locked" in str(exc) → return silencioso`), só reposicionado para envolver o
loop inteiro em vez de uma função monolítica — nenhuma garantia de concorrência entre workers Gunicorn é
adicionada nem removida.

### 6. Baseline — decisão central desta Phase 1

`0001_baseline` **não** é uma versão resumida do schema final — são as **695 linhas de hoje, verbatim**,
incluindo os 37 `ALTER TABLE` originais (não colapsados nas colunas finais de cada `CREATE TABLE`).

**Por quê:** colapsar os `ALTER TABLE` nas colunas finais só funcionaria para um banco já 100%
atualizado. Um banco de produção atrasado (ex.: sem colunas da V1.5 ainda) rodando uma baseline colapsada
teria `CREATE TABLE IF NOT EXISTS` como no-op (tabela já existe) e nunca ganharia as colunas que faltam —
dado perdido silenciosamente. Mantendo a baseline idêntica em efeito ao mecanismo de hoje, ela converge
corretamente para **qualquer** estado inicial (vazio, atrasado, ou já atualizado) — mesma garantia que
`criar_tabelas()` já tem em produção há meses. **Nenhum procedimento manual de "adoção" é necessário**:
rodar `run_migrations()` pela primeira vez em qualquer banco converge e registra
`schema_migrations = ["0001"]`.

Consequência direta: a TD-03 não reescreve as 37 mudanças históricas como 37 migrations artificiais — vira
1 migration que é o próprio mecanismo atual, preservado. Migrations novas (`0002` em diante) só tratam de
mudanças reais, daqui para frente.

### 7. Separação DDL/DML

`0001_baseline` mantém DDL e os 4 blocos de backfill juntos, exatamente como estão hoje — separá-los
agora seria reescrever comportamento, não só reorganizar código.

**Convenção para migrations novas (`0002` em diante): preferir separar DDL de backfill quando forem
independentes; não obrigar quando forem inseparáveis.** Sem regra artificial do tipo "toda alteração de
coluna precisa de duas migrations" — se a mudança estrutural e o backfill formam uma unidade lógica
única, ficam juntas num só arquivo.

### 8. Migrations não-aditivas

O caso `DROP INDEX` + `CREATE UNIQUE INDEX` de hoje entra na baseline sem mudança (já idempotente/seguro).
Para uma futura migration genuinamente não-aditiva (recriar tabela), o padrão formalizado é o já validado
em `scripts/migrate_unidades_serializadas.py`: `CREATE` tabela nova → copiar dado → `DROP` tabela antiga →
`RENAME`, com checagem de idempotência própria dentro do `apply()`. O script permanece como referência,
não é migrado para dentro de `migrations/` nesta sprint.

### 9. `api_backup.py`/`forcar_migracao_schema()` — zero mudança de contrato

```python
def forcar_migracao_schema() -> None:
    """Reexecuta migrations pendentes no banco atual (útil após restore de
    arquivo legado ou atrasado)."""
    run_migrations()
```

`api_backup.py` não muda nenhuma linha — `deps["forcar_migracao_schema"]` continua sendo uma função de
zero argumentos com o mesmo nome. Um backup restaurado sem `schema_migrations` (arquivo anterior à TD-03)
converge normalmente: a tabela de controle é criada, `0001` roda (idempotente e seguro mesmo que o backup
já tenha a maior parte do schema), o banco fica atualizado.

### 10. Rollback — **APROVADO: roll-forward only**

Nenhuma migration exige `rollback(cursor)` no contrato. Se uma migration precisar ser desfeita, a prática
é escrever uma **nova** migration (N+1) que reverte o efeito da anterior — nunca editar ou remover o
arquivo já registrado em `schema_migrations` (histórico de migrations imutável, mesmo espírito de "nunca
apagar entradas do `KNOWN_ISSUES.md`"). Decisão do CTO: evita criar falsa sensação de rollback seguro em
SQLite (suporte a `DROP COLUMN` é inconsistente entre versões) e mantém o hábito real do time — colunas
deprecadas já nunca foram removidas mesmo tendo oportunidade (`limite_desconto_livre`,
`desconto_aprovado_em`).

### 11. Transição de `criar_tabelas()` — **APROVADO: 2 fatias**

**Hoje:**
```
import app.py
 └─ conectar() [qualquer chamador]
      └─ criar_tabelas()  [695 linhas: DDL + backfill + guard SCHEMA_READY]
           └─ sqlite3.connect() [conexão dedicada, WAL]
 └─ (nível de módulo) criar_tabelas() explícito
      criar_admin_padrao()
```

**Fatia 1 — introdução, com rede de segurança em `conectar()`:**
```
import app.py
 ├─ (nível de módulo) run_migrations()   ← substitui a chamada a criar_tabelas()
 ├─ criar_admin_padrao()                  ← inalterado
 └─ conectar() [qualquer chamador]
      ├─ run_migrations()  ← rede de segurança: idempotente via schema_migrations
      └─ sqlite3.connect() [devolvida ao chamador]
```

**Fatia 2 — estado final, só depois da Fatia 1 validada e documentada em produção:**
```
import app.py
 ├─ (nível de módulo) run_migrations()
 ├─ criar_admin_padrao()
 └─ conectar() [qualquer chamador]
      └─ sqlite3.connect() [pura -- run_migrations() removida daqui]
```

**Regra explícita:** `criar_tabelas()`/`SCHEMA_READY`/`SCHEMA_LOCK` **não são removidos de `app.py` até a
Fatia 1 estar validada e documentada**. A remoção acontece só na Fatia 2, nunca junto da introdução do
mecanismo novo.

### 12. Testes novos obrigatórios (Fatia 1)

- `run_migrations()` contra banco vazio → confirma as 24 tabelas/22 índices existem.
- `run_migrations()` duas vezes seguidas → resultado idêntico, sem erro (idempotência do runner inteiro,
  lacuna identificada na Phase 0).
- `schema_migrations` fica com exatamente `["0001"]` após a primeira execução.
- Banco "atrasado" simulado (colunas `ALTER` ausentes) → baseline completa corretamente (prova direta da
  decisão da seção 6).
- Ordem de execução do registry nunca invertida, mesmo que a lista `MIGRATIONS` seja reordenada por
  engano.
- Caminho `except OperationalError "locked" → retorna silenciosamente` (lacuna identificada na Phase 0,
  sem cobertura hoje).
- `forcar_migracao_schema()`/restore de backup continuam funcionando ponta a ponta — estender a cobertura
  existente de `api_backup.py`, confirmar nome exato do arquivo de teste atual antes da implementação.

---

## Decisões fechadas da Phase 1

| Decisão | Status |
|---|---|
| Registry Python de migrations (Opção C) | ✅ Aprovado |
| `migrations/versions/` (pacote) | ✅ Aprovado |
| Registry explícito, sem reflexão/auto-discovery | ✅ Aprovado |
| Tabela `schema_migrations` | ✅ Aprovado |
| `0001_baseline` preservando o comportamento verbatim de hoje | ✅ Aprovado |
| Roll-forward only (sem `rollback()` no contrato) | ✅ Aprovado |
| Transição em 2 fatias (rede de segurança em `conectar()` até validação) | ✅ Aprovado |
| DDL/DML preferencialmente separados, sem regra rígida | ✅ Aprovado |

**Fora de escopo, explicitamente rejeitado nesta Phase 1:**

| Item | Status |
|---|---|
| Alembic ou qualquer dependência externa de migrations | ❌ Rejeitado |
| Reescrever o histórico em dezenas de migrations artificiais | ❌ Rejeitado |
| Alterar regras de negócio do schema durante a migração de mecanismo | ❌ Rejeitado |

### Definition of Done da Phase 1

- [x] Estrutura de diretórios definida (`migrations/registry.py`, `migrations/runner.py`,
      `migrations/versions/`)
- [x] Formato/contrato de cada migration definido (`ID`, `DESCRICAO`, `apply(cursor)`)
- [x] Registry e ordem de execução definidos (lista explícita, sem reflexão)
- [x] Estratégia de baseline para produção potencialmente atrasada definida e justificada
- [x] Separação DDL/DML resolvida (preferencial, não obrigatória)
- [x] Tratamento de migrations não-aditivas resolvido (precedente `scripts/migrate_unidades_serializadas.py`)
- [x] Caso `DROP INDEX`/`CREATE INDEX` existente resolvido (entra na baseline sem mudança)
- [x] Proteção contra concorrência entre workers preservada (mesmo padrão de hoje, reposicionado)
- [x] Impacto em `api_backup.py`/`forcar_migracao_schema()` resolvido (zero mudança de contrato)
- [x] Estratégia de rollback definida e aprovada (roll-forward only)
- [x] Transição de `criar_tabelas()` definida e aprovada (2 fatias, rede de segurança até validação)
- [x] Testes novos obrigatórios da Fatia 1 listados
- [x] Aprovação do CTO para iniciar a Phase 2 (Fatia 1) — 2026-08-08, com as 3 decisões acima fechadas
