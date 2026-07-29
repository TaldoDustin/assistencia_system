"""
fluxoly_tipos_garantia_service.py

Regra de negócio do cadastro Tipos de Garantia (BR-055,
docs/product/features/VENDAS.md "V1.5 -- Garantia"). Consumido por
`fluxoly_vendas_service.py` (Garantia de Venda) e `irflow_os.py` (Garantia de
Reparo) via `obter_tipo_garantia` -- nenhum dos dois acessa
`fluxoly_tipos_garantia_repository.py` diretamente (service a service, nunca
repository a repository, `ENGINEERING_GUIDE.md` §3.1).
"""

import fluxoly_tipos_garantia_repository as repo


def _tipo_garantia_para_dict(row):
    return {
        "id": row[0],
        "nome": row[1],
        "duracao_meses": row[2],
        "ativo": bool(row[3]),
    }


def criar_tipo_garantia(conectar, nome, duracao_meses):
    """Retorna (id, erro). `nome` obrigatório; `duracao_meses` inteiro >= 0
    (0 = "sem garantia", uma política que a loja pode ou não cadastrar,
    BR-055 -- nunca obrigatório existir)."""
    nome = (nome or "").strip()
    if not nome:
        return None, "Nome é obrigatório."
    if not isinstance(duracao_meses, int) or isinstance(duracao_meses, bool) or duracao_meses < 0:
        return None, "Duração deve ser um número inteiro de meses maior ou igual a zero."

    conn = conectar()
    try:
        cursor = conn.cursor()
        tipo_garantia_id = repo.inserir(cursor, nome, duracao_meses)
        conn.commit()
    finally:
        conn.close()
    return tipo_garantia_id, None


def atualizar_tipo_garantia(conectar, tipo_garantia_id, nome, duracao_meses, ativo=True):
    """Retorna (sucesso, erro). Editar a política nunca altera garantias já
    concedidas -- essas vivem como snapshot em `vendas_itens`/`os_reparos`,
    nunca lidas ao vivo daqui (BR-057/BR-062)."""
    nome = (nome or "").strip()
    if not nome:
        return False, "Nome é obrigatório."
    if not isinstance(duracao_meses, int) or isinstance(duracao_meses, bool) or duracao_meses < 0:
        return False, "Duração deve ser um número inteiro de meses maior ou igual a zero."

    conn = conectar()
    try:
        cursor = conn.cursor()
        linhas = repo.atualizar(cursor, tipo_garantia_id, nome, duracao_meses, ativo)
        if linhas == 0:
            conn.rollback()
            return False, "Tipo de Garantia não encontrado."
        conn.commit()
    finally:
        conn.close()
    return True, None


def obter_tipo_garantia(conectar, tipo_garantia_id):
    """Usado por Vendas/Assistência para resolver o tipo escolhido no momento
    da concessão. Retorna `None` se não existir -- o chamador decide a
    mensagem de erro apropriada ao seu próprio contexto."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, tipo_garantia_id)
    finally:
        conn.close()
    return _tipo_garantia_para_dict(row) if row else None


def listar_tipos_garantia(conectar, incluir_inativos=False):
    conn = conectar()
    try:
        cursor = conn.cursor()
        rows = repo.listar(cursor, incluir_inativos)
    finally:
        conn.close()
    return [_tipo_garantia_para_dict(r) for r in rows]
