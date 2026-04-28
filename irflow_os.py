from datetime import datetime

from irflow_core import texto_limpo, to_float


def _consumir_lotes_fifo(cursor, estoque_id, quantidade):
    restante = int(quantidade or 0)
    if restante <= 0:
        return

    cursor.execute(
        """
        SELECT id, COALESCE(quantidade_disponivel, 0)
        FROM estoque_lotes
        WHERE estoque_id=? AND COALESCE(quantidade_disponivel, 0) > 0
        ORDER BY COALESCE(data_compra, '') ASC, id ASC
        """,
        (estoque_id,),
    )
    lotes = cursor.fetchall()

    for lote_id, disponivel in lotes:
        if restante <= 0:
            break
        consumir = min(restante, int(disponivel or 0))
        if consumir <= 0:
            continue
        cursor.execute(
            "UPDATE estoque_lotes SET quantidade_disponivel = MAX(0, quantidade_disponivel - ?) WHERE id=?",
            (consumir, lote_id),
        )
        restante -= consumir


def _criar_lote_retorno(cursor, estoque_id, quantidade, valor, fornecedor, observacoes):
    qtd = int(quantidade or 0)
    if qtd <= 0:
        return
    data_ref = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        INSERT INTO estoque_lotes (
            estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            estoque_id,
            fornecedor or "Nao informado",
            float(valor or 0),
            qtd,
            qtd,
            data_ref,
            observacoes or "devolucao",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


def extrair_reparo_ids(formulario):
    valores = formulario.getlist("reparo_ids")
    if not valores:
        valor_unico = (formulario.get("reparo_id") or "").strip()
        if valor_unico:
            valores = [valor_unico]

    ids = []
    vistos = set()
    for valor in valores:
        texto = str(valor or "").strip()
        if not texto:
            continue
        try:
            reparo_id = int(texto)
        except ValueError as exc:
            raise ValueError("Reparo invalido selecionado.") from exc
        if reparo_id in vistos:
            continue
        vistos.add(reparo_id)
        ids.append(reparo_id)
    return ids


def validar_reparo_ids(cursor, reparo_ids):
    if not reparo_ids:
        return False

    placeholders = ",".join("?" for _ in reparo_ids)
    cursor.execute(
        f"SELECT id FROM reparos WHERE id IN ({placeholders})",
        reparo_ids,
    )
    encontrados = {row[0] for row in cursor.fetchall()}
    return len(encontrados) == len(reparo_ids)


def salvar_reparos_os(cursor, os_id, reparo_ids):
    cursor.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
    for reparo_id in reparo_ids:
        cursor.execute(
            "INSERT INTO os_reparos (os_id, reparo_id) VALUES (?, ?)",
            (os_id, reparo_id),
        )
    cursor.execute(
        "UPDATE os SET reparo_id=? WHERE id=?",
        (reparo_ids[0] if reparo_ids else None, os_id),
    )


def obter_ou_criar_reparo(cursor, nome):
    nome_limpo = texto_limpo(nome)
    if not nome_limpo:
        return None

    cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?)", (nome_limpo,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (nome_limpo,))
    return cursor.lastrowid


def obter_reparos_por_os(cursor):
    cursor.execute(
        """
        SELECT
            os_reparos.os_id,
            reparos.id,
            COALESCE(reparos.nome, '')
        FROM os_reparos
        JOIN reparos ON reparos.id = os_reparos.reparo_id
        ORDER BY reparos.nome
        """
    )
    mapa = {}
    for os_id, reparo_id, nome in cursor.fetchall():
        if os_id not in mapa:
            mapa[os_id] = {"ids": [], "nomes": []}
        mapa[os_id]["ids"].append(reparo_id)
        if nome:
            mapa[os_id]["nomes"].append(nome)
    return mapa


def carregar_os_com_relacoes(cursor, order_by="os.id DESC"):
    cursor.execute(
        f"""
        SELECT
            os.id,
            os.tipo,
            os.cliente,
            os.aparelho,
            os.tecnico,
            os.reparo_id,
            os.status,
            COALESCE(os.valor_cobrado, 0),
            COALESCE(os.valor_descontado, 0),
            COALESCE(os.custo_pecas, 0),
            COALESCE(os.data, ''),
            COALESCE(os.observacoes, ''),
            COALESCE(os.modelo, ''),
            COALESCE(os.vendedor, ''),
            COALESCE(os.cor, ''),
            COALESCE(os.imei, ''),
            COALESCE(os.origem_integracao, '')
        FROM os
        ORDER BY {order_by}
        """
    )
    dados = cursor.fetchall()
    reparos_por_os = obter_reparos_por_os(cursor)

    cursor.execute(
        """
        SELECT os_id, COALESCE(SUM(valor), 0)
        FROM os_pecas
        GROUP BY os_id
        """
    )
    custos = {row[0]: row[1] or 0 for row in cursor.fetchall()}
    return dados, reparos_por_os, custos


