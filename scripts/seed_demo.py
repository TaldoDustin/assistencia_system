#!/usr/bin/env python
"""Popula uma "loja modelo" 100% sintética no Ambiente de Demonstração (ADR-012).

Uso:
  DEMO_SEED_ADMIN_PASSWORD=... DEMO_SEED_TECNICO_PASSWORD=... DEMO_SEED_VENDEDOR_PASSWORD=... \
      python scripts/seed_demo.py

Roda uma única vez, contra um banco já com schema aplicado (depois do primeiro
boot do serviço demo) e vazio de dados de negócio -- ver
docs/engineering/plans/PLAN-ambiente-demo-homologacao.md. Conecta direto ao
banco via `conectar()` de `app.py`, sem subir o servidor Flask (mesmo padrão
de `scripts/import_legacy_db.py`).

As senhas das 3 contas de demonstração são lidas de variáveis de ambiente no
momento da execução -- nunca hardcoded aqui nem commitadas (KI-029: dois
arquivos de banco com dado real já vazaram para o histórico do git por causa
de credencial/dado versionado; nunca hardcode nada sensível neste script,
mesmo que "só para teste"). CUIDADO ao rodar localmente: se o shell registrar
histórico de comandos, a senha pode ficar exposta nesse histórico -- prefira
exportar as variáveis num passo separado (`export DEMO_SEED_ADMIN_PASSWORD=...`)
em vez de embuti-las na mesma linha do comando, ou usar um gerenciador de
segredos do shell.

Depois do seed rodar com sucesso, crie o backup "estado inicial" via
`POST /api/backup/criar` (endpoint já existente) com um nome identificável --
esse arquivo vira o "seed-inicial" usado pelo mecanismo de reset manual
(`POST /api/backup/restaurar`). Este script não faz essa chamada HTTP --
requer o servidor rodando, o que contradiria "sem subir o servidor Flask".
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash  # noqa: E402

import fluxoly_caixa_repository as caixa_repo  # noqa: E402
import fluxoly_clientes_repository as clientes_repo  # noqa: E402
import fluxoly_produtos_repository as produtos_repo  # noqa: E402
import fluxoly_unidades_serializadas_repository as unidades_repo  # noqa: E402
import fluxoly_vendas_repository as vendas_repo  # noqa: E402
from app import conectar  # noqa: E402
from fluxoly_os import obter_ou_criar_reparo, salvar_reparos_os  # noqa: E402

SENHA_ENV_VARS = {
    "admin": "DEMO_SEED_ADMIN_PASSWORD",
    "tecnico": "DEMO_SEED_TECNICO_PASSWORD",
    "vendedor": "DEMO_SEED_VENDEDOR_PASSWORD",
}

CLIENTES_DEMO = [
    ("Ana Beatriz Ferreira", "(11) 91234-0001", "ana.ferreira@example.com"),
    ("Bruno Carvalho Lima", "(11) 91234-0002", "bruno.lima@example.com"),
    ("Camila Souza Ribeiro", "(11) 91234-0003", "camila.ribeiro@example.com"),
    ("Diego Almeida Rocha", "(11) 91234-0004", "diego.rocha@example.com"),
    ("Elaine Cristina Santos", "(11) 91234-0005", "elaine.santos@example.com"),
    ("Fábio Henrique Costa", "(11) 91234-0006", "fabio.costa@example.com"),
    ("Gabriela Martins Pinto", "(11) 91234-0007", "gabriela.pinto@example.com"),
    ("Henrique Oliveira Dias", "(11) 91234-0008", "henrique.dias@example.com"),
    ("Isabela Nunes Barros", "(11) 91234-0009", "isabela.barros@example.com"),
    ("João Pedro Cavalcante", "(11) 91234-0010", "joao.cavalcante@example.com"),
    ("Karina Alves Teixeira", "(11) 91234-0011", "karina.teixeira@example.com"),
    ("Lucas Gabriel Moreira", "(11) 91234-0012", "lucas.moreira@example.com"),
    ("Mariana Duarte Freitas", "(11) 91234-0013", "mariana.freitas@example.com"),
    ("Natália Ramos Cardoso", "(11) 91234-0014", "natalia.cardoso@example.com"),
    ("Otávio Correia Batista", "(11) 91234-0015", "otavio.batista@example.com"),
    ("Patrícia Gomes Andrade", "(11) 91234-0016", "patricia.andrade@example.com"),
    ("Rafael Nascimento Vieira", "(11) 91234-0017", "rafael.vieira@example.com"),
    ("Sabrina Lopes Monteiro", "(11) 91234-0018", "sabrina.monteiro@example.com"),
]

REPAROS_DEMO = [
    "TROCA DE TELA",
    "TROCA DE BATERIA",
    "TROCA DE DOCK DE CARGA",
    "TROCA DE CAMERA TRASEIRA",
    "TROCA DE VIDRO DA TELA",
]

PECAS_ESTOQUE_DEMO = [
    # (descricao, valor, fornecedor, quantidade, modelo, tipo, qualidade)
    ("Tela iPhone 12 Original", 420.0, "Fornecedor Demo A", 8, "iPhone 12", "Tela", "Original"),
    ("Bateria iPhone 12 Compativel", 90.0, "Fornecedor Demo A", 15, "iPhone 12", "Bateria", "Compativel"),
    ("Tela iPhone 13 Original", 520.0, "Fornecedor Demo B", 6, "iPhone 13", "Tela", "Original"),
    ("Bateria iPhone 13 Compativel", 110.0, "Fornecedor Demo B", 12, "iPhone 13", "Bateria", "Compativel"),
    ("Dock de Carga iPhone 11", 60.0, "Fornecedor Demo A", 10, "iPhone 11", "Dock de Carga", "Compativel"),
    ("Camera Traseira iPhone 12", 180.0, "Fornecedor Demo B", 5, "iPhone 12", "Camera", "Original"),
]

PRODUTOS_DEMO = [
    # (modelo, cor, capacidade, condicao, preco_custo, preco_venda)
    ("iPhone 12", "Preto", "128GB", "Seminovo", 1800.0, 2400.0),
    ("iPhone 12", "Branco", "128GB", "Seminovo", 1850.0, 2450.0),
    ("iPhone 13", "Meia-noite", "128GB", "Seminovo", 2400.0, 3100.0),
    ("iPhone 13", "Estelar", "256GB", "Novo", 2900.0, 3700.0),
    ("iPhone 13 Pro", "Grafite", "256GB", "Seminovo", 3300.0, 4200.0),
    ("iPhone 11", "Preto", "64GB", "Seminovo", 1300.0, 1750.0),
    ("iPhone 11", "Branco", "128GB", "Seminovo", 1450.0, 1900.0),
    ("iPhone SE (2a geracao)", "Preto", "64GB", "Seminovo", 950.0, 1350.0),
    ("iPhone 14", "Meia-noite", "128GB", "Novo", 3400.0, 4300.0),
    ("iPhone 14 Plus", "Roxo", "256GB", "Novo", 3900.0, 4900.0),
]

OS_STATUS_CICLO = [
    "Finalizado",
    "Finalizado",
    "Finalizado",
    "Em andamento",
    "Em andamento",
    "Aguardando peca",
    "Cancelado",
]

TECNICOS_DEMO = ["ISAQUE SOUZA", "RUAM SOARES"]


def _senhas_do_ambiente():
    valores = {}
    faltando = []
    for perfil, env_var in SENHA_ENV_VARS.items():
        valor = (os.environ.get(env_var) or "").strip()
        if not valor:
            faltando.append(env_var)
        valores[perfil] = valor
    if faltando:
        print(
            "Faltam variáveis de ambiente obrigatórias (sem default -- nunca hardcode senha aqui, ver KI-029): "
            + ", ".join(faltando)
        )
        sys.exit(1)
    return valores


def _garantir_banco_vazio(cursor):
    for tabela in ("clientes", "os", "vendas"):
        cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
        (total,) = cursor.fetchone()
        if total:
            print(
                f"Tabela '{tabela}' já tem {total} registro(s) -- este script só roda contra um banco "
                "vazio de dados de negócio (ver docstring). Abortando sem gravar nada."
            )
            sys.exit(1)


def seed_usuarios(cursor, senhas):
    contas = [
        ("Admin Demo", "admin.demo", "admin", senhas["admin"]),
        ("Técnico Demo", "tecnico.demo", "tecnico", senhas["tecnico"]),
        ("Vendedor Demo", "vendedor.demo", "vendedor", senhas["vendedor"]),
    ]
    ids = {}
    for nome, usuario, perfil, senha in contas:
        cursor.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, 1)",
            (nome, usuario, generate_password_hash(senha), perfil),
        )
        ids[perfil] = cursor.lastrowid
    return ids


def seed_clientes(cursor):
    ids = []
    for nome, telefone, email in CLIENTES_DEMO:
        ids.append(clientes_repo.inserir(cursor, nome, telefone, email, "", ""))
    return ids


def seed_reparos(cursor):
    return {nome: obter_ou_criar_reparo(cursor, nome) for nome in REPAROS_DEMO}


def seed_estoque_pecas(cursor):
    ids = []
    for descricao, valor, fornecedor, quantidade, modelo, tipo, qualidade in PECAS_ESTOQUE_DEMO:
        cursor.execute(
            """
            INSERT INTO estoque (descricao, valor, fornecedor, quantidade, data_compra, modelo, tipo, qualidade, requer_imei)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """,
            (
                descricao,
                valor,
                fornecedor,
                quantidade,
                datetime.now().strftime("%Y-%m-%d"),
                modelo,
                tipo,
                qualidade,
            ),
        )
        ids.append((cursor.lastrowid, valor, descricao, fornecedor, modelo))
    return ids


def seed_produtos_e_unidades(cursor):
    """Cria os produtos e uma unidade serializada 'disponivel' por produto,
    com IMEI claramente sintético (prefixo 00, nunca um IMEI real válido)."""
    produtos = []
    for indice, (modelo, cor, capacidade, condicao, preco_custo, preco_venda) in enumerate(PRODUTOS_DEMO):
        produto_id = produtos_repo.inserir(
            cursor,
            categoria="iPhone",
            marca="Apple",
            modelo=modelo,
            cor=cor,
            capacidade=capacidade,
            condicao=condicao,
            descricao=f"{modelo} {capacidade} {cor} ({condicao}) -- loja modelo Demo",
            sku=f"DEMO-{indice + 1:03d}",
            fornecedor="Fornecedor Demo",
            preco_custo=preco_custo,
            preco_venda=preco_venda,
            quantidade=0,
            requer_rastreio_unidade=1,
        )
        imei_sintetico = f"00{indice + 1:013d}"
        unidade_id = unidades_repo.inserir(cursor, produto_id=produto_id, imei=imei_sintetico)
        produtos.append(
            {
                "produto_id": produto_id,
                "unidade_id": unidade_id,
                "modelo": modelo,
                "sku": f"DEMO-{indice + 1:03d}",
                "preco_venda": preco_venda,
            }
        )
    return produtos


def seed_os(cursor, cliente_ids, reparo_map, pecas_estoque, tecnico_ids):
    reparo_ids = list(reparo_map.values())
    hoje = datetime.now()
    for indice in range(24):
        status = OS_STATUS_CICLO[indice % len(OS_STATUS_CICLO)]
        cliente_id = cliente_ids[indice % len(cliente_ids)]
        cliente_nome = CLIENTES_DEMO[indice % len(CLIENTES_DEMO)][0]
        modelo = PRODUTOS_DEMO[indice % len(PRODUTOS_DEMO)][0]
        tecnico = TECNICOS_DEMO[indice % len(TECNICOS_DEMO)]
        data_abertura = (hoje - timedelta(days=(indice * 2) % 55)).strftime("%Y-%m-%d")
        reparo_id_escolhido = reparo_ids[indice % len(reparo_ids)]
        valor_cobrado = 150.0 + (indice % 6) * 45.0

        cursor.execute(
            """
            INSERT INTO os (tipo, cliente, aparelho, tecnico, reparo_id, status,
                valor_cobrado, valor_descontado, custo_pecas, data, observacoes, modelo, vendedor, cor, imei, cliente_id)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "Assistencia",
                cliente_nome,
                modelo,
                tecnico,
                reparo_id_escolhido,
                status,
                valor_cobrado,
                0.0,
                0.0,
                data_abertura,
                "OS sintética -- Ambiente de Demonstração (ADR-012)",
                modelo,
                "",
                "",
                "",
                cliente_id,
            ),
        )
        os_id = cursor.lastrowid
        salvar_reparos_os(cursor, os_id, [reparo_id_escolhido])

        peca_id, peca_valor, peca_descricao, peca_fornecedor, peca_modelo = pecas_estoque[indice % len(pecas_estoque)]
        cursor.execute(
            """
            INSERT INTO os_pecas (os_id, estoque_id, quantidade, valor, peca_descricao, peca_fornecedor, peca_modelo)
            VALUES (?, ?, 1, ?, ?, ?, ?)
            """,
            (os_id, peca_id, peca_valor, peca_descricao, peca_fornecedor, peca_modelo),
        )
        cursor.execute("UPDATE os SET custo_pecas=? WHERE id=?", (round(peca_valor, 2), os_id))

        if status == "Finalizado":
            cursor.execute("UPDATE os SET data_finalizado=? WHERE id=?", (data_abertura, os_id))


