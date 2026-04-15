import json
import time
from datetime import datetime
from urllib import error as urllib_error
from urllib import request as urllib_request


def valor_payload(payload, *caminhos):
    for caminho in caminhos:
        atual = payload
        for chave in caminho:
            if not isinstance(atual, dict):
                atual = None
                break
            atual = atual.get(chave)
        if atual not in (None, ""):
            return atual
    return ""


def lista_payload(payload, chave):
    valor = payload.get(chave) if isinstance(payload, dict) else None
    return valor if isinstance(valor, list) else []


def primeiro_item_lista(payload, chave):
    itens = lista_payload(payload, chave)
    return itens[0] if itens else {}


def obter_estado_integracao(cursor, chave, padrao=""):
    cursor.execute("SELECT valor FROM integracao_sync_estado WHERE chave=?", (chave,))
    row = cursor.fetchone()
    return row[0] if row else padrao


def definir_estado_integracao(cursor, chave, valor):
    cursor.execute(
        """
        INSERT INTO integracao_sync_estado (chave, valor)
        VALUES (?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor
        """,
        (chave, str(valor)),
    )


def os_integracao_ja_vista(cursor, origem, external_id):
    cursor.execute(
        "SELECT 1 FROM integracao_os_vistas WHERE origem=? AND id_externo=?",
        (origem, str(external_id)),
    )
    return cursor.fetchone() is not None


