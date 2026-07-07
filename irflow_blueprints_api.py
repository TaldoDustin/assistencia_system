"""
IR Flow - API Blueprint (JSON endpoints)
All routes under /api/* — consumed by the React SPA frontend.
Authentication: Flask session cookies (same-origin, credentials: 'include').
"""

from datetime import datetime, timedelta
import json
import re
import secrets
import math
import threading

from flask import Blueprint, jsonify, request, session, send_from_directory, Response
import os

from irflow_price_tables import sugerir_preco_tabela


def create_api_blueprint(deps):
    api = Blueprint("api", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    normalizar_status_os = deps["normalizar_status_os"]
    status_finalizado = deps["status_finalizado"]
    status_cancelado = deps["status_cancelado"]
    status_aberto = deps["status_aberto"]
    status_em_andamento = deps["status_em_andamento"]
    status_aguardando_peca = deps["status_aguardando_peca"]
    calcular_faturamento_os = deps["calcular_faturamento_os"]
    calcular_lucro_os = deps["calcular_lucro_os"]
    carregar_os_com_relacoes = deps["carregar_os_com_relacoes"]
    extrair_reparo_ids = deps["extrair_reparo_ids"]
    validar_reparo_ids = deps["validar_reparo_ids"]
    vendedor_valido = deps["vendedor_valido"]
    salvar_reparos_os = deps["salvar_reparos_os"]
    modelo_compativel = deps["modelo_compativel"]
    consumir_peca_da_os = deps["consumir_peca_da_os"]
    adicionar_peca_os_sem_consumir = deps["adicionar_peca_os_sem_consumir"]
    devolver_pecas_da_os = deps["devolver_pecas_da_os"]
    registrar_movimentacao = deps["registrar_movimentacao"]
    obter_reparos_por_os = deps["obter_reparos_por_os"]
    modelo_para_os = deps["modelo_para_os"]
    normalizar_imei = deps["normalizar_imei"]
    normalizar_modelo_iphone = deps["normalizar_modelo_iphone"]
    carregar_tabelas_preco = deps["carregar_tabelas_preco"]
    salvar_tabelas_preco = deps["salvar_tabelas_preco"]
    texto_reparos_os = deps["texto_reparos_os"]
    listar_custos_operacionais = deps["listar_custos_operacionais"]
    agrupar_relatorio_custos_operacionais = deps["agrupar_relatorio_custos_operacionais"]
    agrupar_relatorio_ir_phones = deps["agrupar_relatorio_ir_phones"]
    agrupar_relatorio_tecnicos = deps["agrupar_relatorio_tecnicos"]
    montar_linhas_relatorio_custos_operacionais = deps["montar_linhas_relatorio_custos_operacionais"]
    montar_linhas_relatorio_ir_phones = deps["montar_linhas_relatorio_ir_phones"]
    montar_linhas_relatorio_tecnicos = deps["montar_linhas_relatorio_tecnicos"]
    montar_pdf_texto = deps["montar_pdf_texto"]
    formatar_periodo_relatorio = deps["formatar_periodo_relatorio"]
    parse_data_ymd = deps["parse_data_ymd"]
    obter_alertas_sistema = deps["obter_alertas_sistema"]
    iphone_models = deps["iphone_models"]
    iphone_colors = deps["iphone_colors"]
    vendedores = deps["vendedores"]
    tecnicos = deps["tecnicos"]
    status_os_opcoes = deps["status_os_opcoes"]
    categorias_custos = deps["categorias_custos"]
    reparos_padrao = deps["reparos_padrao"]
    backup_dir = deps["backup_dir"]
    criar_backup = deps["criar_backup"]
    google_drive_backup_dir = deps["google_drive_backup_dir"]
    garantir_pasta_backup_google_drive = deps["garantir_pasta_backup_google_drive"]
    enviar_backup_email = deps["enviar_backup_email"]
    backup_email_remetente = deps["backup_email_remetente"]
    backup_email_senha_app = deps["backup_email_senha_app"]
    backup_email_destino = deps["backup_email_destino"]
    check_password_hash = deps["check_password_hash"]
    generate_password_hash = deps["generate_password_hash"]
    sincronizar_mercado_phone = deps["sincronizar_mercado_phone"]
    reimportar_todas_os_mercado_phone = deps["reimportar_todas_os_mercado_phone"]
    reprocessar_todas_os_mercado_phone = deps["reprocessar_todas_os_mercado_phone"]
    mercado_phone_runtime_config = deps["mercado_phone_runtime_config"]
    mercado_phone_helpers = deps["mercado_phone_helpers"]
    public_base_url = deps.get("public_base_url", "")
    integrations_config_path = deps["integrations_config_path"]
    carregar_configuracoes_integracoes = deps["carregar_configuracoes_integracoes"]
    salvar_configuracoes_integracoes = deps["salvar_configuracoes_integracoes"]
    db_path = deps["db_path"]
    forcar_migracao_schema = deps["forcar_migracao_schema"]

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def _texto_limpo_local(valor):
        return (valor or "").strip()

    def _to_bool(valor, padrao=False):
        if valor is None:
            return padrao
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() not in {"", "0", "false", "nao", "off"}

    def _carregar_config_mercadophone():
        dados = carregar_configuracoes_integracoes(integrations_config_path)
        if not isinstance(dados, dict):
            dados = {}
        mp = dados.get("mercado_phone")
        if not isinstance(mp, dict):
            mp = {}
            dados["mercado_phone"] = mp
        return dados, mp

    def _atualizar_runtime_mercadophone(mp_cfg):
        token_cfg = _texto_limpo_local(mp_cfg.get("api_token"))
        token_runtime = _texto_limpo_local(mercado_phone_runtime_config.get("api_token"))
        token = token_cfg or token_runtime

        intervalo_cfg = mp_cfg.get("sync_interval_seconds", mercado_phone_runtime_config.get("sync_interval_seconds", 180))
        timeout_cfg = mp_cfg.get("sync_timeout_seconds", mercado_phone_runtime_config.get("sync_timeout_seconds", 20))

        try:
            intervalo = max(30, int(intervalo_cfg or 180))
        except (TypeError, ValueError):
            intervalo = 180

        try:
            timeout = max(5, int(timeout_cfg or 20))
        except (TypeError, ValueError):
            timeout = 20

        start_date = _texto_limpo_local(mp_cfg.get("sync_start_date") or mercado_phone_runtime_config.get("sync_start_date") or "2026-04-01")

        mercado_phone_runtime_config.update(
            {
                "api_token": token,
                "sync_enabled": _to_bool(mp_cfg.get("sync_enabled"), padrao=bool(token)),
                "sync_interval_seconds": intervalo,
                "sync_timeout_seconds": timeout,
                "sync_start_date": start_date,
            }
        )

        return {
            "configurado": bool(token),
            "sync_enabled": bool(mercado_phone_runtime_config.get("sync_enabled")),
            "sync_interval_seconds": int(mercado_phone_runtime_config.get("sync_interval_seconds") or 0),
            "sync_timeout_seconds": int(mercado_phone_runtime_config.get("sync_timeout_seconds") or 0),
            "sync_start_date": mercado_phone_runtime_config.get("sync_start_date") or "",
            "api_base": mercado_phone_runtime_config.get("api_base") or "",
        }

    reprocessamento_mp_lock = threading.Lock()
    reprocessamento_mp_estado = {
        "rodando": False,
        "iniciado_em": None,
        "finalizado_em": None,
        "atualizadas": 0,
        "erros": 0,
        "total": 0,
        "erro": "",
    }

    def _snapshot_reprocessamento_mp():
        with reprocessamento_mp_lock:
            return dict(reprocessamento_mp_estado)

    def _executar_reprocessamento_mp_async():
        try:
            resultado = reprocessar_todas_os_mercado_phone(
                conectar, mercado_phone_runtime_config, mercado_phone_helpers
            )
            with reprocessamento_mp_lock:
                reprocessamento_mp_estado["rodando"] = False
                reprocessamento_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["total"] = int(resultado.get("total") or 0)
                reprocessamento_mp_estado["atualizadas"] = int(resultado.get("atualizadas") or 0)
                reprocessamento_mp_estado["erros"] = int(resultado.get("erros") or 0)
                reprocessamento_mp_estado["erro"] = ""
        except Exception as exc:
            with reprocessamento_mp_lock:
                reprocessamento_mp_estado["rodando"] = False
                reprocessamento_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["erro"] = str(exc)

    reimportacao_mp_lock = threading.Lock()
    reimportacao_mp_estado = {
        "rodando": False,
        "iniciado_em": None,
        "finalizado_em": None,
        "removidas": 0,
        "importadas": 0,
        "atualizadas": 0,
        "erro": "",
    }

    def _snapshot_reimportacao_mp():
        with reimportacao_mp_lock:
            return dict(reimportacao_mp_estado)

    def _executar_reimportacao_mp_async():
        try:
            resultado = reimportar_todas_os_mercado_phone(
                conectar, mercado_phone_runtime_config, mercado_phone_helpers
            )
            with reimportacao_mp_lock:
                reimportacao_mp_estado["rodando"] = False
                reimportacao_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["removidas"] = int(resultado.get("removidas") or 0)
                reimportacao_mp_estado["importadas"] = int(resultado.get("importadas") or 0)
                reimportacao_mp_estado["atualizadas"] = int(resultado.get("atualizadas") or 0)
                reimportacao_mp_estado["erro"] = ""
        except Exception as exc:
            with reimportacao_mp_lock:
                reimportacao_mp_estado["rodando"] = False
                reimportacao_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["erro"] = str(exc)

    ESTOQUE_TIPOS = ["Tela", "Bateria", "Conector", "Camera", "Placa", "Carcaca", "Alto-falante", "Outros"]
    ESTOQUE_QUALIDADES = ["Original", "Premium", "Paralelo", "Refurbished", "Padrao"]

    # ── Inject dependencies ────────────────────────────────────────────────
    def criar_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        modelo = normalizar_modelo_iphone(body.get("modelo") or "") or (body.get("modelo") or "").strip()
        tipo = _normalizar_tipo_estoque(body.get("tipo"))
        qualidade = _normalizar_qualidade_estoque(body.get("qualidade"))
        valor = float(body.get("valor") or 0)
        fornecedor = (body.get("fornecedor") or "Nao informado").strip()
        quantidade = int(body.get("quantidade") or 0)
        data_compra = (body.get("data_compra") or "").strip() or datetime.now().strftime("%Y-%m-%d")

        if not descricao or valor <= 0 or quantidade < 0:
            return err("Preencha descrição, valor e quantidade.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            # Permitir sempre cadastrar novo produto, mesmo com modelo/tipo/qualidade igual

            cursor.execute(
                """
                INSERT INTO estoque (descricao, modelo, valor, fornecedor, quantidade, data_compra, tipo, qualidade)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (descricao, modelo, valor, fornecedor, max(0, quantidade), data_compra, tipo, qualidade),
            )
            novo_id = cursor.lastrowid
            if quantidade > 0:
                cursor.execute(
                    """
                    INSERT INTO estoque_lotes (
                        estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
                    )
                    VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (novo_id, fornecedor, valor, quantidade, quantidade, data_compra, "", datetime.now().isoformat()),
                )
            conn.commit()
            return ok(id=novo_id)
        except Exception as e:
            conn.rollback()
            return err(f"Erro ao criar item: {e}")
        finally:
            conn.close()
        return bool(session.get("usuario_id"))

    def usuario_admin():
        return session.get("usuario_perfil") == "admin"

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    def _slug_estoque(valor):
        base = (valor or "").strip().upper()
        base = re.sub(r"[^A-Z0-9]+", "-", base)
        base = re.sub(r"-+", "-", base).strip("-")
        return base

    def _normalizar_tipo_estoque(valor):
        texto = (valor or "").strip().lower()
        for opcao in ESTOQUE_TIPOS:
            if texto == opcao.lower():
                return opcao
        return "Outros"

    def _normalizar_qualidade_estoque(valor):
        texto = (valor or "").strip().lower()
        for opcao in ESTOQUE_QUALIDADES:
            if texto == opcao.lower():
                return opcao
        return "Padrao"

    def _gerar_sku_estoque(modelo, tipo, qualidade, descricao):
        partes = [
            _slug_estoque(modelo)[:10],
            _slug_estoque(tipo)[:8],
            _slug_estoque(qualidade)[:8],
            _slug_estoque(descricao)[:10],
        ]
        partes = [p for p in partes if p]
        if not partes:
            return "ITEM"
        return "-".join(partes)

    def _recalcular_custo_medio(cursor, estoque_id):
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(COALESCE(valor_compra, 0) * COALESCE(quantidade_disponivel, 0)), 0),
                COALESCE(SUM(COALESCE(quantidade_disponivel, 0)), 0)
            FROM estoque_lotes
            WHERE estoque_id = ?
            """,
            (estoque_id,),
        )
        total_valor, total_qtd = cursor.fetchone() or (0, 0)
        total_qtd = int(total_qtd or 0)

        if total_qtd > 0:
            valor_medio = float(total_valor or 0) / total_qtd
            cursor.execute("UPDATE estoque SET valor=? WHERE id=?", (round(valor_medio, 2), estoque_id))

    def _status_item_estoque(quantidade, ultima_movimentacao, consumo_90d):
        qtd = int(quantidade or 0)
        consumo = int(consumo_90d or 0)
        if qtd > 0:
            return "disponivel"
        if consumo > 0:
            return "esgotado_ativo"
        if not (ultima_movimentacao or "").strip():
            return "inativo"
        return "esgotado"

    def _parse_checklist_json(value):
        texto = (value or "").strip()
        if not texto:
            return {}
        try:
            parsed = json.loads(texto)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _checklist_status(value):
        texto = (value or "").strip().lower().replace(" ", "_")
        aliases = {
            "": "nao_testado",
            "nao": "reprovado",
            "nao_testado": "nao_testado",
            "nao-testado": "nao_testado",
            "pendente": "nao_testado",
            "ok": "aprovado",
            "passou": "aprovado",
            "aprovado": "aprovado",
            "falhou": "reprovado",
            "falha": "reprovado",
            "reprovado": "reprovado",
        }
        return aliases.get(texto, "nao_testado")

    def _serialize_checklist(cursor, row):
        if not row:
            return None

        resultado = _parse_checklist_json(row[10])
        return {
            "id": row[0],
            "os_id": row[1],
            "access_token": row[2] or "",
            "status_touch": _checklist_status(row[3]),
            "status_audio": _checklist_status(row[4]),
            "status_microfone": _checklist_status(row[5]),
            "status_camera": _checklist_status(row[6]),
            "status_botoes": _checklist_status(row[7]),
            "observacoes": row[8] or "",
            "executado_por": row[9] or "",
            "resultado": resultado,
            "origem": row[11] or "",
            "criado_em": row[12] or "",
            "atualizado_em": row[13] or "",
        }

    def _resolve_public_base_url():
        if public_base_url:
            return public_base_url
        return request.host_url.rstrip("/")

    def _enriquecer_checklist_urls(checklist):
        if not checklist:
            return None
        enriched = dict(checklist)
        token = enriched.get("access_token") or ""
        if token:
            enriched["public_url"] = f"{_resolve_public_base_url()}/app/checklist/{token}"
        else:
            enriched["public_url"] = ""
        return enriched

    def _buscar_checklist_por_os(cursor, os_id):
        cursor.execute(
            """
            SELECT id, os_id, COALESCE(access_token, ''), COALESCE(status_touch, 'nao_testado'),
                   COALESCE(status_audio, 'nao_testado'), COALESCE(status_microfone, 'nao_testado'),
                   COALESCE(status_camera, 'nao_testado'), COALESCE(status_botoes, 'nao_testado'),
                   COALESCE(observacoes, ''), COALESCE(executado_por, ''), COALESCE(resultado_json, '{}'),
                   COALESCE(origem, ''), COALESCE(criado_em, ''), COALESCE(atualizado_em, '')
            FROM os_checklists
            WHERE os_id=?
            """,
            (os_id,),
        )
        return _enriquecer_checklist_urls(_serialize_checklist(cursor, cursor.fetchone()))

    def _buscar_checklist_por_token(cursor, token):
        cursor.execute(
            """
            SELECT id, os_id, COALESCE(access_token, ''), COALESCE(status_touch, 'nao_testado'),
                   COALESCE(status_audio, 'nao_testado'), COALESCE(status_microfone, 'nao_testado'),
                   COALESCE(status_camera, 'nao_testado'), COALESCE(status_botoes, 'nao_testado'),
                   COALESCE(observacoes, ''), COALESCE(executado_por, ''), COALESCE(resultado_json, '{}'),
                   COALESCE(origem, ''), COALESCE(criado_em, ''), COALESCE(atualizado_em, '')
            FROM os_checklists
            WHERE access_token=?
            """,
            (token,),
        )
        return _enriquecer_checklist_urls(_serialize_checklist(cursor, cursor.fetchone()))

    def _garantir_checklist_os(cursor, os_id):
        checklist = _buscar_checklist_por_os(cursor, os_id)
        if checklist:
            return checklist

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO os_checklists (os_id, criado_em, atualizado_em)
            VALUES (?, ?, ?)
            """,
            (os_id, agora, agora),
        )
        return _buscar_checklist_por_os(cursor, os_id)

    # ── AUTHENTICATION ─────────────────────────────────────────────────────

    @api.route("/auth/login", methods=["POST"])
    def auth_login():
        body = request.get_json(silent=True) or {}
        usuario_txt = (body.get("usuario") or "").strip()
        senha_txt = body.get("senha") or ""

        if not usuario_txt or not senha_txt:
            return err("Usuário e senha são obrigatórios.")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, senha_hash, perfil, ativo FROM usuarios WHERE usuario = ?",
            (usuario_txt,),
        )
        row = cursor.fetchone()
        conn.close()

        if row and row[4] == 1 and check_password_hash(row[2], senha_txt):
            session.permanent = True
            session["usuario_id"] = row[0]
            session["usuario_nome"] = row[1]
            session["usuario_perfil"] = row[3]
            return ok(usuario={"id": row[0], "nome": row[1], "perfil": row[3]})

        return err("Usuário ou senha inválidos.", 401)

    @api.route("/auth/logout", methods=["POST"])
    def auth_logout():
        session.clear()
        return ok()

    @api.route("/auth/me")
    def auth_me():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(usuario={
            "id": session["usuario_id"],
            "nome": session["usuario_nome"],
            "perfil": session["usuario_perfil"],
        })

    # ── CONSTANTS ──────────────────────────────────────────────────────────

    def _sanitize_list(arr):
        if not isinstance(arr, (list, tuple)):
            return arr
        out = []
        for v in arr:
            if v is None:
                continue
            if isinstance(v, str):
                s = v.strip()
                if s == "":
                    continue
                out.append(s)
            else:
                out.append(v)
        return out

    def _sanitize_nested_obj(obj):
        if not isinstance(obj, dict):
            return obj
        out = {}
        for k, v in obj.items():
            if isinstance(v, (list, tuple)):
                out[k] = _sanitize_list(v)
            else:
                out[k] = v
        return out

    @api.route("/constantes")
    def constantes():
        payload = {
            "iphone_models": _sanitize_list(iphone_models),
            "iphone_colors": _sanitize_nested_obj(iphone_colors),
            "vendedores": _sanitize_list(vendedores),
            "tecnicos": _sanitize_list(tecnicos),
            "status_opcoes": _sanitize_list(status_os_opcoes),
            "os_tipos": _sanitize_list(["Assistencia", "Garantia", "Upgrade"]),
            "categorias_custos": _sanitize_list(categorias_custos),
            "estoque_tipos": _sanitize_list(ESTOQUE_TIPOS),
            "estoque_qualidades": _sanitize_list(ESTOQUE_QUALIDADES),
            "reparos_padrao": _sanitize_list(reparos_padrao),
            "garantia_dias": 90,
        }
        return ok(**payload)

    # ── ALERTS ─────────────────────────────────────────────────────────────

    @api.route("/alertas")
    def alertas():
        if not usuario_logado():
            return ok(alertas=[])
        try:
            alerts = obter_alertas_sistema(limit=20)
        except Exception:
            alerts = []
        return ok(alertas=alerts)

    # ── DASHBOARD ──────────────────────────────────────────────────────────

    @api.route("/dashboard")
    def dashboard():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        filtro_tecnico = (request.args.get("tecnico") or "").strip()

        conn = conectar()
        cursor = conn.cursor()
        dados, reparos_por_os, custos = carregar_os_com_relacoes(cursor, order_by="os.id DESC")

        lucro_total = faturamento_total = custo_consumido_periodo = 0.0
        ordens_finalizadas = ordens_abertas = 0
        lucro_por_tecnico = {}
        resumo_por_vendedor = {}
        servicos_mais_feitos = {}
        faturamento_por_dia = {}

        for os_item in dados:
            os_id = os_item[0]
            tipo = os_item[1]
            tecnico = os_item[4]
            status = normalizar_status_os(os_item[6])
            valor_cobrado = os_item[7]
            valor_descontado = os_item[8]
            data = os_item[10]
            vendedor = os_item[13]

            custo = custos.get(os_id, 0)
            lucro = calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo)
            faturamento_os = calcular_faturamento_os(valor_cobrado, valor_descontado)

            if filtro_tecnico and tecnico != filtro_tecnico:
                continue
            if (start_date or end_date) and not data:
                continue
            if start_date and data and data < start_date:
                continue
            if end_date and data and data > end_date:
                continue

            if not status_cancelado(status):
                custo_consumido_periodo += custo

            if status_finalizado(status):
                lucro_total += lucro
                faturamento_total += faturamento_os
                ordens_finalizadas += 1
                if data:
                    faturamento_por_dia[data] = faturamento_por_dia.get(data, 0) + faturamento_os
            elif status_aberto(status):
                ordens_abertas += 1

            for reparo_nome in (reparos_por_os.get(os_id, {}).get("nomes", []) or [tipo]):
                if reparo_nome:
                    servicos_mais_feitos[reparo_nome] = servicos_mais_feitos.get(reparo_nome, 0) + 1

            if tecnico and status_finalizado(status):
                lucro_por_tecnico[tecnico] = lucro_por_tecnico.get(tecnico, 0) + lucro

            if vendedor:
                if vendedor not in resumo_por_vendedor:
                    resumo_por_vendedor[vendedor] = {"os_total": 0, "faturamento": 0, "lucro": 0}
                resumo_por_vendedor[vendedor]["os_total"] += 1
                if status_finalizado(status):
                    resumo_por_vendedor[vendedor]["lucro"] += lucro
                    resumo_por_vendedor[vendedor]["faturamento"] += faturamento_os

        cursor.execute("SELECT COALESCE(SUM(valor * quantidade), 0) FROM estoque")
        gasto_total = cursor.fetchone()[0] or 0
        conn.close()

        resumo_custos = listar_custos_operacionais(start_date, end_date)
        custos_operacionais_periodo = resumo_custos["total_periodo"]
        resultado_liquido = lucro_total - custos_operacionais_periodo
        ticket_medio = round(faturamento_total / ordens_finalizadas, 2) if ordens_finalizadas else 0

        dias_ordenados = sorted(faturamento_por_dia.keys())
        servicos_sorted = sorted(servicos_mais_feitos.items(), key=lambda x: x[1], reverse=True)
        lucro_tecnicos_sorted = sorted(lucro_por_tecnico.items(), key=lambda x: x[1], reverse=True)

        # Contadores de shopping list
        try:
            conn2 = conectar()
            cur2 = conn2.cursor()
            cur2.execute("SELECT COUNT(1) FROM shopping_list WHERE status='PENDENTE'")
            shopping_pendentes = int(cur2.fetchone()[0] or 0)
            cur2.execute("SELECT COUNT(1) FROM shopping_list WHERE prioridade='URGENTE' AND status!='CANCELADO'")
            shopping_urgentes = int(cur2.fetchone()[0] or 0)
            conn2.close()
        except Exception:
            shopping_pendentes = 0
            shopping_urgentes = 0

        return ok(
            faturamento_total=round(faturamento_total, 2),
            lucro_total=round(lucro_total, 2),
            custo_consumido_periodo=round(custo_consumido_periodo, 2),
            custos_operacionais_periodo=round(custos_operacionais_periodo, 2),
            resultado_liquido=round(resultado_liquido, 2),
            ticket_medio=ticket_medio,
            gasto_total_estoque=round(gasto_total, 2),
            ordens_finalizadas=ordens_finalizadas,
            ordens_abertas=ordens_abertas,
            shopping_pendentes=shopping_pendentes,
            shopping_urgentes=shopping_urgentes,
            faturamento_por_dia=[{"date": d, "value": round(faturamento_por_dia[d], 2)} for d in dias_ordenados],
            lucro_por_tecnico=[{"name": k, "value": round(v, 2)} for k, v in lucro_tecnicos_sorted],
            servicos_mais_feitos=[{"name": k, "value": v} for k, v in servicos_sorted[:10]],
            resumo_por_vendedor=[
                {"vendedor": k, **{kk: round(vv, 2) if isinstance(vv, float) else vv for kk, vv in v.items()}}
                for k, v in sorted(resumo_por_vendedor.items(), key=lambda x: x[1]["faturamento"], reverse=True)
            ],
            custos_por_categoria=resumo_custos["por_categoria"],
        )

    # ── SERVICE ORDERS ─────────────────────────────────────────────────────

    def _os_row_to_dict(row, reparos_por_os, custos):
        os_id = row[0]
        tipo = row[1]
        status = normalizar_status_os(row[6])
        valor_cobrado = row[7]
        valor_descontado = row[8]
        custo = custos.get(os_id, row[9] or 0)
        reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
        return {
            "id": os_id,
            "tipo": tipo or "",
            "cliente": row[2] or "",
            "aparelho": row[3] or "",
            "tecnico": row[4] or "",
            "status": status,
            "reparos": reparos_info.get("nomes", []),
            "reparo_ids": reparos_info.get("ids", []),
            "reparo": texto_reparos_os(reparos_info, tipo or "—"),
            "vendedor": row[13] or "",
            "cor": row[14] or "" if len(row) > 14 else "",
            "imei": row[15] or "" if len(row) > 15 else "",
            "modelo": row[12] or "" if len(row) > 12 else "",
            "valor_cobrado": round(valor_cobrado or 0, 2),
            "valor_descontado": round(valor_descontado or 0, 2),
            "custo_pecas": round(custo or 0, 2),
            "faturamento": round(calcular_faturamento_os(valor_cobrado, valor_descontado), 2),
            "lucro": round(calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo), 2),
            "data": row[10] or "",
            "observacoes": row[11] or "" if len(row) > 11 else "",
            "origem_integracao": row[16] or "" if len(row) > 16 else "",
            "id_externo_integracao": row[17] or "" if len(row) > 17 else "",
        }

    # ── SHOPPING LIST (Lista de Compras) ────────────────────────────────────

    SHOPPING_STATUSES = {"PENDENTE", "EM_COTACAO", "EM_COMPRA", "COMPRADO", "RECEBIDO", "CANCELADO", "ARQUIVADO"}
    SHOPPING_PRIORITIES = {"URGENTE", "ALTA", "NORMAL", "BAIXA"}

    def _log_shopping(cursor, shopping_id, usuario_id, acao, antes=None, depois=None):
        # Armazena valores anteriores/novos como JSON quando possível
        try:
            va = antes if antes is None else (antes if isinstance(antes, str) else json.dumps(antes, default=str))
        except Exception:
            va = str(antes or "")
        try:
            vn = depois if depois is None else (depois if isinstance(depois, str) else json.dumps(depois, default=str))
        except Exception:
            vn = str(depois or "")

        cursor.execute(
            """
            INSERT INTO shopping_list_logs (shopping_list_id, usuario_id, acao, valor_anterior, valor_novo)
            VALUES (?, ?, ?, ?, ?)
            """,
            (shopping_id, usuario_id, acao, va or "", vn or ""),
        )

    @api.route("/shopping-list")
    def shopping_list():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        # filtros e paginação
        status = (request.args.get("status") or "").strip()
        prioridade = (request.args.get("prioridade") or "").strip()
        produto = (request.args.get("produto") or "").strip().lower()
        os_id = (request.args.get("os_id") or "").strip()
        page = int(request.args.get("page") or 1)
        per_page = int(request.args.get("per_page") or 20)

        try:
            conn = conectar()
            cursor = conn.cursor()
            where = []
            params = []
            if status:
                where.append("status = ?")
                params.append(status)
            if prioridade:
                where.append("prioridade = ?")
                params.append(prioridade)
            if produto:
                where.append("lower(produto_nome) LIKE ?")
                params.append(f"%{produto}%")
            if os_id and os_id.isdigit():
                where.append("os_id = ?")
                params.append(int(os_id))

            where_sql = " AND ".join(where) if where else "1=1"
            cursor.execute(f"SELECT COUNT(1) FROM shopping_list WHERE {where_sql}", tuple(params))
            total = cursor.fetchone()[0] or 0

            offset = (max(1, page) - 1) * per_page
            # join with usuarios to get responsavel nome
            cursor.execute(
                f"SELECT s.id, s.os_id, s.produto_id, s.produto_nome, s.quantidade_solicitada, s.quantidade_comprada, s.quantidade_recebida, s.prioridade, s.status, s.responsavel_id, u.nome, s.observacao, s.created_at, s.updated_at, s.purchased_at, s.received_at, s.cancelled_at FROM shopping_list s LEFT JOIN usuarios u ON s.responsavel_id = u.id WHERE {where_sql} ORDER BY prioridade DESC, created_at DESC LIMIT ? OFFSET ?",
                tuple(params + [per_page, offset]),
            )
            rows = cursor.fetchall()
            items = []
            for r in rows:
                items.append({
                    "id": r[0],
                    "os_id": r[1],
                    "produto_id": r[2],
                    "produto_nome": r[3],
                    "quantidade_solicitada": int(r[4] or 0),
                    "quantidade_comprada": int(r[5] or 0),
                    "quantidade_recebida": int(r[6] or 0),
                    "prioridade": r[7],
                    "status": r[8],
                    "responsavel_id": r[9],
                    "responsavel_nome": r[10] or "",
                    "observacao": r[11] or "",
                    "created_at": r[12] or "",
                    "updated_at": r[13] or "",
                    "purchased_at": r[14] or "",
                    "received_at": r[15] or "",
                    "cancelled_at": r[16] or "",
                })
            conn.close()
            return ok(items=items, total=total, page=page, per_page=per_page)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao listar shopping list: {exc}")

    @api.route("/shopping-list/<int:item_id>")
    def shopping_get(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT s.id, s.os_id, s.produto_id, s.produto_nome, s.quantidade_solicitada, s.quantidade_comprada, s.quantidade_recebida, s.prioridade, s.status, s.responsavel_id, u.nome, s.observacao, s.created_at, s.updated_at, s.purchased_at, s.received_at, s.cancelled_at FROM shopping_list s LEFT JOIN usuarios u ON s.responsavel_id = u.id WHERE s.id=?",
                (item_id,),
            )
            r = cursor.fetchone()
            conn.close()
            if not r:
                return err("Item não encontrado", 404)
            return ok(item={
                "id": r[0], "os_id": r[1], "produto_id": r[2], "produto_nome": r[3],
                "quantidade_solicitada": int(r[4] or 0), "quantidade_comprada": int(r[5] or 0), "quantidade_recebida": int(r[6] or 0),
                "prioridade": r[7], "status": r[8], "responsavel_id": r[9], "responsavel_nome": r[10] or "", "observacao": r[11] or "",
                "created_at": r[12] or "", "updated_at": r[13] or "", "purchased_at": r[14] or "", "received_at": r[15] or "", "cancelled_at": r[16] or "",
            })
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao obter item: {exc}")

    @api.route("/shopping-list", methods=["POST"])
    def shopping_create():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            body = request.get_json(silent=True) or {}
            os_id = int(body.get("os_id") or 0)
            produto_id = body.get("produto_id")
            try:
                produto_id = int(produto_id) if produto_id else None
            except Exception:
                produto_id = None
            produto_nome = (body.get("produto_nome") or "").strip()
            quantidade = int(body.get("quantidade_solicitada") or body.get("quantidade") or 1)
            prioridade = (body.get("prioridade") or "NORMAL").strip().upper()
            observacao = (body.get("observacao") or "").strip()

            if quantidade <= 0:
                return err("Quantidade invalida")
            if prioridade not in SHOPPING_PRIORITIES:
                prioridade = "NORMAL"

            conn = conectar()
            cursor = conn.cursor()

            # Verifica duplicidade: mesmo produto (id ou nome) na mesma OS e status != CANCELADO
            if produto_id:
                cursor.execute("SELECT id FROM shopping_list WHERE os_id=? AND produto_id=? AND COALESCE(status, '') != 'CANCELADO'", (os_id, produto_id))
            else:
                cursor.execute("SELECT id FROM shopping_list WHERE os_id=? AND lower(produto_nome)=? AND COALESCE(status, '') != 'CANCELADO'", (os_id, produto_nome.lower()))
            if cursor.fetchone():
                conn.close()
                return err("Esta peça já está cadastrada nesta OS.")

            cursor.execute(
                """
                INSERT INTO shopping_list (os_id, produto_id, produto_nome, quantidade_solicitada, prioridade, observacao)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (os_id or None, produto_id, produto_nome, quantidade, prioridade, observacao),
            )
            new_id = cursor.lastrowid
            _log_shopping(cursor, new_id, session.get("usuario_id"), "create", antes=None, depois=str({"quantidade": quantidade, "prioridade": prioridade}))
            conn.commit()
            conn.close()
            return ok(id=new_id)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao criar item: {exc}")

    @api.route("/shopping-list/<int:item_id>", methods=["PUT"])
    def shopping_update(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            body = request.get_json(silent=True) or {}
            quantidade = body.get("quantidade_solicitada")
            prioridade = (body.get("prioridade") or "").strip().upper()
            observacao = body.get("observacao")

            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT quantidade_solicitada, prioridade, observacao FROM shopping_list WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return err("Item não encontrado", 404)
            antes = {"quantidade_solicitada": row[0], "prioridade": row[1], "observacao": row[2]}

            updates = []
            params = []
            if quantidade is not None:
                try:
                    q = int(quantidade)
                except Exception:
                    q = None
                if q is None or q < 0:
                    conn.close()
                    return err("Quantidade invalida")
                updates.append("quantidade_solicitada = ?")
                params.append(q)
            if prioridade:
                if prioridade not in SHOPPING_PRIORITIES:
                    prioridade = "NORMAL"
                updates.append("prioridade = ?")
                params.append(prioridade)
            if observacao is not None:
                updates.append("observacao = ?")
                params.append(observacao)

            if updates:
                params.extend([datetime.now().isoformat(), item_id])
                cursor.execute(f"UPDATE shopping_list SET {', '.join(updates)}, updated_at=? WHERE id=?", tuple(params))
                _log_shopping(cursor, item_id, session.get("usuario_id"), "update", antes=str(antes), depois=str(body))
                conn.commit()

            conn.close()
            return ok(id=item_id)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao atualizar item: {exc}")

    @api.route("/shopping-list/<int:item_id>/status", methods=["PATCH"])
    def shopping_patch_status(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        body = request.get_json(silent=True) or {}
        novo = (body.get("status") or "").strip().upper()
        quantidade_recebida = body.get("quantidade_recebida")

        if novo not in SHOPPING_STATUSES:
            return err("Status invalido")

        usuario_id = session.get("usuario_id")
        perfil = session.get("usuario_perfil")

        # só perfis autorizados podem alterar status/cancel/arquivar
        if perfil not in ("admin", "tecnico", "comprador"):
            return err("Permissao negada", 403)

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT status, responsavel_id FROM shopping_list WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return err("Item nao encontrado", 404)
            atual_status, atual_responsavel = row[0], row[1]

        # Bloqueio de compras simultâneas
            if atual_status == 'EM_COMPRA' and novo == 'EM_COMPRA' and atual_responsavel and atual_responsavel != usuario_id:
                # buscar nome do responsavel
                cursor.execute("SELECT nome FROM usuarios WHERE id=?", (atual_responsavel,))
                nome = cursor.fetchone()
                nome = nome[0] if nome else 'Outro usuario'
                conn.close()
                return err(f"Compra em andamento por {nome}")

            # Valida transições simples (não permite saltos de RECEBIDO -> PENDENTE, por exemplo)
            valid_transitions = {
                'PENDENTE': {'EM_COTACAO', 'EM_COMPRA', 'CANCELADO', 'ARQUIVADO'},
                'EM_COTACAO': {'EM_COMPRA', 'CANCELADO', 'ARQUIVADO'},
                'EM_COMPRA': {'COMPRADO', 'CANCELADO', 'ARQUIVADO'},
                'COMPRADO': {'RECEBIDO', 'ARQUIVADO'},
                'RECEBIDO': {'ARQUIVADO'},
                'CANCELADO': set(),
                'ARQUIVADO': set(),
            }

            if atual_status and atual_status in valid_transitions and novo not in valid_transitions.get(atual_status, set()):
                # Permite idempotência
                if novo != atual_status:
                    conn.close()
                    return err(f"Transição inválida de {atual_status} para {novo}")

            antes = atual_status
            updates = []
            params = []
            now = datetime.now().isoformat()

            if novo == 'EM_COMPRA':
                updates.append('status = ?')
                updates.append('responsavel_id = ?')
                updates.append('updated_at = ?')
                params.extend([novo, usuario_id, now])
            elif novo == 'COMPRADO':
                updates.append('status = ?')
                updates.append('quantidade_comprada = COALESCE(quantidade_comprada,0)')
                updates.append('purchased_at = ?')
                updates.append('updated_at = ?')
                params.extend([novo, now, now])
            elif novo == 'RECEBIDO':
                # pode informar quantidade_recebida
                qrecv = None
                try:
                    qrecv = int(quantidade_recebida) if quantidade_recebida is not None else None
                except Exception:
                    qrecv = None
                if qrecv is not None:
                    updates.append('quantidade_recebida = ?')
                    params.append(qrecv)
                updates.append('status = ?')
                updates.append('received_at = ?')
                updates.append('updated_at = ?')
                params.extend([novo, now, now])
            elif novo == 'CANCELADO':
                updates.append('status = ?')
                updates.append('cancelled_at = ?')
                updates.append('updated_at = ?')
                params.extend([novo, now, now])
            else:
                updates.append('status = ?')
                updates.append('updated_at = ?')
                params.extend([novo, now])

            params.append(item_id)
            cursor.execute(f"UPDATE shopping_list SET {', '.join(updates)} WHERE id=?", tuple(params))
            _log_shopping(cursor, item_id, usuario_id, 'status_change', antes=str(antes), depois=novo)
            conn.commit()
            conn.close()
            return ok(id=item_id, status=novo)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao alterar status: {exc}")

    @api.route("/shopping-list/<int:item_id>", methods=["DELETE"])
    def shopping_delete(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        perfil = session.get("usuario_perfil")
        if perfil not in ("admin", "tecnico", "comprador"):
            return err("Permissao negada", 403)
        usuario_id = session.get("usuario_id")
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM shopping_list WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return err("Item nao encontrado", 404)
            antes = row[0]
            now = datetime.now().isoformat()
            cursor.execute("UPDATE shopping_list SET status='CANCELADO', cancelled_at=?, updated_at=? WHERE id=?", (now, now, item_id))
            _log_shopping(cursor, item_id, usuario_id, 'cancel', antes=antes, depois='CANCELADO')
            conn.commit()
            conn.close()
            return ok(id=item_id)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao cancelar item: {exc}")

    @api.route("/shopping-list/grouped")
    def shopping_grouped():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(produto_id,0), produto_nome, SUM(quantidade_solicitada) as total_qtd, COUNT(DISTINCT os_id) as os_count FROM shopping_list WHERE COALESCE(status,'') != 'CANCELADO' GROUP BY COALESCE(produto_id,0), produto_nome ORDER BY total_qtd DESC"
            )
            rows = cursor.fetchall()
            conn.close()
            result = []
            for r in rows:
                result.append({"produto_id": r[0], "produto_nome": r[1] or "", "quantidade_total": int(r[2] or 0), "os_count": int(r[3] or 0)})
            return ok(grouped=result)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao agrupar: {exc}")


    @api.route('/shopping-list/<int:item_id>/logs')
    def shopping_logs(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, usuario_id, acao, valor_anterior, valor_novo, created_at FROM shopping_list_logs WHERE shopping_list_id=? ORDER BY created_at DESC", (item_id,))
            rows = cursor.fetchall()
            conn.close()
            logs = []
            for r in rows:
                va = r[3] or ""
                vn = r[4] or ""
                # tenta desserializar JSON quando aplicavel
                try:
                    va_parsed = json.loads(va) if va else va
                except Exception:
                    va_parsed = va
                try:
                    vn_parsed = json.loads(vn) if vn else vn
                except Exception:
                    vn_parsed = vn

                logs.append({
                    "id": r[0],
                    "usuario_id": r[1],
                    "acao": r[2],
                    "valor_anterior": va_parsed,
                    "valor_novo": vn_parsed,
                    "created_at": r[5],
                })
            return ok(logs=logs)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao listar logs: {exc}")


    @api.route('/shopping-list/logs/export')
    def shopping_logs_export():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        fmt = (request.args.get('format') or 'json').lower()
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT l.id, l.shopping_list_id, l.usuario_id, u.nome, l.acao, l.valor_anterior, l.valor_novo, l.created_at FROM shopping_list_logs l LEFT JOIN usuarios u ON l.usuario_id = u.id ORDER BY l.created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            records = []
            for r in rows:
                va = r[5] or ""
                vn = r[6] or ""
                try:
                    va_parsed = json.loads(va) if va else va
                except Exception:
                    va_parsed = va
                try:
                    vn_parsed = json.loads(vn) if vn else vn
                except Exception:
                    vn_parsed = vn

                records.append({
                    "id": r[0],
                    "shopping_list_id": r[1],
                    "usuario_id": r[2],
                    "usuario_nome": r[3] or "",
                    "acao": r[4],
                    "valor_anterior": va_parsed,
                    "valor_novo": vn_parsed,
                    "created_at": r[7],
                })

            if fmt == 'csv':
                # gerar CSV simples
                import io, csv
                out = io.StringIO()
                writer = csv.writer(out)
                writer.writerow(['id','shopping_list_id','usuario_id','usuario_nome','acao','valor_anterior','valor_novo','created_at'])
                for rec in records:
                    writer.writerow([
                        rec['id'], rec['shopping_list_id'], rec['usuario_id'], rec['usuario_nome'], rec['acao'],
                        json.dumps(rec['valor_anterior'], ensure_ascii=False) if not isinstance(rec['valor_anterior'], str) else rec['valor_anterior'],
                        json.dumps(rec['valor_novo'], ensure_ascii=False) if not isinstance(rec['valor_novo'], str) else rec['valor_novo'],
                        rec['created_at']
                    ])
                csv_text = out.getvalue()
                resp = Response(csv_text, mimetype='text/csv')
                resp.headers['Content-Disposition'] = 'attachment; filename="shopping_list_logs.csv"'
                return resp
            # default JSON
            return ok(records=records)
        except Exception as exc:
            try:
                conn.close()
            except Exception:
                pass
            return err(f"Erro ao exportar logs: {exc}")


    def _ordem_lista_por_id_desc(item):
        origem = (item.get("origem_integracao") or "").strip().lower()
        externo = (item.get("id_externo_integracao") or "").strip()
        interno = int(item.get("id") or 0)

        if origem == "mercado_phone" and externo.isdigit():
            return int(externo)
        return interno

    @api.route("/ordens")
    def listar_ordens():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        q = (request.args.get("q") or "").strip().lower()
        filtro_status = (request.args.get("status") or "").strip()
        filtro_tipo = (request.args.get("tipo") or "").strip()
        filtro_tecnico = (request.args.get("tecnico") or "").strip()
        filtro_vendedor = (request.args.get("vendedor") or "").strip()
        filtro_modelo = (request.args.get("modelo") or "").strip()
        data_ini = (request.args.get("data_ini") or "").strip()
        data_fim = (request.args.get("data_fim") or "").strip()

        _, mp_cfg = _carregar_config_mercadophone()
        _atualizar_runtime_mercadophone(mp_cfg)
        mp_sync_start_date = _texto_limpo_local(mercado_phone_runtime_config.get("sync_start_date") or "")

        conn = conectar()
        cursor = conn.cursor()
        dados, reparos_por_os, custos = carregar_os_com_relacoes(cursor, order_by="os.id DESC")
        conn.close()

        result = []
        for row in dados:
            os_id = row[0]
            status = normalizar_status_os(row[6])
            tipo = row[1] or ""
            tecnico = row[4] or ""
            vendedor = row[13] or ""
            modelo = row[12] or ""
            data = row[10] or ""
            origem_integracao = (row[16] or "") if len(row) > 16 else ""
            reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
            reparo_nome = texto_reparos_os(reparos_info, tipo)

            # Mantém OS antigas da integração no banco, mas oculta da listagem.
            if origem_integracao == "mercado_phone" and mp_sync_start_date:
                if (not data) or (data < mp_sync_start_date):
                    continue

            if q:
                haystack = f"{os_id} {row[2]} {row[3]} {tecnico} {status} {reparo_nome} {modelo} {vendedor} {row[14] or ''} {row[15] or ''} {row[16] or ''} {row[17] or ''}".lower()
                if q not in haystack:
                    continue
            if filtro_status and status != filtro_status:
                continue
            if filtro_tipo and tipo != filtro_tipo:
                continue
            if filtro_tecnico and tecnico != filtro_tecnico:
                continue
            if filtro_vendedor and vendedor != filtro_vendedor:
                continue
            if filtro_modelo and modelo != filtro_modelo:
                continue
            if data_ini and (not data or data < data_ini):
                continue
            if data_fim and (not data or data > data_fim):
                continue

            result.append(_os_row_to_dict(row, reparos_por_os, custos))

        result.sort(key=_ordem_lista_por_id_desc, reverse=True)

        return ok(
            ordens=result,
            total=len(result),
            abertas=len([o for o in result if status_aberto(o["status"])]),
            finalizadas=len([o for o in result if status_finalizado(o["status"])]),
        )

    @api.route("/ordens/<int:os_id>")
    def obter_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id, tipo, cliente, aparelho, tecnico, reparo_id, status,
                COALESCE(valor_cobrado, 0), COALESCE(valor_descontado, 0),
                COALESCE(custo_pecas, 0), COALESCE(data, ''),
                COALESCE(observacoes, ''), COALESCE(modelo, ''),
                COALESCE(vendedor, ''), COALESCE(cor, ''),
                COALESCE(imei, ''), COALESCE(origem_integracao, ''),
                COALESCE(id_externo_integracao, ''),
                COALESCE(data_finalizado, '')
            FROM os
            WHERE id=?
            """,
            (os_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return err("OS não encontrada.", 404)

        reparos_por_os = obter_reparos_por_os(cursor)
        cursor.execute(
            """
            SELECT estoque_id, COALESCE(peca_descricao,''), COALESCE(valor,0),
                   COALESCE(peca_fornecedor,''), COALESCE(quantidade,1), COALESCE(peca_modelo,'')
            FROM os_pecas WHERE os_id=? ORDER BY id
            """,
            (os_id,),
        )
        pecas_usadas = [
            {"estoque_id": p[0], "descricao": p[1], "valor": p[2], "fornecedor": p[3], "quantidade": p[4], "modelo": p[5]}
            for p in cursor.fetchall()
        ]
        conn.close()

        reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
        status = normalizar_status_os(row[6])
        tipo = row[1] or ""
        custo = row[9] or 0
        return ok(ordem={
            "id": row[0], "tipo": tipo, "cliente": row[2] or "",
            "aparelho": row[3] or "", "tecnico": row[4] or "",
            "status": status,
            "reparos": reparos_info.get("nomes", []),
            "reparo_ids": reparos_info.get("ids", []),
            "vendedor": row[13] or "", "cor": row[14] or "", "imei": row[15] or "",
            "modelo": row[12] or "",
            "valor_cobrado": row[7] or 0, "valor_descontado": row[8] or 0,
            "custo_pecas": custo,
            "faturamento": round(calcular_faturamento_os(row[7], row[8]), 2),
            "lucro": round(calcular_lucro_os(tipo, row[7], row[8], custo), 2),
            "data": row[10] or "", "observacoes": row[11] or "",
            "origem_integracao": row[16] or "",
            "id_externo_integracao": row[17] or "",
            "data_finalizado": row[18] or "",
            "pecas_usadas": pecas_usadas,
        })

    @api.route("/ordens/<int:os_id>/checklist")
    def obter_checklist_os(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, cliente, COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(imei, ''), COALESCE(status, ''), COALESCE(origem_integracao, ''), COALESCE(id_externo_integracao, '') FROM os WHERE id=?",
            (os_id,),
        )
        ordem = cursor.fetchone()
        if not ordem:
            conn.close()
            return err("OS não encontrada.", 404)

        checklist = _garantir_checklist_os(cursor, os_id)
        conn.commit()
        conn.close()

        return ok(
            checklist=checklist,
            ordem={
                "id": ordem[0],
                "cliente": ordem[1] or "",
                "modelo": ordem[2] or "",
                "cor": ordem[3] or "",
                "imei": ordem[4] or "",
                "status": normalizar_status_os(ordem[5]),
                "origem_integracao": ordem[6] or "",
                "id_externo_integracao": ordem[7] or "",
            },
        )

    @api.route("/ordens/<int:os_id>/checklist/token", methods=["POST"])
    def gerar_token_checklist_os(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, cliente, COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(imei, ''), COALESCE(status, '') FROM os WHERE id=?",
            (os_id,),
        )
        ordem = cursor.fetchone()
        if not ordem:
            conn.close()
            return err("OS não encontrada.", 404)

        checklist = _garantir_checklist_os(cursor, os_id)
        token = checklist.get("access_token") or secrets.token_urlsafe(18)
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            UPDATE os_checklists
            SET access_token=?, atualizado_em=?
            WHERE os_id=?
            """,
            (token, agora, os_id),
        )
        conn.commit()
        checklist = _buscar_checklist_por_os(cursor, os_id)
        conn.close()

        return ok(
            checklist=checklist,
            ordem={
                "id": ordem[0],
                "cliente": ordem[1] or "",
                "modelo": ordem[2] or "",
                "cor": ordem[3] or "",
                "imei": ordem[4] or "",
                "status": normalizar_status_os(ordem[5]),
            },
        )

    @api.route("/checklist/<token>")
    def obter_checklist_publico(token):
        token = (token or "").strip()
        if not token:
            return err("Token inválido.", 404)

        conn = conectar()
        cursor = conn.cursor()
        checklist = _buscar_checklist_por_token(cursor, token)
        if not checklist:
            conn.close()
            return err("Checklist não encontrado.", 404)

        cursor.execute(
            """
            SELECT id, cliente, COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(imei, ''), COALESCE(status, ''),
                   COALESCE(origem_integracao, ''), COALESCE(id_externo_integracao, '')
            FROM os
            WHERE id=?
            """,
            (checklist["os_id"],),
        )
        ordem = cursor.fetchone()
        conn.close()
        if not ordem:
            return err("OS não encontrada.", 404)

        return ok(
            checklist=checklist,
            ordem={
                "id": ordem[0],
                "cliente": ordem[1] or "",
                "modelo": ordem[2] or "",
                "cor": ordem[3] or "",
                "imei": ordem[4] or "",
                "status": normalizar_status_os(ordem[5]),
                "origem_integracao": ordem[6] or "",
                "id_externo_integracao": ordem[7] or "",
            },
        )

    @api.route("/checklist/<token>", methods=["POST"])
    def salvar_checklist_publico(token):
        token = (token or "").strip()
        if not token:
            return err("Token inválido.", 404)

        body = request.get_json(silent=True) or {}
        testes = body.get("testes") or {}
        if not isinstance(testes, dict):
            return err("Formato do checklist inválido.")

        status_touch = _checklist_status((testes.get("touch") or {}).get("status"))
        status_audio = _checklist_status((testes.get("audio") or {}).get("status"))
        status_microfone = _checklist_status((testes.get("microfone") or {}).get("status"))
        status_camera = _checklist_status((testes.get("camera") or {}).get("status"))
        status_botoes = _checklist_status((testes.get("botoes") or {}).get("status"))
        executado_por = (body.get("executado_por") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        origem = (body.get("origem") or "qr_publico").strip() or "qr_publico"
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resultado_json = json.dumps({"testes": testes}, ensure_ascii=True)

        conn = conectar()
        cursor = conn.cursor()
        checklist = _buscar_checklist_por_token(cursor, token)
        if not checklist:
            conn.close()
            return err("Checklist não encontrado.", 404)

        cursor.execute(
            """
            UPDATE os_checklists
            SET status_touch=?, status_audio=?, status_microfone=?, status_camera=?, status_botoes=?,
                observacoes=?, executado_por=?, origem=?, resultado_json=?, atualizado_em=?
            WHERE access_token=?
            """,
            (
                status_touch,
                status_audio,
                status_microfone,
                status_camera,
                status_botoes,
                observacoes,
                executado_por,
                origem,
                resultado_json,
                agora,
                token,
            ),
        )
        conn.commit()
        checklist_atualizado = _buscar_checklist_por_token(cursor, token)
        conn.close()
        return ok(checklist=checklist_atualizado)

    @api.route("/ordens", methods=["POST"])
    def criar_ordem():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}

        tipo = (body.get("tipo") or "").strip()
        cliente = (body.get("cliente") or "").strip()
        modelo_raw = body.get("modelo") or ""
        modelo = modelo_para_os(modelo_raw)
        cor = (body.get("cor") or "").strip()
        imei = normalizar_imei(body.get("imei"))
        aparelho = modelo
        tecnico = (body.get("tecnico") or "").strip()
        vendedor = (body.get("vendedor") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        reparo_ids = [int(x) for x in (body.get("reparo_ids") or []) if str(x).isdigit()]
        pecas_ids = [int(x) for x in (body.get("pecas_ids") or []) if str(x).isdigit()]
        valor_cobrado = float(body.get("valor_cobrado") or 0)
        valor_descontado = float(body.get("valor_descontado") or 0)
        data = (body.get("data_os") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        status_raw = (body.get("status") or "Em andamento").strip()

        # Upgrade → internal
        if tipo.lower() == "upgrade":
            tipo = "Assistencia"
            cliente = "IR Phones"
        if body.get("interna_ir_phones"):
            tipo = "Assistencia"
            cliente = "IR Phones"
            vendedor = ""

        status = normalizar_status_os(status_raw)

        if not tipo or not cliente or not modelo or not tecnico:
            return err("Preencha tipo, cliente, modelo e técnico.")
        if not reparo_ids:
            return err("Selecione ao menos um reparo.")
        if not vendedor_valido(vendedor, vendedores) and cliente != "IR Phones":
            return err("Vendedor inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if not validar_reparo_ids(cursor, reparo_ids):
                return err("Um ou mais reparos não existem.")

            cursor.execute(
                """
                INSERT INTO os (tipo, cliente, aparelho, tecnico, reparo_id, status,
                    valor_cobrado, valor_descontado, custo_pecas, data, observacoes, modelo, vendedor, cor, imei)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (tipo, cliente, aparelho, tecnico, reparo_ids[0], status,
                 valor_cobrado, valor_descontado, 0, data, observacoes, modelo, vendedor, cor, imei),
            )
            novo_id = cursor.lastrowid
            salvar_reparos_os(cursor, novo_id, reparo_ids)

            custo_total = 0.0
            for peca_id in pecas_ids:
                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row else ""
                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    return err("Peça incompatível com o modelo da OS.")
                ok_peca, erro_peca = consumir_peca_da_os(cursor, novo_id, peca_id)
                if not ok_peca:
                    conn.rollback()
                    return err(erro_peca)
                custo_total += valor_peca

            cursor.execute("UPDATE os SET custo_pecas=? WHERE id=?", (round(custo_total, 2), novo_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(os_id=novo_id), 201

    @api.route("/ordens/<int:os_id>", methods=["PUT"])
    def atualizar_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}

        tipo = (body.get("tipo") or "").strip()
        cliente = (body.get("cliente") or "").strip()
        modelo_raw = body.get("modelo") or ""
        modelo = modelo_para_os(modelo_raw)
        cor = (body.get("cor") or "").strip()
        imei = normalizar_imei(body.get("imei"))
        tecnico = (body.get("tecnico") or "").strip()
        vendedor = (body.get("vendedor") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        reparo_ids = [int(x) for x in (body.get("reparo_ids") or []) if str(x).isdigit()]
        pecas_ids = [int(x) for x in (body.get("pecas_ids") or []) if str(x).isdigit()]
        valor_cobrado = float(body.get("valor_cobrado") or 0)
        valor_descontado = float(body.get("valor_descontado") or 0)
        data_os = (body.get("data_os") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        status = normalizar_status_os(body.get("status") or "", status_padrao="")
        aparelho = modelo

        if not tipo or not cliente or not modelo or not tecnico or not status:
            return err("Preencha todos os campos obrigatórios.")
        if not reparo_ids:
            return err("Selecione ao menos um reparo.")
        if not vendedor_valido(vendedor, vendedores) and cliente != "IR Phones":
            return err("Vendedor inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if not validar_reparo_ids(cursor, reparo_ids):
                return err("Um ou mais reparos não existem.")

            cursor.execute("SELECT status, COALESCE(data_finalizado,'') FROM os WHERE id=?", (os_id,))
            row_atual = cursor.fetchone()
            if not row_atual:
                return err("OS não encontrada.", 404)

            status_atual = normalizar_status_os(row_atual[0])
            data_finalizado_atual = row_atual[1]

            data_finalizado_valor = None
            if status_finalizado(status):
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                """
                UPDATE os SET tipo=?,cliente=?,aparelho=?,tecnico=?,reparo_id=?,status=?,
                    valor_cobrado=?,valor_descontado=?,data=?,observacoes=?,modelo=?,vendedor=?,
                    cor=?,imei=?,data_finalizado=?
                WHERE id=?
                """,
                (tipo, cliente, aparelho, tecnico, reparo_ids[0], status,
                 valor_cobrado, valor_descontado, data_os, observacoes, modelo, vendedor,
                 cor, imei, data_finalizado_valor, os_id),
            )
            salvar_reparos_os(cursor, os_id, reparo_ids)

            if not status_cancelado(status_atual):
                devolver_pecas_da_os(cursor, os_id, "devolucao-edicao")
            cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))

            custo_total = 0.0
            for peca_id in pecas_ids:
                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row else ""
                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    return err("Peça incompatível com o modelo da OS.")
                if status_cancelado(status):
                    ok_peca, erro_peca = adicionar_peca_os_sem_consumir(cursor, os_id, peca_id)
                else:
                    ok_peca, erro_peca = consumir_peca_da_os(cursor, os_id, peca_id)
                if not ok_peca:
                    conn.rollback()
                    return err(erro_peca)
                custo_total += valor_peca

            cursor.execute("UPDATE os SET custo_pecas=? WHERE id=?", (round(custo_total, 2), os_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/ordens/<int:os_id>", methods=["DELETE"])
    def deletar_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT status, COALESCE(origem_integracao, ''), COALESCE(id_externo_integracao, '')
                FROM os
                WHERE id=?
                """,
                (os_id,),
            )
            row = cursor.fetchone()
            if row:
                s = normalizar_status_os(row[0])
                if not status_finalizado(s) and not status_cancelado(s):
                    devolver_pecas_da_os(cursor, os_id, "devolucao")

                origem_integracao = (row[1] or "").strip().lower()
                id_externo_integracao = (row[2] or "").strip()
                if origem_integracao == "mercado_phone" and id_externo_integracao:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO integracao_os_vistas (origem, id_externo, primeira_visualizacao)
                        VALUES (?, ?, ?)
                        """,
                        ("mercado_phone_bloqueada", id_externo_integracao, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    )
            cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os_checklists WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os WHERE id=?", (os_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/ordens/<int:os_id>/status", methods=["PATCH"])
    def atualizar_status_os(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}
        status = normalizar_status_os(body.get("status") or "", status_padrao="")
        if not status:
            return err("Status inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT status, COALESCE(data_finalizado,'') FROM os WHERE id=?", (os_id,))
            row = cursor.fetchone()
            if not row:
                return err("OS não encontrada.", 404)
            status_atual = normalizar_status_os(row[0])
            data_finalizado_atual = row[1]

            data_finalizado_valor = None
            if status_finalizado(status):
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                "UPDATE os SET status=?, data_finalizado=? WHERE id=?",
                (status, data_finalizado_valor, os_id),
            )

            if status_cancelado(status) and not status_cancelado(status_atual):
                devolver_pecas_da_os(cursor, os_id, "devolucao")

            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/ordens/historico-cliente")
    def historico_cliente():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        cliente = (request.args.get("cliente") or "").strip()
        excluir_id = request.args.get("excluir_id", type=int)
        if not cliente:
            return ok(ordens=[])

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, tipo, modelo, data, status
            FROM os
            WHERE lower(cliente) = lower(?) AND id != ?
            ORDER BY id DESC LIMIT 10
            """,
            (cliente, excluir_id or -1),
        )
        rows = cursor.fetchall()
        reparos_por_os = obter_reparos_por_os(cursor)
        conn.close()

        ordens = []
        for r in rows:
            rinfo = reparos_por_os.get(r[0], {"nomes": []})
            ordens.append({
                "id": r[0], "tipo": r[1] or "", "modelo": r[2] or "",
                "data": r[3] or "", "status": normalizar_status_os(r[4]),
                "reparos": rinfo.get("nomes", []),
            })
        return ok(ordens=ordens)

    # ── STOCK ──────────────────────────────────────────────────────────────

    @api.route("/estoque")
    def listar_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        filtro_modelo = (request.args.get("modelo") or "").strip()
        filtro_tipo = (request.args.get("tipo") or "").strip()
        filtro_qualidade = (request.args.get("qualidade") or "").strip()
        filtro_status = (request.args.get("status") or "").strip().lower()
        include_zerados = str(request.args.get("include_zerados") or "").strip().lower() in {"1", "true", "sim", "yes"}
        q = (request.args.get("q") or "").strip().lower()

        agora = datetime.now()
        corte_30 = (agora - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        corte_90 = (agora - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")

        conn = conectar()
        cursor = conn.cursor()

        params = []
        where = []
        if filtro_modelo == "Universal":
            where.append("COALESCE(modelo,'') = ''")
        elif filtro_modelo:
            where.append("COALESCE(modelo,'') = ?")
            params.append(normalizar_modelo_iphone(filtro_modelo) or filtro_modelo)

        if filtro_tipo:
            where.append("COALESCE(tipo,'Outros') = ?")
            params.append(_normalizar_tipo_estoque(filtro_tipo))

        if filtro_qualidade:
            where.append("COALESCE(qualidade,'Padrao') = ?")
            params.append(_normalizar_qualidade_estoque(filtro_qualidade))

        clause = f"WHERE {' AND '.join(where)}" if where else ""

        cursor.execute(
            f"""
            SELECT
                id,
                descricao,
                valor,
                fornecedor,
                quantidade,
                data_compra,
                COALESCE(modelo,''),
                COALESCE(tipo,'Outros'),
                COALESCE(qualidade,'Padrao'),
                (
                    SELECT COALESCE(MAX(m.data), '')
                    FROM movimentacoes m
                    WHERE m.estoque_id = estoque.id
                ) AS ultima_movimentacao,
                (
                    SELECT COALESCE(SUM(m.quantidade), 0)
                    FROM movimentacoes m
                    WHERE m.estoque_id = estoque.id
                      AND m.tipo = 'saida'
                      AND m.data >= ?
                ) AS consumo_30d,
                (
                    SELECT COALESCE(SUM(m.quantidade), 0)
                    FROM movimentacoes m
                    WHERE m.estoque_id = estoque.id
                      AND m.tipo = 'saida'
                      AND m.data >= ?
                ) AS consumo_90d
            FROM estoque {clause}
            ORDER BY id DESC
            """,
            [*params, corte_30, corte_90],
        )
        itens = []
        for r in cursor.fetchall():
            status_item = _status_item_estoque(r[4] or 0, r[9] or "", r[11] or 0)
            quantidade_item = int(r[4] or 0)
            if quantidade_item <= 0 and not include_zerados:
                continue
            item = {
                "id": r[0],
                "descricao": r[1] or "",
                "valor": round(r[2] or 0, 2),
                "fornecedor": r[3] or "",
                "quantidade": quantidade_item,
                "data_compra": r[5] or "",
                "modelo": r[6] or "",
                "tipo": r[7] or "Outros",
                "qualidade": r[8] or "Padrao",
                "ultima_movimentacao": r[9] or "",
                "consumo_30d": int(r[10] or 0),
                "consumo_90d": int(r[11] or 0),
                "status_estoque": status_item,
            }
            itens.append(item)

        if filtro_status:
            itens = [i for i in itens if (i.get("status_estoque") or "") == filtro_status]

        if q:
            itens = [
                i
                for i in itens
                if q in f"{i['descricao']} {i['modelo']} {i['fornecedor']} {i['tipo']} {i['qualidade']}".lower()
            ]

        # Summary stats
        cursor.execute("SELECT COALESCE(SUM(valor*quantidade),0) FROM estoque")
        valor_total = cursor.fetchone()[0] or 0
        conn.close()

        total_lotes = len(itens)
        total_unidades = sum(i["quantidade"] for i in itens)
        criticos = len([i for i in itens if i["quantidade"] <= 2])

        return ok(
            itens=itens,
            total_lotes=total_lotes,
            total_unidades=total_unidades,
            valor_total=round(valor_total, 2),
            criticos=criticos,
        )

    @api.route("/estoque/reposicao-sugerida")
    def reposicao_sugerida_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        dias_base = int(request.args.get("dias") or 30)
        if dias_base < 7:
            dias_base = 7
        if dias_base > 120:
            dias_base = 120

        corte = (datetime.now() - timedelta(days=dias_base)).strftime("%Y-%m-%d %H:%M:%S")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.id,
                COALESCE(e.sku, ''),
                COALESCE(e.descricao, ''),
                COALESCE(e.modelo, ''),
                COALESCE(e.tipo, 'Outros'),
                COALESCE(e.qualidade, 'Padrao'),
                COALESCE(e.quantidade, 0),
                COALESCE(e.valor, 0),
                COALESCE(SUM(CASE WHEN m.tipo='saida' THEN m.quantidade ELSE 0 END), 0) AS consumo_periodo
            FROM estoque e
            LEFT JOIN movimentacoes m
                ON m.estoque_id = e.id
               AND m.data >= ?
            GROUP BY e.id
            ORDER BY consumo_periodo DESC, e.id DESC
            """,
            (corte,),
        )
        rows = cursor.fetchall()
        conn.close()

        itens = []
        for r in rows:
            quantidade = int(r[6] or 0)
            consumo_periodo = int(r[8] or 0)
            if consumo_periodo <= 0:
                continue
            if quantidade > 2:
                continue

            consumo_mensal = (consumo_periodo / max(dias_base, 1)) * 30.0
            estoque_alvo = max(1, int(math.ceil(consumo_mensal * 1.5)))
            sugestao = max(1, estoque_alvo - quantidade)

            if quantidade <= 0 and consumo_mensal >= 6:
                prioridade = "alta"
            elif quantidade <= 1 and consumo_mensal >= 3:
                prioridade = "media"
            else:
                prioridade = "baixa"

            itens.append(
                {
                    "id": r[0],
                    "sku": r[1],
                    "descricao": r[2],
                    "modelo": r[3],
                    "tipo": r[4],
                    "qualidade": r[5],
                    "quantidade_atual": quantidade,
                    "valor_medio": round(float(r[7] or 0), 2),
                    "consumo_periodo": consumo_periodo,
                    "consumo_mensal_estimado": round(consumo_mensal, 2),
                    "estoque_alvo": estoque_alvo,
                    "sugestao_reposicao": sugestao,
                    "prioridade": prioridade,
                }
            )

        return ok(itens=itens, dias_base=dias_base)

    @api.route("/estoque", methods=["POST"])
    def criar_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        modelo = normalizar_modelo_iphone(body.get("modelo") or "") or (body.get("modelo") or "").strip()
        tipo = _normalizar_tipo_estoque(body.get("tipo"))
        qualidade = _normalizar_qualidade_estoque(body.get("qualidade"))
        sku = (body.get("sku") or "").strip().upper()
        valor = float(body.get("valor") or 0)
        fornecedor = (body.get("fornecedor") or "Nao informado").strip()
        quantidade = int(body.get("quantidade") or 0)
        data_compra = (body.get("data_compra") or "").strip() or datetime.now().strftime("%Y-%m-%d")

        if not descricao or valor <= 0 or quantidade < 0:
            return err("Preencha descrição, valor e quantidade.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO estoque (descricao, modelo, valor, fornecedor, quantidade, data_compra, sku, tipo, qualidade)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (descricao, modelo, valor, fornecedor, max(0, quantidade), data_compra, sku, tipo, qualidade),
            )
            novo_id = cursor.lastrowid
            if quantidade > 0:
                cursor.execute(
                    """
                    INSERT INTO estoque_lotes (
                        estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        novo_id,
                        fornecedor,
                        valor,
                        quantidade,
                        quantidade,
                        data_compra,
                        "compra inicial",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                registrar_movimentacao(cursor, novo_id, "entrada", quantidade)
            _recalcular_custo_medio(cursor, novo_id)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api.route("/estoque/<int:item_id>", methods=["PUT"])
    def atualizar_estoque(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        modelo = normalizar_modelo_iphone(body.get("modelo") or "") or (body.get("modelo") or "").strip()
        tipo = _normalizar_tipo_estoque(body.get("tipo"))
        qualidade = _normalizar_qualidade_estoque(body.get("qualidade"))
        sku = (body.get("sku") or "").strip().upper()
        valor = float(body.get("valor") or 0)
        fornecedor = (body.get("fornecedor") or "Nao informado").strip()
        quantidade_nova = int(body.get("quantidade") or 0)
        data_compra = (body.get("data_compra") or "").strip() or datetime.now().strftime("%Y-%m-%d")

        if not descricao or valor <= 0:
            return err("Preencha descrição e valor.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT quantidade, descricao, sku FROM estoque WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                return err("Item não encontrado.", 404)
            qtd_antiga = row[0] or 0
            sku_atual = (row[2] or "").strip().upper()
            if not sku:
                sku = sku_atual

            # Permitir sempre editar, mesmo se existir outro com modelo/tipo/qualidade igual

            cursor.execute(
                """
                UPDATE estoque
                SET descricao=?, modelo=?, valor=?, fornecedor=?, quantidade=?, data_compra=?, sku=?, tipo=?, qualidade=?
                WHERE id=?
                """,
                (descricao, modelo, valor, fornecedor, max(0, quantidade_nova), data_compra, sku, tipo, qualidade, item_id),
            )
            diff = quantidade_nova - qtd_antiga
            if diff != 0:
                tipo_mov = "entrada" if diff > 0 else "saida"
                registrar_movimentacao(cursor, item_id, tipo_mov, abs(diff))
                if diff > 0:
                    cursor.execute(
                        """
                        INSERT INTO estoque_lotes (
                            estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item_id,
                            fornecedor,
                            valor,
                            diff,
                            diff,
                            data_compra,
                            "ajuste manual",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                else:
                    restante = abs(diff)
                    cursor.execute(
                        """
                        SELECT id, COALESCE(quantidade_disponivel, 0)
                        FROM estoque_lotes
                        WHERE estoque_id=? AND COALESCE(quantidade_disponivel, 0) > 0
                        ORDER BY COALESCE(data_compra, '') ASC, id ASC
                        """,
                        (item_id,),
                    )
                    for lote_id, disponivel in cursor.fetchall():
                        if restante <= 0:
                            break
                        usar = min(restante, int(disponivel or 0))
                        if usar <= 0:
                            continue
                        cursor.execute(
                            "UPDATE estoque_lotes SET quantidade_disponivel = MAX(0, quantidade_disponivel - ?) WHERE id=?",
                            (usar, lote_id),
                        )
                        restante -= usar
            _recalcular_custo_medio(cursor, item_id)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/estoque/<int:item_id>", methods=["DELETE"])
    def deletar_estoque(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM os_pecas p JOIN os o ON p.os_id=o.id WHERE p.estoque_id=? AND o.status NOT IN ('Finalizado','Cancelado')",
                (item_id,),
            )
            em_uso = cursor.fetchone()[0] or 0
            if em_uso > 0:
                return err("Não é possível excluir: peça está em uso em OS abertas.")
            cursor.execute("DELETE FROM estoque_lotes WHERE estoque_id=?", (item_id,))
            cursor.execute("DELETE FROM estoque WHERE id=?", (item_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/estoque/movimentacoes")
    def movimentacoes():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.estoque_id, m.tipo, m.quantidade, m.data,
                   COALESCE(e.descricao, '')
            FROM movimentacoes m
            LEFT JOIN estoque e ON e.id = m.estoque_id
            ORDER BY m.id DESC LIMIT 30
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return ok(movimentacoes=[
            {"id": r[0], "estoque_id": r[1], "tipo": r[2], "quantidade": r[3], "data": r[4], "descricao": r[5]}
            for r in rows
        ])

    # ── REPAIR TYPES ───────────────────────────────────────────────────────

    @api.route("/reparos")
    def listar_reparos():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM reparos ORDER BY nome")
        rows = cursor.fetchall()
        conn.close()
        return ok(reparos=[{"id": r[0], "nome": r[1]} for r in rows])

    @api.route("/reparos", methods=["POST"])
    def criar_reparo():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        if not nome:
            return err("Informe o nome do reparo.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?)", (nome,))
            if cursor.fetchone():
                return err("Esse tipo de reparo já existe.")
            cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (nome,))
            novo_id = cursor.lastrowid
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api.route("/reparos/<int:reparo_id>", methods=["PUT"])
    def atualizar_reparo(reparo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        if not nome:
            return err("Informe um nome válido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?) AND id<>?", (nome, reparo_id))
            if cursor.fetchone():
                return err("Já existe um reparo com esse nome.")
            cursor.execute("UPDATE reparos SET nome=? WHERE id=?", (nome, reparo_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/reparos/<int:reparo_id>", methods=["DELETE"])
    def deletar_reparo(reparo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM os_reparos WHERE reparo_id=?", (reparo_id,))
            if (cursor.fetchone()[0] or 0) > 0:
                return err("Não é possível excluir: reparo vinculado a OS.")
            cursor.execute("DELETE FROM reparos WHERE id=?", (reparo_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    # ── OPERATIONAL COSTS ──────────────────────────────────────────────────

    @api.route("/custos")
    def listar_custos():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = listar_custos_operacionais(start_date, end_date)
        return ok(**resumo)

    @api.route("/custos", methods=["POST"])
    def criar_custo():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        categoria = (body.get("categoria") or "Outros").strip()
        valor = float(body.get("valor") or 0)
        data = (body.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        observacoes = (body.get("observacoes") or "").strip()

        if not descricao or valor <= 0:
            return err("Informe descrição e valor maior que zero.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO custos_operacionais (descricao, categoria, valor, data, observacoes) VALUES (?,?,?,?,?)",
                (descricao, categoria, valor, data, observacoes),
            )
            novo_id = cursor.lastrowid
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api.route("/custos/<int:custo_id>", methods=["PUT"])
    def atualizar_custo(custo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        categoria = (body.get("categoria") or "Outros").strip()
        valor = float(body.get("valor") or 0)
        data = (body.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        observacoes = (body.get("observacoes") or "").strip()

        if not descricao or valor <= 0:
            return err("Informe descrição e valor maior que zero.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM custos_operacionais WHERE id=?", (custo_id,))
            if not cursor.fetchone():
                return err("Custo não encontrado.", 404)

            cursor.execute(
                """
                UPDATE custos_operacionais
                SET descricao=?, categoria=?, valor=?, data=?, observacoes=?
                WHERE id=?
                """,
                (descricao, categoria, valor, data, observacoes, custo_id),
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/custos/<int:custo_id>", methods=["DELETE"])
    def deletar_custo(custo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM custos_operacionais WHERE id=?", (custo_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    # ── PRICE TABLES ───────────────────────────────────────────────────────

    @api.route("/precos")
    def listar_precos():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        return ok(tabelas=carregar_tabelas_preco())

    @api.route("/precos", methods=["POST"])
    def salvar_preco():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        tabela = (body.get("tabela") or "").strip()
        servico = (body.get("servico") or "").strip().upper()
        modelo = (body.get("modelo") or "").strip()
        valor = float(body.get("valor") or -1)

        if tabela not in ("ir_phones", "clientes"):
            return err("Tabela inválida.")
        if not servico or not modelo or valor < 0:
            return err("Preencha serviço, modelo e valor.")

        tabelas = carregar_tabelas_preco()
        tabelas.setdefault(tabela, {}).setdefault(servico, {})[modelo] = valor
        salvar_tabelas_preco(tabelas)
        return ok()

    @api.route("/precos/excluir", methods=["POST"])
    def excluir_preco():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        tabela = (body.get("tabela") or "").strip()
        servico = (body.get("servico") or "").strip()
        modelo = (body.get("modelo") or "").strip()

        if tabela not in ("ir_phones", "clientes"):
            return err("Tabela inválida.")

        tabelas = carregar_tabelas_preco()
        if tabela in tabelas and servico in tabelas[tabela] and modelo in tabelas[tabela][servico]:
            del tabelas[tabela][servico][modelo]
            if not tabelas[tabela][servico]:
                del tabelas[tabela][servico]
            salvar_tabelas_preco(tabelas)
            return ok()

        return err("Entrada não encontrada.", 404)

    @api.route("/precos/sugerir")
    def sugerir_preco():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        modelo = (request.args.get("modelo") or "").strip()
        tabela = (request.args.get("tabela") or "clientes").strip()
        reparo_ids_raw = (request.args.get("reparo_ids") or "").strip()

        if not modelo or not reparo_ids_raw:
            return ok(valor=0, encontrado=False)

        reparo_ids = [int(x) for x in reparo_ids_raw.split(",") if x.strip().isdigit()]
        if not reparo_ids:
            return ok(valor=0, encontrado=False)

        if tabela not in ("ir_phones", "clientes"):
            tabela = "clientes"

        conn = conectar()
        cursor = conn.cursor()
        placeholders = ",".join("?" * len(reparo_ids))
        cursor.execute(f"SELECT nome FROM reparos WHERE id IN ({placeholders})", reparo_ids)
        nomes = [r[0].upper() for r in cursor.fetchall()]
        conn.close()

        tabelas = carregar_tabelas_preco()
        total, encontrou = sugerir_preco_tabela(tabelas, tabela, modelo, nomes)
        return ok(valor=round(total, 2), encontrado=encontrou)

    # ── WARRANTIES ─────────────────────────────────────────────────────────

    @api.route("/garantias")
    def listar_garantias():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        q = (request.args.get("q") or "").strip().lower()
        hoje = datetime.now().date()
        garantia_dias = 90

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, cliente, modelo, tecnico,
                   COALESCE(data_finalizado,''), COALESCE(data,''), COALESCE(imei,''),
                   COALESCE(origem_integracao,''), COALESCE(id_externo_integracao,'')
            FROM os
            WHERE status='Finalizado'
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        reparos_por_os = obter_reparos_por_os(cursor)
        conn.close()

        result = []
        for r in rows:
            os_id, cliente, modelo, tecnico, data_fin, data_os, imei, origem_integracao, id_externo_integracao = r
            if (cliente or "").strip().lower() == "ir phones":
                continue
            if q and q not in f"{cliente} {modelo} {imei}".lower():
                continue

            base = parse_data_ymd(data_fin) or parse_data_ymd(data_os)
            dias_restantes = None
            label = "Sem data"
            color = "gray"
            if base:
                fim = (base + timedelta(days=garantia_dias)).date()
                dias_restantes = (fim - hoje).days
                if dias_restantes < 0:
                    label = "Vencida"
                    color = "red"
                elif dias_restantes <= 7:
                    label = f"Vence em {dias_restantes}d"
                    color = "amber"
                else:
                    label = f"{dias_restantes} dias"
                    color = "green"

            rinfo = reparos_por_os.get(os_id, {"nomes": []})
            result.append({
                "id": os_id, "cliente": cliente or "", "modelo": modelo or "",
                "tecnico": tecnico or "", "imei": imei or "",
                "data_finalizado": data_fin or data_os,
                "reparos": rinfo.get("nomes", []),
                "origem_integracao": origem_integracao or "",
                "id_externo_integracao": id_externo_integracao or "",
                "garantia": {"dias_restantes": dias_restantes, "label": label, "color": color},
            })

        total = len(result)
        ativas = len([r for r in result if r["garantia"]["color"] == "green"])
        vencendo = len([r for r in result if r["garantia"]["color"] == "amber"])
        vencidas = len([r for r in result if r["garantia"]["color"] == "red"])

        return ok(
            ordens=result, total=total,
            ativas=ativas, vencendo=vencendo, vencidas=vencidas,
        )

    # ── REPORTS ────────────────────────────────────────────────────────────

    @api.route("/relatorios/ir-phones")
    def relatorio_ir_phones():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = agrupar_relatorio_ir_phones(start_date, end_date)
        total_os = sum(v["total_os"] for v in resumo.values())
        total_lucro = sum(v["lucro"] for v in resumo.values())
        return ok(meses=resumo, total_os=total_os, total_lucro=round(total_lucro, 2))

    @api.route("/relatorios/tecnicos")
    def relatorio_tecnicos():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = agrupar_relatorio_tecnicos(start_date, end_date)
        return ok(meses=resumo)

    @api.route("/relatorios/custos-operacionais")
    def relatorio_custos_operacionais():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = agrupar_relatorio_custos_operacionais(start_date, end_date)
        total_lancamentos = sum(v["total_itens"] for v in resumo.values())
        total_custos = sum(v["total_valor"] for v in resumo.values())

        categorias = {}
        for mes in resumo.values():
            for categoria, valor in (mes.get("categorias") or {}).items():
                categorias[categoria] = categorias.get(categoria, 0) + valor

        categorias_ordenadas = dict(sorted(categorias.items(), key=lambda item: (-item[1], item[0])))
        return ok(
            meses=resumo,
            total_lancamentos=total_lancamentos,
            total_custos=round(total_custos, 2),
            categorias=categorias_ordenadas,
        )

    @api.route("/relatorios/pdf/ir-phones")
    def pdf_ir_phones():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        linhas = montar_linhas_relatorio_ir_phones(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - IR Phones",
            f"Servicos finalizados, gastos com pecas e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-ir-phones.pdf",
        )

    @api.route("/relatorios/pdf/tecnicos")
    def pdf_tecnicos():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        linhas = montar_linhas_relatorio_tecnicos(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - Tecnicos",
            f"Servicos finalizados por tecnico com gastos e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-tecnicos.pdf",
        )

    @api.route("/relatorios/pdf/custos-operacionais")
    def pdf_custos_operacionais():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        linhas = montar_linhas_relatorio_custos_operacionais(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - Custos Operacionais",
            f"Custos operacionais agregados por mes e categoria. Periodo: {periodo}",
            linhas,
            "relatorio-custos-operacionais.pdf",
        )

    # ── USERS ──────────────────────────────────────────────────────────────

    @api.route("/usuarios")
    def listar_usuarios():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, usuario, perfil, ativo FROM usuarios ORDER BY nome")
        rows = cursor.fetchall()
        conn.close()
        return ok(usuarios=[
            {"id": r[0], "nome": r[1], "usuario": r[2], "perfil": r[3], "ativo": bool(r[4])}
            for r in rows
        ])

    @api.route("/usuarios", methods=["POST"])
    def criar_usuario():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        usuario_txt = (body.get("usuario") or "").strip()
        senha_txt = (body.get("senha") or "").strip()
        perfil = body.get("perfil") or "tecnico"

        if not nome or not usuario_txt or not senha_txt:
            return err("Preencha nome, usuário e senha.")
        if perfil not in ("admin", "tecnico", "vendedor"):
            perfil = "tecnico"

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?,?,?,?)",
                (nome, usuario_txt, generate_password_hash(senha_txt), perfil),
            )
            novo_id = cursor.lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            return err("Usuário já existe.")
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api.route("/usuarios/<int:uid>", methods=["PUT"])
    def atualizar_usuario(uid):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        perfil = body.get("perfil") or "tecnico"
        senha_nova = (body.get("senha_nova") or "").strip()
        ativo = bool(body.get("ativo", True))

        if perfil not in ("admin", "tecnico", "vendedor"):
            perfil = "tecnico"
        if uid == session.get("usuario_id") and not ativo:
            return err("Você não pode desativar sua própria conta.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if senha_nova:
                cursor.execute(
                    "UPDATE usuarios SET nome=?,perfil=?,senha_hash=?,ativo=? WHERE id=?",
                    (nome, perfil, generate_password_hash(senha_nova), 1 if ativo else 0, uid),
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET nome=?,perfil=?,ativo=? WHERE id=?",
                    (nome, perfil, 1 if ativo else 0, uid),
                )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/usuarios/<int:uid>", methods=["DELETE"])
    def deletar_usuario(uid):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        if uid == session.get("usuario_id"):
            return err("Você não pode excluir sua própria conta.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id=?", (uid,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    # ── BACKUP ─────────────────────────────────────────────────────────────

    @api.route("/backup/criar", methods=["POST"])
    def criar_backup_api():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        try:
            os.makedirs(backup_dir, exist_ok=True)
            body = request.get_json(silent=True) or {}
            versao_bruta = _texto_limpo_local(body.get("versao"))
            versao = re.sub(r"[^A-Za-z0-9._-]", "", versao_bruta)[:40]
            nome_arquivo = None
            if versao:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                nome_arquivo = f"backup-v{versao}-{stamp}.db"

            info = criar_backup(
                backup_dir, google_drive_backup_dir,
                conectar,
                nome_arquivo=nome_arquivo,
            )
            if backup_email_senha_app:
                enviar_backup_email(
                    info["destino_local"], backup_email_remetente,
                    backup_email_senha_app, backup_email_destino,
                )
            return ok(
                arquivo=info["nome"],
                destino_drive=bool(info.get("destino_drive")),
                erro_drive=info.get("erro_drive", ""),
            )
        except Exception as exc:
            return err(str(exc))

    @api.route("/backup/listar")
    def listar_backups():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        backups = []
        if os.path.isdir(backup_dir):
            for f in os.listdir(backup_dir):
                if f.endswith(".db"):
                    full = os.path.join(backup_dir, f)
                    backups.append({
                        "nome": f,
                        "tamanho": os.path.getsize(full),
                        "data": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M"),
                        "modificado_em": os.path.getmtime(full),
                    })

        backups.sort(key=lambda item: item["modificado_em"], reverse=True)
        for item in backups:
            item.pop("modificado_em", None)

        return ok(backups=backups[:30])

    @api.route("/backup/download/<path:filename>")
    def download_backup(filename):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        return send_from_directory(backup_dir, filename, as_attachment=True)

    @api.route("/backup/restaurar", methods=["POST"])
    def restaurar_backup_upload():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        if "arquivo" not in request.files:
            return err("Envie o arquivo no campo 'arquivo'.", 400)
        f = request.files["arquivo"]
        if not f.filename or not f.filename.lower().endswith(".db"):
            return err("O arquivo deve ter extensão .db", 400)
        # Valida que é um SQLite legítimo lendo o magic header
        header = f.read(16)
        if not header.startswith(b"SQLite format 3"):
            return err("Arquivo inválido: não é um banco SQLite.", 400)
        f.seek(0)
        import sqlite3 as _sqlite3, tempfile, shutil
        # Salva em temp para validar antes de sobrescrever
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        try:
            f.save(tmp.name)
            # Testa integridade
            test_conn = _sqlite3.connect(tmp.name)
            result = test_conn.execute("PRAGMA integrity_check").fetchone()
            test_conn.close()
            if result[0] != "ok":
                return err(f"Banco corrompido: {result[0]}", 400)
            # Faz backup do atual antes de substituir
            if os.path.exists(db_path):
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(db_path, os.path.join(backup_dir, f"pre-restore-{stamp}.db"))
            shutil.copy2(tmp.name, db_path)
            # Garante colunas/tabelas novas quando o backup é de schema antigo.
            forcar_migracao_schema()
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
        return ok(mensagem="Backup restaurado com sucesso.")



    @api.route("/integracoes/mercadophone/sincronizar", methods=["POST"])
    def sincronizar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            _, mp_cfg = _carregar_config_mercadophone()
            status_cfg = _atualizar_runtime_mercadophone(mp_cfg)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            resultado = sincronizar_mercado_phone(
                conectar, mercado_phone_runtime_config, mercado_phone_helpers
            )
            return ok(resultado=resultado)
        except Exception as exc:
            return err(str(exc))

    @api.route("/integracoes/mercadophone/reprocessar", methods=["POST", "OPTIONS"])
    def reprocessar_mercadophone():
        if request.method == "OPTIONS":
            return ("", 204)
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            _, mp_cfg = _carregar_config_mercadophone()
            status_cfg = _atualizar_runtime_mercadophone(mp_cfg)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            with reprocessamento_mp_lock:
                if reprocessamento_mp_estado["rodando"]:
                    estado = dict(reprocessamento_mp_estado)
                    return ok(iniciado=False, reprocessamento=estado)

                reprocessamento_mp_estado["rodando"] = True
                reprocessamento_mp_estado["iniciado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["finalizado_em"] = None
                reprocessamento_mp_estado["atualizadas"] = 0
                reprocessamento_mp_estado["erros"] = 0
                reprocessamento_mp_estado["total"] = 0
                reprocessamento_mp_estado["erro"] = ""
                estado = dict(reprocessamento_mp_estado)

            threading.Thread(target=_executar_reprocessamento_mp_async, daemon=True).start()
            return ok(iniciado=True, reprocessamento=estado), 202
        except Exception as exc:
            return err(str(exc))

    @api.route("/integracoes/mercadophone/reprocessar/status")
    def status_reprocessar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(reprocessamento=_snapshot_reprocessamento_mp())

    @api.route("/integracoes/mercadophone/reimportar", methods=["POST", "OPTIONS"])
    def reimportar_mercadophone():
        if request.method == "OPTIONS":
            return ("", 204)
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            _, mp_cfg = _carregar_config_mercadophone()
            status_cfg = _atualizar_runtime_mercadophone(mp_cfg)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            with reimportacao_mp_lock:
                if reimportacao_mp_estado["rodando"]:
                    estado = dict(reimportacao_mp_estado)
                    return ok(iniciado=False, reimportacao=estado)

                reimportacao_mp_estado["rodando"] = True
                reimportacao_mp_estado["iniciado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["finalizado_em"] = None
                reimportacao_mp_estado["removidas"] = 0
                reimportacao_mp_estado["importadas"] = 0
                reimportacao_mp_estado["atualizadas"] = 0
                reimportacao_mp_estado["erro"] = ""
                estado = dict(reimportacao_mp_estado)

            threading.Thread(target=_executar_reimportacao_mp_async, daemon=True).start()
            return ok(iniciado=True, reimportacao=estado), 202
        except Exception as exc:
            return err(str(exc))

    @api.route("/integracoes/mercadophone/reimportar/status")
    def status_reimportar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(reimportacao=_snapshot_reimportacao_mp())

    @api.route("/integracoes/mercadophone/status")
    def status_mercadophone():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        _, mp_cfg = _carregar_config_mercadophone()
        status_cfg = _atualizar_runtime_mercadophone(mp_cfg)

        return ok(
            mercado_phone={
                **status_cfg,
                "tem_token": status_cfg["configurado"],
            }
        )

    @api.route("/integracoes/mercadophone/config", methods=["POST"])
    def salvar_config_mercadophone():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        dados, mp_cfg = _carregar_config_mercadophone()

        if "api_token" in body:
            mp_cfg["api_token"] = _texto_limpo_local(body.get("api_token"))

        if "sync_enabled" in body:
            mp_cfg["sync_enabled"] = _to_bool(body.get("sync_enabled"), padrao=True)

        if "sync_interval_seconds" in body:
            try:
                mp_cfg["sync_interval_seconds"] = max(30, int(body.get("sync_interval_seconds") or 180))
            except (TypeError, ValueError):
                return err("sync_interval_seconds inválido.", 400)

        if "sync_timeout_seconds" in body:
            try:
                mp_cfg["sync_timeout_seconds"] = max(5, int(body.get("sync_timeout_seconds") or 20))
            except (TypeError, ValueError):
                return err("sync_timeout_seconds inválido.", 400)

        if "sync_start_date" in body:
            mp_cfg["sync_start_date"] = _texto_limpo_local(body.get("sync_start_date")) or "2026-04-01"

        dados["mercado_phone"] = mp_cfg
        salvar_configuracoes_integracoes(integrations_config_path, dados)

        status_cfg = _atualizar_runtime_mercadophone(mp_cfg)
        return ok(mercado_phone=status_cfg)

    return api
