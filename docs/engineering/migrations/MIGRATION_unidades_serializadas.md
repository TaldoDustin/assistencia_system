# Plano Técnico de Migração — `estoque_unidades` → `unidades_serializadas`

**Data:** 2026-07-21
**Status:** ✅ APROVADO pelo usuário (CTO) em 2026-07-21. **Ainda não implementado** — este documento
descreve o plano; a implementação acontece em branch própria, seguindo exatamente o que está aprovado
aqui (ver "Decisões Aprovadas pelo CTO" ao final).
**Implementa:** [ADR-007](../adr/ADR-007.md) — Consolidação de rastreamento por IMEI entre Estoque e Produtos
**Pré-requisito de:** Sprint Comercial 1.3 (Tela IMEI) e Sprint Comercial 2 (Primeira Venda)
**Autor:** Claude (Principal Engineer), a pedido do usuário (CTO). Decisões finais de escopo (seção
"Decisões Aprovadas pelo CTO") definidas pelo usuário (CTO).

> Este documento é o plano aprovado. Nenhuma linha de código, migração ou schema foi alterada ao
> escrevê-lo ou aprová-lo — a implementação é o próximo passo, em branch própria.

---

## 1. Objetivo da migração

**Por que ela existe:** `estoque_unidades` (rastreamento por IMEI) foi desenhada em 2026-07-11, antes de
existir o catálogo comercial `produtos` (criado em 2026-07-20). Ela só enxerga unidades originadas de
`estoque` (peças de assistência) — não cobre o cenário real que motivou a tela de IMEI (buscar um
iPhone de revenda do catálogo `produtos` por IMEI).

**Qual problema resolve:** a ambiguidade "qual tabela representa a unidade física de um aparelho para
revenda?", em aberto desde a nota da Sprint Comercial 0.1 em `docs/product/features/VENDAS.md`
(*"a venda de um iPhone do catálogo comercial não deveria apontar para a tabela de peças de reparo"*).

**Qual ADR ela implementa:** [ADR-007](../adr/ADR-007.md), decisão aceita em 2026-07-21 — `estoque_unidades`
evolui para `unidades_serializadas`, generalizando a origem (`estoque_id` OU `produto_id`, nunca os
dois), com a Regra de Ouro (um IMEI/serial = uma unidade, nunca duplicada entre domínios) e o Princípio
da Responsabilidade de Transição (cada domínio só transiciona os estados que lhe pertencem) fixados como
regra de arquitetura.

**Quais épicos ela desbloqueia:**
- Sprint Comercial 1.3 (Tela IMEI) — hoje pausada, só pode cobrir o cenário completo (produtos +
  estoque) depois desta migração.
- Sprint Comercial 2 (Primeira Venda) — `vendas.estoque_unidade_id` não pode ser implementado sem saber
  onde a unidade vendida vive; ADR-007 exige esta decisão resolvida antes de qualquer código de Vendas.

---

## 2. Impacto arquitetural

Nada fica implícito. Todo arquivo/rota/teste que precisa mudar está listado abaixo, com o estado atual
confirmado no código (não suposição).

### Tabelas

| Tabela | Mudança |
|---|---|
| `estoque_unidades` | Recriada como `unidades_serializadas` (rename + `estoque_id` relaxado para nullable + `produto_id` novo + `saude_bateria`/`localizacao` novos) |
| `estoque` | Não muda (só é referenciada) |
| `produtos` | Não muda (só é referenciada; `requer_rastreio_unidade` já existe desde 2026-07-20 e passa a ser consumido pela primeira vez) |
| `audit_log` | Não muda de schema; valores históricos da coluna `entidade` (`"estoque_unidade"`) **não são reescritos** — decisão aprovada, ver seção 3 |

Schema atual de `estoque_unidades` (`app.py:596-609`), para referência exata:

```sql
CREATE TABLE IF NOT EXISTS estoque_unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estoque_id INTEGER NOT NULL,
    lote_id INTEGER,
    imei TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'disponivel',
    reservado_por INTEGER,
    reservado_ate TEXT,
    venda_id INTEGER,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
)
```
Índices: `idx_estoque_unidades_estoque_id`, `idx_estoque_unidades_status`, `idx_estoque_unidades_imei`.
Nenhuma constraint `FOREIGN KEY` é declarada (convenção do projeto — `estoque_id`/`lote_id` são FKs
lógicas, não de banco).

