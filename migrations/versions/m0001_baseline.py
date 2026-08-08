"""
Baseline do schema conhecido em 2026-08-08 (TD-03, Fase 2 Fatia 1).

Cópia verbatim do corpo de app.py::criar_tabelas() (695 linhas, antes da
TD-03) -- DDL original + os 37 ALTER TABLE aditivos + a migração de índice
DROP+CREATE + os 4 blocos de backfill de dados, na mesma ordem física.
Deliberadamente não dividida em migrations menores (decisão do CTO,
SPRINT_TD03_MIGRATIONS_FORMAIS.md seção 6): colapsar os ALTER TABLE nas
colunas finais de cada CREATE TABLE só funcionaria para um banco já 100%
atualizado -- um banco atrasado (produção pode estar até ~10 dias atrás de
main, ver PROJECT_STATUS.md) rodando uma baseline colapsada nunca ganharia
as colunas que faltam. Mantendo o mecanismo idêntico ao de hoje, a baseline
converge corretamente para qualquer estado inicial (vazio, atrasado, ou já
atualizado).

Original em app.py NÃO foi removido nesta fatia -- esta é uma cópia, não uma
mudança de lugar. Ver docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md.
"""

import contextlib
import sqlite3

from fluxoly_reference_data import normalizar_modelo_iphone

