"""
irflow_estoque_unidades_service.py

Regra de negócio pura do domínio `estoque_unidades` (rastreamento
individual por IMEI) — não conhece Flask, `request` nem `jsonify`
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Responsabilidade: registrar unidades individuais de itens de estoque que
exigem rastreamento por IMEI (`estoque.requer_imei = 1`) e suas transições
manuais de status. `reservado`/`vendido` existem no schema para o futuro
módulo de Vendas, mas nenhuma função aqui produz ou aceita esses estados —
só `disponivel`, `em_reparo` e `devolvido` são alcançáveis nesta sprint.

Tabelas usadas: `estoque_unidades` (via
`irflow_estoque_unidades_repository.py`), leitura de `estoque.requer_imei`.

Depende de: `irflow_estoque_unidades_repository.py` (SQL), `irflow_audit.py`
(auditoria — create/status_change).
"""

import irflow_estoque_unidades_repository as repo
from irflow_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20

# Estados alcançáveis nesta sprint — 'reservado'/'vendido' ficam de fora até
# o módulo de Vendas existir (nem como origem, nem como destino).
TRANSICOES_VALIDAS = {
    "disponivel": {"em_reparo"},
    "em_reparo": {"disponivel", "devolvido"},
    "devolvido": {"disponivel"},
}


def _unidade_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "estoque_id": row[1],
        "lote_id": row[2],
        "imei": row[3] or "",
        "status": row[4],
        "reservado_por": row[5],
        "reservado_ate": row[6],
        "venda_id": row[7],
        "criado_em": row[8],
        "atualizado_em": row[9],
    }


def listar_unidades(conectar, imei="", estoque_id=None, status="", page=None, per_page=None):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, imei, estoque_id, status)
        rows = repo.buscar_paginado(cursor, imei, estoque_id, status, per_page, offset)
    finally:
        conn.close()

    return {
        "items": [_unidade_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def obter_unidade(conectar, unidade_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, unidade_id)
    finally:
        conn.close()
    return _unidade_para_dict(row)


def criar_unidade(conectar, usuario_id, estoque_id, imei, lote_id=None):
    """Retorna (unidade_id, erro). `erro` é None em caso de sucesso."""
    imei = (imei or "").strip()
    if not estoque_id:
        return None, "estoque_id é obrigatório."
    if not imei:
        return None, "IMEI é obrigatório."

    conn = conectar()
    try:
        cursor = conn.cursor()
        requer_imei = repo.obter_estoque_requer_imei(cursor, estoque_id)
        if requer_imei is None:
            return None, "Item de estoque não encontrado."
        if not requer_imei:
            return None, "Este item de estoque não está marcado para rastreamento por IMEI."

        try:
            unidade_id = repo.inserir(cursor, estoque_id, imei, lote_id)
        except Exception:
            conn.rollback()
            return None, "IMEI já cadastrado."

        registrar_log_auditoria(
            cursor,
            "estoque_unidade",
            unidade_id,
            usuario_id,
            "create",
            depois={"estoque_id": estoque_id, "imei": imei},
        )
        conn.commit()
    finally:
        conn.close()

    return unidade_id, None


def transicionar_status(conectar, usuario_id, unidade_id, novo_status):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, unidade_id)
        if not antes:
            return False, "Unidade não encontrada."

        status_atual = antes[4]
        destinos_validos = TRANSICOES_VALIDAS.get(status_atual, set())
        if novo_status not in destinos_validos:
            return False, f"Transição inválida de '{status_atual}' para '{novo_status}'."

        repo.atualizar_status(cursor, unidade_id, novo_status)
        registrar_log_auditoria(
            cursor,
            "estoque_unidade",
            unidade_id,
            usuario_id,
            "status_change",
            antes=status_atual,
            depois=novo_status,
        )
        conn.commit()
    finally:
        conn.close()

    return True, None