Schema alvo de `unidades_serializadas`:

```sql
CREATE TABLE IF NOT EXISTS unidades_serializadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estoque_id INTEGER,              -- relaxado para nullable
    produto_id INTEGER,              -- novo
    lote_id INTEGER,
    imei TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'disponivel',
    reservado_por INTEGER,
    reservado_ate TEXT,
    venda_id INTEGER,
    saude_bateria TEXT,              -- novo (aditivo)
    localizacao TEXT,                -- novo (aditivo)
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
)
```
Índices a recriar: `idx_unidades_serializadas_estoque_id`, `idx_unidades_serializadas_produto_id` (novo),
`idx_unidades_serializadas_status`, `idx_unidades_serializadas_imei`.
Invariante "exatamente um de `estoque_id`/`produto_id` preenchido" — validada na camada de serviço, não
via `CHECK` (SQLite não tem `CHECK` condicional prático sem trigger; decisão já registrada no ADR-007).

### `app.py`

- `criar_tabelas()`: bloco `CREATE TABLE estoque_unidades` (linhas 596-619) substituído pelo bloco
  `CREATE TABLE IF NOT EXISTS unidades_serializadas` acima — isso cobre **instalações novas e bancos de
  teste** (que nunca tiveram `estoque_unidades`, então recebem o schema final direto). **Não** cobre o
  banco de produção existente — isso é papel do script de migração (seção 3), que roda uma única vez,
  antes do deploy do `app.py` atualizado.
- Import/registro do blueprint (linha 1609-1611) atualizado para o novo nome de arquivo/módulo (ver
  decisão de rename abaixo — aprovada).

### Repository — `irflow_estoque_unidades_repository.py` (88 linhas)

Todas as 6 ocorrências literais de `estoque_unidades` no SQL precisam virar `unidades_serializadas`.
Funções afetadas:
- `inserir(cursor, estoque_id, imei, lote_id=None)` → precisa aceitar `produto_id` também, com
  `estoque_id` agora opcional.
- `buscar_por_id`, `buscar_paginado`, `contar` → `_COLUNAS` ganha `produto_id`, `saude_bateria`,
  `localizacao`; `buscar_paginado`/`contar` ganham filtro opcional por `produto_id`.
- `atualizar_status` → sem mudança de assinatura.
- `obter_estoque_requer_imei(cursor, estoque_id)` → mantém, e ganha uma função irmã
  `obter_produto_requer_rastreio_unidade(cursor, produto_id)` (`SELECT requer_rastreio_unidade FROM
  produtos WHERE id = ?`), mesmo padrão de leitura cross-tabela já usado hoje.

### Service — `irflow_estoque_unidades_service.py` (151 linhas)

- `criar_unidade(...)` ganha parâmetro `produto_id`, com nova validação: rejeitar (400, não coagir) se
  nem `estoque_id` nem `produto_id` estiverem preenchidos, ou se **ambos** estiverem preenchidos —
  mesma filosofia de "rejeitar em vez de coagir silenciosamente" já aplicada em KI-015/KI-016 e na
  Sprint Comercial 0.1.
- Passa a checar `estoque.requer_imei` OU `produtos.requer_rastreio_unidade`, dependendo de qual FK
  lógica está setada.
- `_unidade_para_dict(row)` — mapeamento posicional (`row[0]`…`row[9]`) precisa de novos índices para as
  3 colunas novas.
- `TRANSICOES_VALIDAS` — sem mudança nesta migração (novos estados ficam fora de escopo, seção 10).

### Controller — `irflow_estoque_unidades_controller.py` (96 linhas)

4 rotas hoje sob `/api/estoque-unidades` (`GET` lista, `GET` por id, `POST` cria, `PATCH` status).
`POST` passa a aceitar `produto_id` no corpo. Nenhuma rota nova é criada — reaproveita as 4 existentes.

### Rename de arquivos Python e da rota da API — aprovado, sem aliases