ID = "0001"
DESCRICAO = "Baseline do schema conhecido (24 tabelas, 22 índices, 4 blocos de backfill)"


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS reparos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        cliente TEXT,
        aparelho TEXT,
        tecnico TEXT,
        reparo_id INTEGER,
        status TEXT,
        valor_cobrado REAL,
        valor_descontado REAL,
        custo_pecas REAL,
        data TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        valor REAL,
        fornecedor TEXT,
        quantidade INTEGER,
        data_compra TEXT,
        sku TEXT,
        modelo TEXT,
        tipo TEXT,
        qualidade TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS estoque_lotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estoque_id INTEGER NOT NULL,
        fornecedor TEXT,
        valor_compra REAL,
        quantidade INTEGER,
        quantidade_disponivel INTEGER,
        data_compra TEXT,
        observacoes TEXT,
        criado_em TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS os_pecas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        os_id INTEGER,
        estoque_id INTEGER,
        quantidade INTEGER,
        valor REAL
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS os_reparos (
        os_id INTEGER NOT NULL,
        reparo_id INTEGER NOT NULL,
        PRIMARY KEY (os_id, reparo_id)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estoque_id INTEGER,
        tipo TEXT,
        quantidade INTEGER,
        data TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS custos_operacionais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        categoria TEXT,
        valor REAL NOT NULL,
        data TEXT,
        observacoes TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS integracao_sync_estado (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS integracao_os_vistas (
        origem TEXT NOT NULL,
        id_externo TEXT NOT NULL,
        primeira_visualizacao TEXT,
        PRIMARY KEY (origem, id_externo)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto TEXT NOT NULL,
        os_id INTEGER,
        quantidade INTEGER NOT NULL DEFAULT 1,
        status TEXT DEFAULT 'PENDENTE',
        criado_em TEXT DEFAULT '',
        atualizado_em TEXT DEFAULT ''
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        perfil TEXT NOT NULL DEFAULT 'tecnico',
        ativo INTEGER NOT NULL DEFAULT 1
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS os_checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        os_id INTEGER NOT NULL UNIQUE,
        access_token TEXT UNIQUE,
        status_touch TEXT NOT NULL DEFAULT 'nao_testado',
        status_audio TEXT NOT NULL DEFAULT 'nao_testado',
        status_microfone TEXT NOT NULL DEFAULT 'nao_testado',
        status_camera TEXT NOT NULL DEFAULT 'nao_testado',
        status_botoes TEXT NOT NULL DEFAULT 'nao_testado',
        observacoes TEXT NOT NULL DEFAULT '',
        executado_por TEXT NOT NULL DEFAULT '',
        origem TEXT NOT NULL DEFAULT '',
        resultado_json TEXT NOT NULL DEFAULT '{}',
        criado_em TEXT NOT NULL DEFAULT '',
        atualizado_em TEXT NOT NULL DEFAULT ''
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificador TEXT NOT NULL,
        sucesso INTEGER NOT NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_login_attempts_identificador_criado_em
        ON login_attempts (identificador, criado_em)
        """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entidade TEXT NOT NULL,
        entidade_id INTEGER,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        valor_anterior TEXT,
        valor_novo TEXT,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_log_entidade
        ON audit_log (entidade, entidade_id)
        """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        expira_em TEXT NOT NULL,
        usado_em TEXT,
        criado_por INTEGER
    )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_usuario_id
        ON password_reset_tokens (usuario_id)
        """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT,
        email TEXT,
        cpf_cnpj TEXT,
        observacoes TEXT NOT NULL DEFAULT '',
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes (telefone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj ON clientes (cpf_cnpj)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes (nome)")

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS unidades_serializadas (
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
    )
    """
    )

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_estoque_id ON unidades_serializadas (estoque_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_produto_id ON unidades_serializadas (produto_id)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_status ON unidades_serializadas (status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_imei ON unidades_serializadas (imei)")

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT NOT NULL,
        marca TEXT,
        modelo TEXT,
        cor TEXT,
        capacidade TEXT,
        condicao TEXT NOT NULL DEFAULT 'Novo',
        descricao TEXT,
        sku TEXT,
        fornecedor TEXT,
        preco_custo REAL,
        preco_venda REAL NOT NULL,
        quantidade INTEGER NOT NULL DEFAULT 0,
        requer_rastreio_unidade INTEGER NOT NULL DEFAULT 0,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos (categoria)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_sku ON produtos (sku)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos (ativo)")

    # Vendas MVP (docs/product/features/VENDAS.md) — fluxo básico: cliente + aparelho
    # (unidade serializada) + pagamento simples, sem desconto/comissão/garantia/troca
    # (dependem de decisões de negócio ainda pendentes do Product Owner, ver VENDAS.md
    # "O que ainda está em aberto"). status='concluida' é deliberadamente distinto de um
    # futuro conceito de status de pagamento (pago/pendente/estornado) — venda e
    # pagamento são conceitos diferentes, não misturados aqui.
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        vendedor_id INTEGER NOT NULL,
        forma_pagamento TEXT NOT NULL,
        valor_total REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'concluida',
        observacoes TEXT NOT NULL DEFAULT '',
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_cliente_id ON vendas (cliente_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_vendedor_id ON vendas (vendedor_id)")

    # produto_nome/produto_sku/valor_tabela são snapshot no momento da venda (não
    # FK viva) -- preserva o histórico mesmo se o cadastro de produto/estoque mudar
    # depois, mesmo padrão já usado em os_pecas.peca_descricao/peca_fornecedor/
    # peca_modelo. valor_tabela é o preço de catálogo no momento (nullable -- item
    # pode não ter preço cadastrado); valor_unitario é o preço efetivo da venda,
    # pode divergir de valor_tabela (negociação) -- nunca um sobrescreve o outro.
    # unidade_serializada_id é UNIQUE: nunca a mesma unidade em duas vendas -- o
    # verdadeiro guardião contra a corrida de duas vendas simultâneas do mesmo
    # aparelho, no nível do banco, não só na validação da aplicação.
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS vendas_itens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER NOT NULL,
        unidade_serializada_id INTEGER NOT NULL,
        produto_id INTEGER,
        produto_nome TEXT NOT NULL,
        produto_sku TEXT,
        quantidade INTEGER NOT NULL DEFAULT 1,
        valor_tabela REAL,
        valor_unitario REAL NOT NULL,
        subtotal REAL NOT NULL,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_itens_venda_id ON vendas_itens (venda_id)")

    # V1.2 -- Cancelamento (BR-031 a BR-036, VENDAS.md "V1.2 -- Cancelamento"): cancelar uma
    # venda é evento comercial, terminal, sem efeito financeiro (estornada fica para o Épico
    # Financeiro). motivo_cancelamento é lista fechada validada no service, nunca normalizada.
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas ADD COLUMN motivo_cancelamento TEXT")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas ADD COLUMN observacao_cancelamento TEXT")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas ADD COLUMN cancelado_por INTEGER")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas ADD COLUMN cancelado_em TEXT")

    # ativo distingue a venda vigente de uma unidade das suas vendas canceladas no
    # histórico -- permite revenda da mesma unidade_serializada_id sem violar o índice
    # único (BR-033). DEFAULT 1 já backfila as linhas existentes corretamente: toda
    # vendas_itens hoje é uma venda vigente.
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")

    # Substitui o UNIQUE incondicional por um parcial -- só uma linha "ativa" por unidade,
    # não uma por vida inteira. DROP+CREATE é seguro (índice, não dado) e idempotente.
    cursor.execute("DROP INDEX IF EXISTS idx_vendas_itens_unidade_serializada_id")
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_vendas_itens_unidade_ativa "
        "ON vendas_itens (unidade_serializada_id) WHERE ativo = 1"
    )

    # V1.3 -- Descontos e Aprovação (BR-037 a BR-043, VENDAS.md "V1.3 -- Descontos e
    # Aprovação"). Três colunas aditivas, nenhuma tabela nova.
    #
    # limite_desconto_livre: DEPRECADA (2026-07-29, ver VENDAS.md "Revisão do modelo de
    # desconto"). Existiu para BR-037 (limite de desconto sem aprovação, individual por
    # usuário) -- revogada um dia depois de implementada por não refletir o fluxo real de
    # negociação da loja (a venda nunca deveria ter sido bloqueada). Mantida só por
    # compatibilidade histórica com usuários configurados durante a V1.3; nenhum fluxo a
    # partir de 2026-07-29 lê ou escreve esta coluna.
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE usuarios ADD COLUMN limite_desconto_livre REAL")

    # motivo_desconto: opcional, texto livre (BR-039) -- deliberadamente diferente do
    # motivo_cancelamento (lista fechada obrigatória, BR-032). Vive no item, não na
    # venda, porque valor_tabela/valor_unitario já vivem no item. Continua em uso --
    # não afetada pela revisão de 2026-07-29.
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN motivo_desconto TEXT DEFAULT ''")

    # desconto_aprovado_em: DEPRECADA (2026-07-29, ver VENDAS.md "Revisão do modelo de
    # desconto"). Existiu para BR-038 (timestamp de aprovação de desconto acima do
    # limite) -- revogada junto de limite_desconto_livre pelo mesmo motivo. Mantida só
    # por compatibilidade histórica com vendas já feitas na V1.3; nenhum fluxo a partir de
    # 2026-07-29 escreve nesta coluna (permanece sempre NULL para vendas novas).
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN desconto_aprovado_em TEXT")

    # V1.4 -- Comissão (BR-044 a BR-052, VENDAS.md "V1.4 -- Comissão"). Uma coluna
    # aditiva. `comissao_valor`: atribuído manualmente por admin/financeiro, em R$.
    # NULL = "ainda não atribuída" -- nunca confundir com atribuída como zero. Sem
    # campo de "tipo" (fixo/percentual, BR-048): o valor final é sempre o que é
    # gravado, independente de como financeiro chegou nele mentalmente -- é isso que
    # permite a mesma estrutura suportar qualquer política de comissão da loja.
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN comissao_valor REAL")

    # V1.5 -- Garantia (BR-055 a BR-066, VENDAS.md "V1.5 -- Garantia"). Cadastro de
    # política (Tipo de Garantia) separado da instância concedida (Garantia) -- nunca
    # confundir os dois no código. `ativo` permite ao admin aposentar uma política sem
    # apagá-la; nunca afeta garantias já concedidas, que são snapshot (colunas abaixo).
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS tipos_garantia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        duracao_meses INTEGER NOT NULL,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )

    # Garantia de Venda (BR-056/BR-057): atribuída manualmente por item, na criação da
    # venda -- sem default vindo do produto. Snapshot completo (id do tipo, nome,
    # duração, datas) para que uma edição futura em `tipos_garantia` nunca altere uma
    # garantia já concedida. Nullable no schema (compatibilidade com linhas já
    # existentes) -- a obrigatoriedade de BR-056 é imposta pelo service, nunca pelo
    # schema, mesmo padrão já usado no resto do domínio Vendas. Sem FOREIGN KEY real em
    # `tipo_garantia_id`, mesmo padrão do resto do schema (FK lógica).
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN tipo_garantia_id INTEGER")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_nome TEXT")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_duracao_meses INTEGER")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_data_inicio TEXT")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_data_fim TEXT")

    # Garantia de Reparo (BR-061 a BR-063): mesmo conjunto de colunas, mas por linha de
    # reparo (`os_reparos`), não por OS inteira -- uma OS com reparos diferentes pode ter
    # garantias diferentes, cada linha mantém a sua (BR-062). Atribuída na conclusão da
    # OS (`Finalizado`), não na criação -- substitui o prazo fixo de 90 dias hardcoded
    # (`GARANTIA_REPARO_DIAS_PADRAO`, mantida só como fallback para dados históricos sem
    # `tipo_garantia_id`, ver `listar_garantias`).
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_reparos ADD COLUMN tipo_garantia_id INTEGER")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_nome TEXT")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_duracao_meses INTEGER")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_data_inicio TEXT")
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_data_fim TEXT")

    # Add valor column if it doesn't exist
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_pecas ADD COLUMN valor REAL")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_descricao TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_fornecedor TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_modelo TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN data_finalizado TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN modelo TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN cor TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN imei TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN vendedor TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN observacoes TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN origem_integracao TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE os ADD COLUMN id_externo_integracao TEXT")

    # INC-002 (docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md): sem
    # essa restricao, duas OS podiam ser importadas com o mesmo id_externo_integracao
    # (achado: sync do Mercado Phone rodando em mais de um worker do Gunicorn ao mesmo
    # tempo, sem coordenacao). O lock cross-processo (fluxoly_mercadophone.py) corrige o
    # mecanismo mais provavel do bug; este indice e a garantia definitiva no banco,
    # valendo contra qualquer outro caminho futuro de escrita (bug humano, script,
    # nova integracao). SQLite trata cada NULL como distinto em indices UNIQUE, entao
    # OS nativas (origem_integracao/id_externo_integracao ambos NULL) nao sao afetadas.
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_os_origem_id_externo
        ON os (origem_integracao, id_externo_integracao)
        """
    )

    with contextlib.suppress(sqlite3.OperationalError):
        # Aditiva, nullable, sem backfill (CLIENTES.md) -- OS existentes
        # continuam com `cliente` (texto) e nada mais.
        cursor.execute("ALTER TABLE os ADD COLUMN cliente_id INTEGER")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE estoque ADD COLUMN modelo TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE estoque ADD COLUMN sku TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE estoque ADD COLUMN tipo TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("ALTER TABLE estoque ADD COLUMN qualidade TEXT")

    with contextlib.suppress(sqlite3.OperationalError):
        # Flag manual (admin) -- nem todo item de estoque precisa de
        # unidade individual por IMEI (peca de reparo continua agregada).
        cursor.execute("ALTER TABLE estoque ADD COLUMN requer_imei INTEGER NOT NULL DEFAULT 0")

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_estoque_sku
        ON estoque (sku)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_estoque_tripla
        ON estoque (modelo, tipo, qualidade)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_lotes_estoque_id
        ON estoque_lotes (estoque_id)
        """
    )

    # Commit intermediário -- preserva o comportamento original de app.py::criar_tabelas()
    # (o DDL acima ficava visível/committed antes dos backfills de dados abaixo rodarem).
    conn.commit()

    cursor.execute("SELECT id, modelo FROM estoque")
    for item_id, modelo_atual in cursor.fetchall():
        modelo_norm = normalizar_modelo_iphone(modelo_atual)
        if modelo_norm != (modelo_atual or ""):
            cursor.execute("UPDATE estoque SET modelo=? WHERE id=?", (modelo_norm, item_id))

    cursor.execute("SELECT id, COALESCE(sku, '') FROM estoque")
    for item_id, sku_atual in cursor.fetchall():
        if not (sku_atual or "").strip():
            cursor.execute("UPDATE estoque SET sku=? WHERE id=?", (f"ITEM-{item_id}", item_id))

    cursor.execute(
        """
        INSERT INTO estoque_lotes (
            estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
        )
        SELECT
            e.id,
            COALESCE(e.fornecedor, 'Nao informado'),
            COALESCE(e.valor, 0),
            COALESCE(e.quantidade, 0),
            COALESCE(e.quantidade, 0),
            COALESCE(e.data_compra, ''),
            'lote inicial legado',
            datetime('now')
        FROM estoque e
        WHERE NOT EXISTS (
            SELECT 1 FROM estoque_lotes l WHERE l.estoque_id = e.id
        )
        AND COALESCE(e.quantidade, 0) > 0
        """
    )

    cursor.execute("SELECT id, modelo FROM os")
    for os_id, modelo_atual in cursor.fetchall():
        modelo_norm = normalizar_modelo_iphone(modelo_atual)
        if modelo_norm != (modelo_atual or ""):
            cursor.execute("UPDATE os SET modelo=? WHERE id=?", (modelo_norm, os_id))

    cursor.execute(
        """
        INSERT OR IGNORE INTO os_reparos (os_id, reparo_id)
        SELECT id, reparo_id
        FROM os
        WHERE reparo_id IS NOT NULL
        """
    )

    # Shopping list tables
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS shopping_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        os_id INTEGER,
        produto_id INTEGER,
        produto_nome TEXT,
        quantidade_solicitada INTEGER NOT NULL DEFAULT 1,
        quantidade_comprada INTEGER NOT NULL DEFAULT 0,
        quantidade_recebida INTEGER NOT NULL DEFAULT 0,
        prioridade TEXT DEFAULT 'NORMAL',
        status TEXT DEFAULT 'PENDENTE',
        responsavel_id INTEGER,
        observacao TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        purchased_at TEXT,
        received_at TEXT,
        cancelled_at TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS shopping_list_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shopping_list_id INTEGER NOT NULL,
        usuario_id INTEGER,
        acao TEXT NOT NULL,
        valor_anterior TEXT,
        valor_novo TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_shopping_list_os_produto
        ON shopping_list (os_id, produto_id, produto_nome)
        """
    )