def registrar_movimentacao(cursor, estoque_id, tipo, quantidade):
    cursor.execute(
        """
        INSERT INTO movimentacoes (estoque_id, tipo, quantidade, data)
        VALUES (?, ?, ?, ?)
        """,
        (estoque_id, tipo, quantidade, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def modelo_compativel(modelo_peca, modelo_os):
    modelo_os_norm = (modelo_os or "").strip().lower()
    if not modelo_os_norm:
        return False

    modelo_peca_norm = (modelo_peca or "").strip().lower()
    if not modelo_peca_norm:
        return True

    tokens = [t.strip() for t in modelo_peca_norm.replace(";", ",").replace("|", ",").replace("/", ",").split(",")]
    tokens = [t for t in tokens if t]
    if not tokens:
        return True

    for token in tokens:
        if token in modelo_os_norm or modelo_os_norm in token:
            return True
    return False


def ler_valores_financeiros_form(formulario):
    valor_cobrado = to_float((formulario.get("valor_cobrado") or "").strip(), 0)
    valor_descontado = to_float((formulario.get("valor_descontado") or "").strip(), 0)
    if valor_cobrado < 0 or valor_descontado < 0:
        raise ValueError("Valores financeiros nao podem ser negativos.")
    return valor_cobrado, valor_descontado


def vendedor_valido(vendedor, vendedores_validos):
    if not vendedor:
        return True
    return vendedor in vendedores_validos


def consumir_peca_da_os(cursor, os_id, estoque_id):
    cursor.execute(
        """
        SELECT quantidade, valor, descricao, fornecedor, modelo
        FROM estoque
        WHERE id=?
        """,
        (estoque_id,),
    )
    result = cursor.fetchone()

    if not result:
        return False, "Peca nao encontrada no estoque."

    estoque_atual, valor_peca, descricao_peca, fornecedor_peca, modelo_peca = result

    if (estoque_atual or 0) <= 0:
        return False, f"Sem estoque para: {descricao_peca or 'peca'}."

    cursor.execute(
        """
        INSERT INTO os_pecas (os_id, estoque_id, quantidade, valor, peca_descricao, peca_fornecedor, peca_modelo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (os_id, estoque_id, 1, valor_peca, descricao_peca, fornecedor_peca, modelo_peca),
    )

    cursor.execute(
        "UPDATE estoque SET quantidade = MAX(0, quantidade - 1) WHERE id = ?",
        (estoque_id,),
    )
    _consumir_lotes_fifo(cursor, estoque_id, 1)
    registrar_movimentacao(cursor, estoque_id, "saida", 1)
    return True, ""


def adicionar_peca_os_sem_consumir(cursor, os_id, estoque_id):
    cursor.execute(
        """
        SELECT quantidade, valor, descricao, fornecedor, modelo
        FROM estoque
        WHERE id=?
        """,
        (estoque_id,),
    )
    result = cursor.fetchone()

    if not result:
        return False, "Peca nao encontrada no estoque."

    estoque_atual, valor_peca, descricao_peca, fornecedor_peca, modelo_peca = result

    if (estoque_atual or 0) <= 0:
        return False, f"Sem estoque para: {descricao_peca or 'peca'}."

    cursor.execute(
        """
        INSERT INTO os_pecas (os_id, estoque_id, quantidade, valor, peca_descricao, peca_fornecedor, peca_modelo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (os_id, estoque_id, 1, valor_peca, descricao_peca, fornecedor_peca, modelo_peca),
    )
    return True, ""


def devolver_pecas_da_os(cursor, os_id, tipo_movimentacao):
    cursor.execute(
        """
        SELECT id, estoque_id, quantidade, valor, peca_descricao, peca_fornecedor, peca_modelo
        FROM os_pecas
        WHERE os_id=?
        """,
        (os_id,),
    )
    pecas = cursor.fetchall()

    for os_peca_id, estoque_id, qtd, valor, descricao, fornecedor, modelo in pecas:
        cursor.execute("SELECT id FROM estoque WHERE id=?", (estoque_id,))
        existe = cursor.fetchone()

        if existe:
            cursor.execute(
                """
                UPDATE estoque
                SET quantidade = quantidade + ?
                WHERE id = ?
                """,
                (qtd, estoque_id),
            )
            _criar_lote_retorno(
                cursor,
                estoque_id,
                qtd,
                valor,
                fornecedor,
                f"retorno {tipo_movimentacao}",
            )
        else:
            cursor.execute(
                """
                INSERT OR REPLACE INTO estoque (
                    id, descricao, valor, fornecedor, quantidade, data_compra, modelo, sku, tipo, qualidade
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    estoque_id,
                    descricao or "Peca devolvida",
                    valor or 0,
                    fornecedor or "Nao informado",
                    qtd or 0,
                    datetime.now().strftime("%Y-%m-%d"),
                    modelo or "",
                    f"RET-{estoque_id:05d}",
                    "Outros",
                    "Padrao",
                ),
            )
            _criar_lote_retorno(
                cursor,
                estoque_id,
                qtd,
                valor,
                fornecedor,
                f"retorno {tipo_movimentacao}",
            )

        registrar_movimentacao(cursor, estoque_id, tipo_movimentacao, qtd or 0)