ADR-007 decidiu renomear a **tabela**. O usuário (CTO) aprovou explicitamente estender o rename aos
**arquivos** e à **rota**, na mesma migração, sem manter compatibilidade retroativa:

- `irflow_estoque_unidades_repository.py` → `irflow_unidades_serializadas_repository.py`
- `irflow_estoque_unidades_service.py` → `irflow_unidades_serializadas_service.py`
- `irflow_estoque_unidades_controller.py` → `irflow_unidades_serializadas_controller.py`
- Blueprint `estoque_unidades_api` → `unidades_serializadas_api`
- Rota `/api/estoque-unidades` → `/api/unidades-serializadas`

**Sem alias de compatibilidade** — não haverá redirect de `/api/estoque-unidades` para a rota nova, nem
reexportação de `irflow_estoque_unidades_service` apontando para o módulo renomeado. Justificativa
(decisão do CTO): não existe frontend consumindo essa rota hoje (confirmado por grep — zero referências
em `frontend/src`) nem cliente externo documentado, então não há custo de compatibilidade a pagar —
esta é uma janela rara para um breaking change limpo, sem carregar código legado. Manter um alias aqui
só adicionaria superfície de manutenção para um caso que nunca vai ocorrer.

### Testes

`tests/test_estoque_unidades.py` (4 classes: `TestListarUnidades`, `TestObterUnidade`,
`TestCriarUnidade`, `TestTransicaoStatus`, ~20 casos) — renomeado para `tests/test_unidades_serializadas.py`
na mesma migração, mais os casos novos da seção 6.

### Documentação

`docs/engineering/DATABASE.md` (schema), `docs/product/BUSINESS_RULES.md` (BR-025/BR-026 citam a
tabela por nome), `docs/product/features/IMEI.md` e `VENDAS.md` (resolver a nota pendente da Sprint
Comercial 0.1), `docs/operations/CHANGELOG.md`, `docs/operations/PROJECT_STATUS.md`,
`docs/engineering/adr/ADR-007.md` (marcar a migração como executada, com data e commit, quando concluída).

---

## 3. Estratégia SQLite

SQLite não permite relaxar uma constraint `NOT NULL` via `ALTER TABLE` — exige recriação da tabela (já
documentado no ADR-007). Estratégia escolhida: **recriar, copiar, validar, trocar** — dentro de uma
única transação, para que uma falha no meio não deixe o banco em estado intermediário.

Dois caminhos de código diferentes, propositalmente:

- **(a) Bancos novos (instalações limpas, fixtures de teste):** `app.py::criar_tabelas()` passa a criar
  `unidades_serializadas` diretamente com o schema final. Não há dado antigo para migrar.
- **(b) Banco de produção existente:** script único e idempotente,
  `scripts/migrate_unidades_serializadas.py`, executado manualmente uma vez, **antes** do deploy do
  `app.py` atualizado (ver ordem exata na seção 8).

Passo a passo do script (b):

```sql
PRAGMA foreign_keys = OFF;         -- não há FKs declaradas, mas mantém o idioma por segurança
BEGIN TRANSACTION;

CREATE TABLE unidades_serializadas_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estoque_id INTEGER,
    produto_id INTEGER,
    lote_id INTEGER,
    imei TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'disponivel',
    reservado_por INTEGER,
    reservado_ate TEXT,
    venda_id INTEGER,
    saude_bateria TEXT,
    localizacao TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO unidades_serializadas_new
    (id, estoque_id, produto_id, lote_id, imei, status, reservado_por, reservado_ate,
     venda_id, saude_bateria, localizacao, criado_em, atualizado_em)
SELECT
    id, estoque_id, NULL, lote_id, imei, status, reservado_por, reservado_ate,
    venda_id, NULL, NULL, criado_em, atualizado_em
FROM estoque_unidades;

-- validação de contagem acontece em Python, entre o INSERT e o DROP (ver abaixo) --

DROP TABLE estoque_unidades;
ALTER TABLE unidades_serializadas_new RENAME TO unidades_serializadas;

CREATE INDEX idx_unidades_serializadas_estoque_id ON unidades_serializadas (estoque_id);
CREATE INDEX idx_unidades_serializadas_produto_id ON unidades_serializadas (produto_id);
CREATE INDEX idx_unidades_serializadas_status ON unidades_serializadas (status);
CREATE INDEX idx_unidades_serializadas_imei ON unidades_serializadas (imei);

COMMIT;
PRAGMA foreign_keys = ON;
```

