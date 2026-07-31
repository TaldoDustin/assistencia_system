"""
fluxoly_clientes_service.py

Regra de negócio pura do domínio Clientes — não conhece Flask, `request`
nem `jsonify` (`docs/engineering/ENGINEERING_GUIDE.md` §3.1). Primeira
aplicação real da convenção controller → service → repository neste
projeto.

Responsabilidade: entidade Cliente — cadastro mínimo viável (nome +
telefone ou e-mail), busca/paginação, e a regra de que um cliente com
histórico (OS vinculada) não pode ser excluído.

Tabelas usadas: `clientes` (via `fluxoly_clientes_repository.py`), leitura
de `os.cliente_id` para checar histórico antes de excluir.

Depende de: `fluxoly_clientes_repository.py` (SQL), `fluxoly_audit.py`
(auditoria — create/update/delete).
"""

import fluxoly_clientes_repository as repo
from fluxoly_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20


def _cliente_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "nome": row[1],
        "telefone": row[2] or "",
        "email": row[3] or "",
        "cpf_cnpj": row[4] or "",
        "observacoes": row[5] or "",
        "criado_em": row[6],
        "atualizado_em": row[7],
    }


def listar_clientes(conectar, termo="", page=None, per_page=None):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, termo)
        rows = repo.buscar_paginado(cursor, termo, per_page, offset)
    finally:
        conn.close()

    return {
        "items": [_cliente_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def obter_cliente(conectar, cliente_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, cliente_id)
    finally:
        conn.close()
    return _cliente_para_dict(row)


def criar_cliente(conectar, usuario_id, nome, telefone="", email="", cpf_cnpj="", observacoes=""):
    """
    Retorna (cliente_id, erro). `erro` é None em caso de sucesso.

    Regra de cadastro mínimo viável (CLIENTES.md): nome obrigatório, e ao
    menos um contato (telefone OU e-mail) — sem isso o cliente não pode ser
    reencontrado depois.
    """
    nome = (nome or "").strip()
    telefone = (telefone or "").strip()
    email = (email or "").strip()
    cpf_cnpj = (cpf_cnpj or "").strip()
    observacoes = (observacoes or "").strip()

    if not nome:
        return None, "Nome é obrigatório."
    if not telefone and not email:
        return None, "Informe ao menos um contato (telefone ou e-mail)."

    conn = conectar()
    try:
        cursor = conn.cursor()
        cliente_id = repo.inserir(cursor, nome, telefone, email, cpf_cnpj, observacoes)
        registrar_log_auditoria(
            cursor,
            "cliente",
            cliente_id,
            usuario_id,
            "create",
            depois={"nome": nome, "telefone": telefone, "email": email, "cpf_cnpj": cpf_cnpj},
        )
        conn.commit()
    finally:
        conn.close()

    return cliente_id, None


def atualizar_cliente(conectar, usuario_id, cliente_id, nome, telefone="", email="", cpf_cnpj="", observacoes=""):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    nome = (nome or "").strip()
    telefone = (telefone or "").strip()
    email = (email or "").strip()
    cpf_cnpj = (cpf_cnpj or "").strip()
    observacoes = (observacoes or "").strip()

    if not nome:
        return False, "Nome é obrigatório."
    if not telefone and not email:
        return False, "Informe ao menos um contato (telefone ou e-mail)."

    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, cliente_id)
        if not antes:
            return False, "Cliente não encontrado."

        repo.atualizar(cursor, cliente_id, nome, telefone, email, cpf_cnpj, observacoes)
        registrar_log_auditoria(
            cursor,
            "cliente",
            cliente_id,
            usuario_id,
            "update",
            antes=_cliente_para_dict(antes),
            depois={"nome": nome, "telefone": telefone, "email": email, "cpf_cnpj": cpf_cnpj},
        )
        conn.commit()
    finally:
        conn.close()

    return True, None


def excluir_cliente(conectar, usuario_id, cliente_id):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, cliente_id)
        if not antes:
            return False, "Cliente não encontrado."

        if repo.possui_os_vinculada(cursor, cliente_id):
            return False, "Cliente possui OS vinculada e não pode ser excluído."

        repo.deletar(cursor, cliente_id)
        registrar_log_auditoria(
            cursor, "cliente", cliente_id, usuario_id, "delete", antes=_cliente_para_dict(antes)
        )
        conn.commit()
    finally:
        conn.close()

    return True, None