def seed_vendas(cursor, produtos, cliente_ids, vendedor_id):
    formas_pagamento = ["pix", "cartao", "dinheiro", "transferencia"]
    for indice, produto in enumerate(produtos[:8]):
        cliente_id = cliente_ids[indice % len(cliente_ids)]
        valor_unitario = produto["preco_venda"]
        forma_pagamento = formas_pagamento[indice % len(formas_pagamento)]

        venda_id = vendas_repo.inserir_venda(
            cursor, cliente_id, vendedor_id, forma_pagamento, valor_unitario, observacoes="Venda sintética -- Demo"
        )
        vendas_repo.inserir_item(
            cursor,
            venda_id,
            produto["unidade_id"],
            produto["produto_id"],
            produto["modelo"],
            produto["sku"],
            valor_unitario,
            valor_unitario,
        )
        linhas_afetadas = unidades_repo.marcar_vendida(cursor, produto["unidade_id"], venda_id)
        if not linhas_afetadas:
            raise RuntimeError(f"Unidade {produto['unidade_id']} não estava disponível para venda no seed.")

        caixa_repo.inserir(
            cursor,
            tipo="entrada",
            valor=valor_unitario,
            descricao=f"Venda #{venda_id} -- {produto['modelo']} (seed Demo)",
            origem="venda",
            origem_id=venda_id,
            usuario_id=vendedor_id,
        )


def main():
    senhas = _senhas_do_ambiente()

    conn = conectar()
    cursor = conn.cursor()
    try:
        _garantir_banco_vazio(cursor)

        usuario_ids = seed_usuarios(cursor, senhas)
        cliente_ids = seed_clientes(cursor)
        reparo_map = seed_reparos(cursor)
        pecas_estoque = seed_estoque_pecas(cursor)
        produtos = seed_produtos_e_unidades(cursor)
        seed_os(cursor, cliente_ids, reparo_map, pecas_estoque, usuario_ids)
        seed_vendas(cursor, produtos, cliente_ids, usuario_ids["vendedor"])

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("Seed do Ambiente de Demonstração concluído com sucesso.")
    print(f"  Clientes: {len(CLIENTES_DEMO)}")
    print(f"  Produtos/unidades: {len(PRODUTOS_DEMO)}")
    print("  OS: 24")
    print("  Vendas: 8")
    print("  Contas: admin.demo, tecnico.demo, vendedor.demo")
    print(
        "\nPróximo passo (fora deste script): criar o backup 'seed-inicial' via "
        "POST /api/backup/criar com o servidor rodando, para servir de restore point do reset manual."
    )


if __name__ == "__main__":
    main()