Pontos que o script Python (não só o SQL) precisa cobrir, dentro da mesma transação lógica:

1. **Contagem antes/depois:** `SELECT COUNT(*) FROM estoque_unidades` antes do `INSERT`, comparar com
   `SELECT COUNT(*) FROM unidades_serializadas_new` depois — se divergir, `ROLLBACK` e abortar antes do
   `DROP TABLE`.
2. **`sqlite_sequence`:** validar após o `RENAME` que `SELECT seq FROM sqlite_sequence WHERE
   name='unidades_serializadas'` corresponde a `MAX(id)` da tabela — SQLite atualiza isso
   automaticamente na maioria dos casos, mas **não confiar sem verificar**: se divergir, corrigir com
   `UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM unidades_serializadas) WHERE
   name='unidades_serializadas'`. Sem essa correção, o próximo `INSERT` sem id explícito poderia colidir
   com um `id` já usado.
3. **`audit_log.entidade` — não é alterado.** Decisão aprovada pelo CTO: entradas antigas de auditoria
   (`entidade = 'estoque_unidade'`, gravadas por `irflow_estoque_unidades_service.py::criar_unidade`/
   `transicionar_status`) permanecem exatamente como estão. Nenhum `UPDATE` roda contra `audit_log`
   nesta migração. A partir do go-live, o código renomeado passa a gravar `entidade =
   'unidade_serializada'` para eventos novos — o histórico convive com os dois valores, documentado em
   `DATABASE.md`. Motivo: auditoria existe para registrar exatamente o que aconteceu no momento em que
   aconteceu; reescrever `entidade` de um evento passado para um nome que não existia naquele momento
   equivaleria a editar um registro de auditoria depois do fato.

Idempotência: o script verifica no início se `unidades_serializadas` já existe E `estoque_unidades` não
existe mais — se sim, não faz nada e sai com sucesso (permite rodar o script mais de uma vez sem efeito
colateral, protege contra reexecução acidental em deploy).

---

## 4. Rollback

**Cenário: falha no meio da migração (ex.: crash depois de copiar 80% dos dados).**
Como todos os passos DDL/DML da seção 3 rodam dentro de uma única transação (`BEGIN`...`COMMIT`), um
crash ou erro em qualquer ponto antes do `COMMIT` faz o SQLite reverter tudo automaticamente na próxima
abertura da conexão — `estoque_unidades` original permanece intacta, `unidades_serializadas_new` nunca
chega a existir de forma persistente. **Não há cenário de perda parcial de dados nesse caminho** — é
tudo ou nada, por construção.

**Cenário: transação commitou, mas a validação pós-migração (contagem, integridade) falha.**
1. Restaurar o backup verificado (seção 8, passo 1) sobre `database.db`.
2. Não prosseguir com o deploy do novo `app.py`.
3. Investigar a causa raiz do dado divergente antes de tentar novamente — nunca re-rodar cegamente.

**Cenário: migração e deploy do novo código concluídos, problema descoberto em produção depois.**
1. Colocar a aplicação em manutenção (parar o processo Gunicorn).
2. Restaurar o backup verificado sobre `database.db`.
3. Reverter o deploy do backend para a tag/commit anterior (antes desta migração).
4. Reiniciar a aplicação, rodar smoke tests da seção 8.
5. Qualquer dado gravado em `unidades_serializadas` **entre o deploy e a reversão** (novas unidades
   criadas via produto, por exemplo) seria perdido nesse rollback — por isso a janela entre "migração
   concluída" e "smoke tests aprovados" deve ser a menor possível, e nenhuma escrita de produção deve ser
   aceita nesse intervalo (ver checklist de deploy, seção 8).

O script de rollback (restaurar backup + reverter deploy) deve ser **escrito e testado em dry-run** —
contra uma cópia real do banco de produção, não um banco de teste sintético — antes de ser usado de
verdade. Isso é um item do checklist de aceite (seção 7), não opcional.

