"""
irflow_vendas_service.py

Reservado para o domínio Vendas (`docs/product/features/VENDAS.md`), ainda
não implementado. O CTO decidiu não iniciar o módulo de Vendas nesta
sprint — este arquivo existe apenas como placeholder para deixar explícito
onde esse domínio vai viver, seguindo a mesma convenção controller →
service → repository já aplicada em Clientes (`irflow_clientes_service.py`)
e `unidades_serializadas` (`irflow_unidades_serializadas_service.py`).

Depende de (quando implementado): `irflow_clientes_service.py` (cliente da
venda), `irflow_unidades_serializadas_service.py` (reserva/consumo de
IMEI, origem `produto_id` — ver ADR-007) — ambos pré-requisitos já
entregues.

Não importar nem instanciar nada deste módulo até o épico Vendas ser
aprovado para implementação (`docs/product/PRODUCT_BACKLOG.md`, prioridade P0).
"""