def marcar_os_integracao_vista(cursor, origem, external_id):
    cursor.execute(
        """
        INSERT OR IGNORE INTO integracao_os_vistas (origem, id_externo, primeira_visualizacao)
        VALUES (?, ?, ?)
        """,
        (origem, str(external_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def extrair_ids_os_listagem_mercado_phone(payload, texto_limpo):
    if isinstance(payload, list):
        itens = payload
    elif isinstance(payload, dict):
        itens = None
        data = payload.get("data")
        if isinstance(data, dict):
            for chave in ("itens", "items", "results", "ordens", "ordensServico", "rows"):
                valor = data.get(chave)
                if isinstance(valor, list):
                    itens = valor
                    break
        if itens is None:
            for chave in ("data", "items", "results", "ordens", "ordensServico", "rows"):
                valor = payload.get(chave)
                if isinstance(valor, list):
                    itens = valor
                    break
        if itens is None:
            itens = [payload]
    else:
        itens = []

    ids = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        external_id = texto_limpo(item.get("id") or item.get("codigo"))
        if external_id and external_id not in ids:
            ids.append(external_id)
    return ids


def parse_json_response(conteudo):
    if not conteudo:
        return {}
    try:
        return json.loads(conteudo.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(conteudo.decode("latin-1"))


def chamar_api_mercado_phone(method_name, payload, config):
    api_token = config["api_token"]
    if not api_token:
        raise RuntimeError("MERCADO_PHONE_API_TOKEN nao configurado.")

    url = f'{config["api_base"]}{method_name}'
    body = json.dumps(payload or {}).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": api_token,
            "Content-Type": "application/json",
        },
    )
    with urllib_request.urlopen(req, timeout=config["sync_timeout_seconds"]) as response:
        return parse_json_response(response.read())


def listar_os_mercado_phone(config, page=1, limit=300):
    return chamar_api_mercado_phone(
        "index",
        {
            "page": page,
            "limit": limit,
            "order": "id",
            "direction": "desc",
            "filters": {
                "codigo": "",
                "diagnostico": "",
                "clienteId": "",
                "situacaoId": "",
                "tipoId": "",
                "dataCriacaoInicial": config["sync_start_date"],
                "dataCriacaoFinal": "",
                "dataFinalizacaoInicial": "",
                "dataFinalizacaoFinal": "",
                "dataPrevisaoInicial": "",
                "dataPrevisaoFinal": "",
                "observacao": "",
                "defeito": "",
                "nomeCliente": "",
            },
        },
        config,
    )


def detalhar_os_mercado_phone(external_id, config):
    return chamar_api_mercado_phone(
        "get",
        {"filters": {"codigo": "", "id": str(external_id)}},
        config,
    )


def importar_os_mercado_phone(cursor, payload, config, helpers):
    if not isinstance(payload, dict):
        raise ValueError("Payload invalido.")

    texto_limpo = helpers["texto_limpo"]
    modelo_para_os = helpers["modelo_para_os"]
    extrair_modelo_da_descricao_aparelho = helpers["extrair_modelo_da_descricao_aparelho"]
    extrair_cor_da_descricao_aparelho = helpers["extrair_cor_da_descricao_aparelho"]
    normalizar_imei = helpers["normalizar_imei"]
    nome_reparo_importavel = helpers["nome_reparo_importavel"]
    obter_ou_criar_reparo = helpers["obter_ou_criar_reparo"]
    salvar_reparos_os = helpers["salvar_reparos_os"]
    normalizar_busca_texto = helpers["normalizar_busca_texto"]
    normalizar_status_os = helpers["normalizar_status_os"]

    external_id = texto_limpo(
        valor_payload(
            payload,
            ("id_externo",),
            ("external_id",),
            ("id",),
            ("os_id",),
            ("ordem_servico_id",),
            ("ordem_servico", "id"),
        )
    )
    if not external_id:
        raise ValueError("Nao foi encontrado um identificador externo da OS.")

    cursor.execute(
        """
        SELECT id
        FROM os
        WHERE origem_integracao=? AND id_externo_integracao=?
        """,
        ("mercado_phone", external_id),
    )
    existente = cursor.fetchone()
    if existente:
        return {"os_id": existente[0], "duplicada": True}

    aparelho_info = primeiro_item_lista(payload, "aparelhos")
    servicos = lista_payload(payload, "servicos")

    cliente = texto_limpo(
        valor_payload(
            payload,
            ("clienteNome",),
            ("cliente", "nome"),
            ("cliente_nome",),
            ("nome_cliente",),
            ("cliente",),
        )
    )
    descricao_aparelho = texto_limpo(aparelho_info.get("descricao"))
    modelo = modelo_para_os(
        valor_payload(
            payload,
            ("modeloDescricao",),
            ("modeloDescricaoAparelho",),
            ("aparelho", "modelo"),
            ("modelo",),
            ("modelo_celular",),
            ("celular_modelo",),
            ("descricao",),
        )
    )
    if not modelo:
        modelo = modelo_para_os(descricao_aparelho)
    if not modelo:
        modelo = extrair_modelo_da_descricao_aparelho(descricao_aparelho)
    cor = texto_limpo(
        valor_payload(
            payload,
            ("aparelho", "cor"),
            ("cor",),
            ("cor_celular",),
        )
    )
    if not cor:
        cor = extrair_cor_da_descricao_aparelho(descricao_aparelho, modelo)
    imei = normalizar_imei(
        valor_payload(
            payload,
            ("aparelho", "imei"),
            ("imei",),
            ("imei1",),
        )
    )
    if not imei:
        imei = normalizar_imei(aparelho_info.get("imei"))

    reparos_nomes = []
    for servico in servicos:
        if not isinstance(servico, dict):
            continue
        nome_servico = texto_limpo(servico.get("servicoDescricao"))
        if nome_reparo_importavel(nome_servico) and nome_servico not in reparos_nomes:
            reparos_nomes.append(nome_servico)

    reparo_principal = texto_limpo(
        valor_payload(
            payload,
            ("tipo_reparo",),
            ("reparo", "nome"),
            ("reparo",),
            ("servico",),
            ("tipoServico",),
            ("solucao",),
        )
    )
    if nome_reparo_importavel(reparo_principal) and reparo_principal not in reparos_nomes:
        reparos_nomes.insert(0, reparo_principal)

    if not cliente:
        cliente = "Cliente nao informado"
    if not modelo:
        modelo = "Nao informado"
    if not reparos_nomes:
        reparos_nomes = ["Nao informado"]

    aparelho = descricao_aparelho or modelo

    reparo_ids = []
    for nome_reparo in reparos_nomes:
        reparo_id = obter_ou_criar_reparo(cursor, nome_reparo)
        if reparo_id and reparo_id not in reparo_ids:
            reparo_ids.append(reparo_id)

    data_os = texto_limpo(
        valor_payload(
            payload,
            ("dataCriacao",),
            ("data",),
            ("data_os",),
            ("created_at",),
            ("createdAt",),
        )
    )[:10] or datetime.now().strftime("%Y-%m-%d")
    status = normalizar_status_os(
        valor_payload(
            payload,
            ("situacaoDescricao",),
            ("status",),
        )
    )
    tipo_origem = texto_limpo(valor_payload(payload, ("tipoDescricao",), ("tipo",)))
    tipo = "Garantia" if "garantia" in normalizar_busca_texto(tipo_origem) else "Assistencia"
    tecnico = texto_limpo(valor_payload(payload, ("tecnicoNome",), ("tecnico", "nome"))) or config["default_tecnico"]
    vendedor = texto_limpo(valor_payload(payload, ("vendedorNome",), ("vendedor", "nome")))
    observacoes_partes = [
        "Importada automaticamente do Mercado Phone.",
        texto_limpo(valor_payload(payload, ("defeito",))),
        texto_limpo(valor_payload(payload, ("diagnostico",))),
        texto_limpo(valor_payload(payload, ("observacao",))),
        texto_limpo(valor_payload(payload, ("observacaoInterna",))),
        texto_limpo(valor_payload(payload, ("solucao",))),
    ]
    observacoes = " | ".join(parte for parte in observacoes_partes if parte)

    cursor.execute(
        """
        INSERT INTO os (
            tipo, cliente, aparelho, tecnico, reparo_id, status,
            valor_cobrado, valor_descontado, custo_pecas, data, observacoes,
            modelo, vendedor, cor, imei, origem_integracao, id_externo_integracao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tipo,
            cliente,
            aparelho,
            tecnico,
            reparo_ids[0],
            status,
            0,
            0,
            0,
            data_os,
            observacoes,
            modelo,
            vendedor,
            cor,
            imei,
            "mercado_phone",
            external_id,
        ),
    )

    os_id = cursor.lastrowid
    salvar_reparos_os(cursor, os_id, reparo_ids)
    return {"os_id": os_id, "duplicada": False}


def sincronizar_mercado_phone(conectar, config, helpers):
    conn = conectar()
    cursor = conn.cursor()
    origem = "mercado_phone"

    try:
        ids_encontrados = []
        seen_ids = set()
        page = 1
        page_limit = 300
        max_pages = int(config.get("sync_max_pages", 100) or 100)

        while page <= max_pages:
            listagem = listar_os_mercado_phone(config, page=page, limit=page_limit)
            page_ids = extrair_ids_os_listagem_mercado_phone(listagem, helpers["texto_limpo"])
            if not page_ids:
                break

            added = 0
            for external_id in page_ids:
                if external_id not in seen_ids:
                    seen_ids.add(external_id)
                    ids_encontrados.append(external_id)
                    added += 1

            if added == 0 or len(page_ids) < page_limit:
                break

            page += 1

        if not ids_encontrados:
            definir_estado_integracao(cursor, "mercado_phone_sync_ultima_execucao", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            conn.commit()
            return {"ok": True, "importadas": 0, "ignoradas": 0, "inicializada": False}

        inicializada = obter_estado_integracao(cursor, "mercado_phone_sync_inicializado", "") == "1"
        importadas = 0
        ignoradas = 0

        if not inicializada and config["sync_only_after_boot"]:
            for external_id in ids_encontrados:
                marcar_os_integracao_vista(cursor, origem, external_id)
            definir_estado_integracao(cursor, "mercado_phone_sync_inicializado", "1")
            definir_estado_integracao(cursor, "mercado_phone_sync_ultima_execucao", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            conn.commit()
            return {"ok": True, "importadas": 0, "ignoradas": len(ids_encontrados), "inicializada": True}

        for external_id in ids_encontrados:
            if os_integracao_ja_vista(cursor, origem, external_id):
                ignoradas += 1
                continue

            detalhes = detalhar_os_mercado_phone(external_id, config)
            payload_importacao = detalhes if isinstance(detalhes, dict) else {}
            if isinstance(payload_importacao.get("data"), dict):
                payload_importacao = payload_importacao["data"]

            resultado = importar_os_mercado_phone(cursor, payload_importacao, config, helpers)
            marcar_os_integracao_vista(cursor, origem, external_id)
            if resultado["duplicada"]:
                ignoradas += 1
            else:
                importadas += 1

        definir_estado_integracao(cursor, "mercado_phone_sync_inicializado", "1")
        definir_estado_integracao(cursor, "mercado_phone_sync_ultima_execucao", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        conn.commit()
        return {"ok": True, "importadas": importadas, "ignoradas": ignoradas, "inicializada": True}
    finally:
        conn.close()


def corrigir_dados_importados_mercado_phone(conectar, helpers):
    conn = conectar()
    cursor = conn.cursor()

    try:
        normalizar_busca_texto = helpers["normalizar_busca_texto"]
        extrair_modelo_da_descricao_aparelho = helpers["extrair_modelo_da_descricao_aparelho"]
        extrair_cor_da_descricao_aparelho = helpers["extrair_cor_da_descricao_aparelho"]
        nome_reparo_importavel = helpers["nome_reparo_importavel"]

        cursor.execute(
            """
            SELECT id, COALESCE(tipo, ''), COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(aparelho, '')
            FROM os
            WHERE origem_integracao='mercado_phone'
            """
        )
        for os_id, tipo, modelo, cor, aparelho in cursor.fetchall():
            novo_tipo = "Garantia" if "garantia" in normalizar_busca_texto(tipo) else "Assistencia"
            novo_modelo = modelo
            novo_cor = cor

            if (not novo_modelo) or novo_modelo in {"Nao informado"} or "iphone" not in normalizar_busca_texto(novo_modelo):
                modelo_extraido = extrair_modelo_da_descricao_aparelho(aparelho or modelo)
                if modelo_extraido:
                    novo_modelo = modelo_extraido

            if not novo_cor:
                cor_extraida = extrair_cor_da_descricao_aparelho(aparelho or modelo, novo_modelo)
                if cor_extraida:
                    novo_cor = cor_extraida

            cursor.execute(
                "UPDATE os SET tipo=?, modelo=?, aparelho=?, cor=? WHERE id=?",
                (novo_tipo, novo_modelo, novo_modelo, novo_cor, os_id),
            )

        cursor.execute("SELECT id, nome FROM reparos")
        reparos = cursor.fetchall()
        reparos_invalidos = {reparo_id for reparo_id, nome in reparos if not nome_reparo_importavel(nome)}

        for reparo_id in reparos_invalidos:
            cursor.execute("DELETE FROM os_reparos WHERE reparo_id=?", (reparo_id,))

        cursor.execute(
            """
            UPDATE os
            SET reparo_id = (
                SELECT os_reparos.reparo_id
                FROM os_reparos
                WHERE os_reparos.os_id = os.id
                ORDER BY os_reparos.reparo_id
                LIMIT 1
            )
            WHERE origem_integracao='mercado_phone'
            """
        )

        cursor.execute(
            """
            DELETE FROM reparos
            WHERE id NOT IN (SELECT reparo_id FROM os_reparos)
              AND lower(COALESCE(nome, '')) IN ('iphone', 'ipad', 'smartphone', 'celular')
            """
        )
        conn.commit()
    finally:
        conn.close()


def loop_sincronizacao_mercado_phone(conectar, config, helpers):
    while True:
        try:
            if config["sync_enabled"] and config["api_token"]:
                sincronizar_mercado_phone(conectar, config, helpers)
        except urllib_error.URLError as exc:
            print(f"[MercadoPhone] Falha de rede na sincronizacao: {type(exc).__name__}: {exc}")
        except Exception as exc:
            print(f"[MercadoPhone] Falha inesperada na sincronizacao: {type(exc).__name__}: {exc}")
        time.sleep(max(30, config["sync_interval_seconds"]))