---

## 5. Checklist de Integridade (pré-migração, obrigatório antes de qualquer `DROP TABLE`)

Todas as consultas abaixo rodam contra o banco de produção (ou uma cópia idêntica) antes da migração.
Qualquer resultado inesperado **aborta a migração** — não é coagido nem ignorado.

| # | Verificação | Consulta | Resultado esperado |
|---|---|---|---|
| 1 | IMEI duplicado | `SELECT imei, COUNT(*) FROM estoque_unidades WHERE imei IS NOT NULL GROUP BY imei HAVING COUNT(*) > 1` | 0 linhas (a constraint `UNIQUE` já deveria garantir isso — checagem defensiva) |
| 2 | Unidade sem origem | `SELECT id FROM estoque_unidades WHERE estoque_id IS NULL` | 0 linhas (`estoque_id` é `NOT NULL` hoje — checagem defensiva) |
| 3 | Unidade órfã (estoque inexistente) | `SELECT eu.id FROM estoque_unidades eu LEFT JOIN estoque e ON eu.estoque_id = e.id WHERE e.id IS NULL` | 0 linhas |
| 4 | Lote órfão (se `lote_id` preenchido) | `SELECT id FROM estoque_unidades eu WHERE lote_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM estoque_lotes el WHERE el.id = eu.lote_id)` | 0 linhas |
| 5 | Status fora do domínio conhecido | `SELECT DISTINCT status FROM estoque_unidades WHERE status NOT IN ('disponivel','em_reparo','reservado','vendido','devolvido')` | 0 linhas |
| 6 | Contagem baseline | `SELECT COUNT(*) FROM estoque_unidades` | registrado para comparação pós-migração (seção 3, item 1) |

**Unidade apontando para produto inexistente** — não aplicável antes da migração (`produto_id` ainda não
existe); passa a ser uma invariante de serviço (não de banco) a partir do go-live, coberta pelos testes
da seção 6, não por uma consulta de integridade pré-migração.

**Serial duplicado** — não aplicável hoje: o schema atual só tem `imei`, não existe uma coluna genérica
de "número de série" separada (gap já registrado em `IMEI.md`, fora de escopo desta migração).

---

## 6. Testes obrigatórios

### Unitários

**Repository** (`tests/test_estoque_unidades.py` ou arquivo renomeado):
- `inserir` aceita `produto_id` opcional; `estoque_id` agora opcional.
- `buscar_paginado`/`contar` filtram corretamente por `produto_id`.
- `_COLUNAS` reflete as 3 colunas novas na ordem certa.

**Service:**
- `criar_unidade` rejeita (400) quando `estoque_id` e `produto_id` estão ambos ausentes.
- `criar_unidade` rejeita (400) quando `estoque_id` e `produto_id` estão ambos presentes.
- `criar_unidade` com `produto_id` checa `produtos.requer_rastreio_unidade` (equivalente à checagem
  existente de `estoque.requer_imei`).
- Caminho existente (`estoque_id` apenas) continua funcionando sem regressão — teste de não-regressão
  explícito, não assumido.
- `transicionar_status` sem mudança de comportamento (regressão).

**Validações:** nenhuma mudança esperada em `irflow_validation.py` — confirmar via suíte existente.

### Integração (Flask test client, banco isolado via `IR_FLOW_DATA_DIR`, nunca `database.db`)

- **CRUD:** criar unidade via `estoque_id` (regressão) e via `produto_id` (novo); obter por id; listar
  com paginação.
- **Busca:** filtro combinando `imei` + `produto_id`; `imei` + `estoque_id`.
- **Alteração de estado:** `PATCH .../status` inalterado pelo tipo de origem.
- **Permissões:** `perfil_pode_escrever()` continua bloqueando `vendedor` e permitindo
  `admin`/`tecnico` — reteste explícito, já que o arquivo do controller muda.

### Migração (a categoria nova — banco antigo → migração → banco novo → comparar)

Novo módulo, ex. `tests/test_migration_unidades_serializadas.py`:
1. Fixture cria um SQLite descartável com o **schema antigo** de `estoque_unidades` e semeia linhas
   cobrindo casos de borda: `imei` nulo, `lote_id` nulo e preenchido, todos os `status` válidos,
   `reservado_ate`/`venda_id` nulos e preenchidos.
2. Roda o script de migração de verdade (`scripts/migrate_unidades_serializadas.py`) contra esse
   arquivo.
3. Assert: `unidades_serializadas` existe, `estoque_unidades` não existe mais; contagem de linhas
   idêntica; cada linha original preservada campo a campo (`id`, `estoque_id`, `imei`, `status`,
   `reservado_por`, `reservado_ate`, `venda_id`, `criado_em`, `atualizado_em`); `produto_id`,
   `saude_bateria`, `localizacao` são `NULL` em todas as linhas migradas; os 4 índices existem;
   `sqlite_sequence` permite inserir uma nova linha sem colidir com um `id` existente.
4. **Teste de idempotência:** rodar o script uma segunda vez sobre o banco já migrado — deve ser um
   no-op seguro (sem erro, sem duplicar dados), protegendo contra reexecução acidental em deploy.

---

## 7. Critérios de aceite (gate de merge)

Só pode haver merge/deploy se **todos** os itens abaixo forem verdadeiros:

- [ ] Todos os testes verdes — suíte completa (não só os módulos tocados).
- [ ] Cobertura mantida (gate de CI `fail_under = 40` respeitado; idealmente mantém os ~91-99% já
      medidos hoje nos módulos deste domínio).
- [ ] `ruff check .` sem novos erros.
- [ ] Rollback testado em dry-run contra uma cópia real do banco de produção, com resultado documentado.
- [ ] Auditoria preservada — entradas antigas de `audit_log` continuam consultáveis e corretas, sem
      nenhum `UPDATE` retroativo em `entidade` (decisão aprovada, seção 3).
- [ ] Nenhuma perda de IMEI — contagem/lista de IMEIs antes e depois da migração idêntica.
- [ ] Nenhuma perda de histórico — `criado_em`/`atualizado_em` preservados exatamente, não resetados.
- [ ] Revisão humana linha a linha do script de migração antes de rodar contra produção — é uma operação
      destrutiva de tabela real, testes automatizados não substituem essa leitura.
- [ ] Rename de arquivos/rota aplicado sem nenhum alias de compatibilidade (decisão aprovada, seção 2).

---

## 8. Checklist de Deploy (ordem exata)

1. Backup do `database.db` de produção — cópia + checksum SHA-256 registrado.
2. Restaurar esse backup em ambiente local/staging; rodar a suíte de integridade (seção 5) e o script de
   migração ali **primeiro** — nunca direto em produção.
3. Confirmar suíte de testes completa verde na branch da migração (local/CI).
4. Comunicar janela de manutenção — mesmo curta, dado o volume pequeno de dados hoje; medir o tempo real
   do dry-run do passo 2 para dimensionar a janela.
5. Parar temporariamente escritas de produção (evitar concorrência durante a migração).
6. Rodar `scripts/migrate_unidades_serializadas.py` contra o `database.db` real de produção.
7. Rodar a suíte de verificação pós-migração (contagens, integridade, `sqlite_sequence`) contra o banco
   já migrado — **antes** de subir o novo backend.
8. Deploy do novo código de backend (schema em `app.py`, repository/service/controller atualizados) —
   só depois da migração de dados confirmada no passo 7.
9. Smoke tests em produção: `GET` lista, `GET` unidade existente por `id` antigo (confirma preservação),
   `POST` criação nova em ambos os caminhos (`estoque_id` e `produto_id`), `PATCH` status.
10. Monitorar logs/erros por um período curto após liberar.
11. Atualizar documentação (seção 2 — "Documentação") e marcar `ADR-007.md` como migração executada,
    com data e commit.

---

## 9. Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Falha no meio da migração corrompe dados de produção | Crítico | Migração inteira em uma única transação SQLite (tudo ou nada); backup verificado; dry-run obrigatório antes do deploy real |
| `sqlite_sequence` desalinhado após copiar IDs explícitos, causando colisão de PK em inserts futuros | Alto | Passo explícito de verificação/correção incluído no script; teste de migração cobre "insert após migração" |
| Downtime maior que o esperado na janela de manutenção | Médio | Banco pequeno hoje; dry-run mede o tempo real antes do deploy real |
| Renomear arquivos Python quebra imports não previstos | Médio | Grep completo por `estoque_unidades_controller\|_service\|_repository` antes do rename; CI (ruff + pytest) pega qualquer import quebrado |
| Rota `/api/estoque-unidades` renomeada sem alias quebra algum consumidor não documentado | Baixo | Confirmado zero referências em `frontend/src`; nenhuma integração externa documentada usa essa rota; decisão deliberada do CTO de não manter alias |
| `audit_log.entidade` com valores mistos (antigo + novo) confunde consulta futura | Baixo | Documentado explicitamente em `DATABASE.md` — decisão deliberada de não reescrever histórico |
| Invariante "exatamente um de `estoque_id`/`produto_id`" não é reforçada pelo banco (sem `CHECK`), podendo ser violada por acesso direto fora da service layer | Médio | Trade-off já aceito no ADR-007; script de auditoria periódica é uma evolução futura possível, fora de escopo agora |

---

## 10. Fora do escopo

Explicitamente **não** entra nesta migração (evita o "já que estamos mexendo..." que faz o escopo
explodir):

- Módulo de Vendas — nenhuma tabela/rota de Vendas criada ou modificada.
- Tela IMEI / Sprint Comercial 1.3 — esta migração é pré-requisito dela, não parte dela; nenhum
  frontend é tocado.
- Novos estados de ciclo de vida (`em_garantia`, `troca`, `descartado`) — deferidos, conforme ADR-007.
- Garantias, Trocas, RMA — nenhuma lógica de negócio desses domínios é implementada.
- Dashboard ou qualquer relatório consumindo `unidades_serializadas`.
- Validação de formato de IMEI (15 dígitos / checksum Luhn) — gap já registrado em `IMEI.md`, não
  resolvido aqui.
- Campo genérico de identificador para itens sem IMEI (AirPods/acessórios) — decisão de produto
  pendente, não parte desta migração.
- Comportamento de `reservado_ate` (timeout de reserva) — inalterado.
- "Origem da transição" (rastreio de pedido/OS/venda por trás de cada mudança de estado) — anotado como
  evolução futura no ADR-007, não implementado aqui.

---

## Decisões Aprovadas pelo CTO

Registrado aqui para que ninguém precise reler a conversa ou a ADR daqui a um ano para saber o que foi
efetivamente decidido (aprovado em 2026-07-21):

- ✅ Renomear a tabela `estoque_unidades` → `unidades_serializadas` na mesma migração (ADR-007).
- ✅ Renomear os 3 arquivos Python (`_repository`/`_service`/`_controller`) na mesma migração.
- ✅ Renomear o endpoint `/api/estoque-unidades` → `/api/unidades-serializadas` na mesma migração.
- ✅ Não alterar registros antigos de `audit_log` — histórico permanece com `entidade =
  'estoque_unidade'`; só eventos novos usam `'unidade_serializada'`.
- ✅ Não manter nenhum alias de compatibilidade (nem de rota, nem de import) — breaking change limpo,
  justificado por zero consumidores hoje (frontend e integrações externas).
- ✅ Migração única — rename + generalização de origem (`produto_id`) + campos aditivos
  (`saude_bateria`/`localizacao`) tudo na mesma transação, não em etapas separadas.

Com isso, este plano está **fechado para discussão de arquitetura**. Qualquer desvio das decisões acima
durante a implementação deve voltar a este documento para atualização explícita, não ser decidido
silenciosamente no código.

---

## Documentos relacionados

- [`ADR-007`](../adr/ADR-007.md) — decisão de arquitetura que este plano implementa
- `docs/product/features/VENDAS.md` — nota pendente que este plano resolve
- `docs/product/features/IMEI.md` — spec original, gaps citados na seção 10
- `docs/product/BUSINESS_RULES.md` — BR-025, BR-026 (regras afetadas pelo rename de tabela)
- `docs/engineering/DATABASE.md` — convenção de migração aditiva, que não cobre este caso (rebuild de tabela)
