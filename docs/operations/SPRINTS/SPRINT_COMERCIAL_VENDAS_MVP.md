# SPRINT COMERCIAL — Vendas MVP

**Status:** CONCLUÍDA
**Período:** 2026-07-27 (dia único)
**Tipo:** Feature (backend), domínio novo

---

## Objetivo

Entregar o primeiro fluxo comercial completo da Fluxoly: venda de um único aparelho (unidade
serializada) a um cliente, com pagamento simples registrado — o "motor de venda" sobre o qual desconto,
comissão, garantia e troca serão construídos em sprints futuras, quando as decisões de negócio
correspondentes existirem.

## Motivação

Sequência definida pelo usuário (CTO): INC-001 (Branch A + C) → C1.3.5 (Rastreabilidade Individual de
Estoque) → Épico Vendas. `docs/product/features/VENDAS.md` (2026-07-09/11) já desenhava o fluxo
completo, mas várias decisões de negócio reais seguiam pendentes do Product Owner (timeout de reserva
de IMEI, % de comissão, limite de desconto do vendedor, prazo de garantia por tipo, critérios de
avaliação de usado) — bloqueando a implementação do módulo inteiro de uma vez.

## Investigação e decisão de escopo (antes de codar)

Identificada uma fatia decision-independent: o mecanismo central de venda (cliente escolhe aparelho →
confirma → unidade marcada vendida atomicamente → pagamento simples registrado) não depende de nenhuma
das decisões pendentes:

| Decisão pendente | Como foi evitada nesta fatia |
|---|---|
| Timeout de reserva de IMEI | Sem estado `reservado` — unidade vai direto `disponivel` → `vendido` |
| % de comissão sobre margem | Colunas de comissão não criadas; cálculo fica para quando o % existir |
| Limite de desconto do vendedor | Sem campo de desconto nesta fatia — preço é o valor informado, ponto |
| Prazo de garantia por tipo de aparelho | `vendas_garantias` não criada |
| Critérios de avaliação de usado (troca) | Troca inteira fora de escopo — fica para sprint própria |

## Decisões de modelagem (discutidas antes da implementação)

Aprovadas em conversa antes de qualquer código, para evitar retrabalho estrutural quando o fluxo
completo for implementado:

1. **`Venda` + `ItemVenda` desde o início**, não só `Venda` — mesmo com exatamente 1 item nesta fatia,
   evita partir a tabela quando vendas com múltiplos itens (aparelho + acessórios) existirem.
2. **`status='concluida'`, não `'paga'`** — separa o conceito de venda do conceito de pagamento.
3. **Snapshot `produto_nome`/`produto_sku`** em `vendas_itens` — preserva histórico mesmo se o cadastro
   do produto/estoque mudar depois.
4. **`UNIQUE` em `vendas_itens.unidade_serializada_id`** — proteção de banco contra duas vendas da mesma
   unidade, complementar à checagem de status na aplicação.
5. **`marcar_como_vendida` separada de `transicionar_status`** (`irflow_unidades_serializadas_service.py`)
   — evita que o endpoint genérico `PATCH .../status` vire uma porta lateral para `vendido` sem
   nenhuma `venda` real por trás.
6. **Primeiro módulo com o prefixo `fluxoly_`** — decisão de arquitetura própria, ver `ADR-008`.

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `app.py` | Schema `vendas`/`vendas_itens` (`criar_tabelas()`); registro do blueprint de Vendas |
| `fluxoly_vendas_repository.py` | Novo — `inserir_venda`, `inserir_item`, `buscar_por_id` |
| `fluxoly_vendas_service.py` | Novo — `iniciar_venda` (transação única), `obter_venda` |
| `fluxoly_vendas_controller.py` | Novo — `POST /api/vendas`, `GET /api/vendas/<id>` |
| `irflow_unidades_serializadas_repository.py` | + `marcar_vendida`; SKU adicionado às colunas de origem |
| `irflow_unidades_serializadas_service.py` | + `marcar_como_vendida`; `origem_sku` no dict de unidade |
| `irflow_vendas_service.py` | Removido — stub substituído pelos módulos `fluxoly_vendas_*.py` reais |
| `tests/test_vendas.py` | Novo — 16 casos |

## Sequência transacional (`iniciar_venda`)

```
1. Fora da transação (leitura, erro 404/400 cedo):
   clientes_service.obter_cliente(cliente_id)
   unidades_service.obter_unidade(unidade_serializada_id)  → valida status == 'disponivel'

2. Uma única transação:
   inserir_venda → inserir_item → marcar_como_vendida (WHERE status='disponivel') → auditoria → commit
   Qualquer exceção reverte tudo (rollback) — nunca uma venda órfã nem uma unidade vendida sem venda.
```

## Testes

16 casos (`tests/test_vendas.py`), incluindo:

- Criação válida — persiste `vendas`/`vendas_itens`, marca unidade `vendido`, snapshot correto
- Permissões (`admin`/`vendedor` podem vender, `tecnico` não, sem sessão → 401)
- Cliente/unidade inexistente → 404; unidade já vendida/forma de pagamento inválida/valor ≤ 0 → 400
- **Duas vendas concorrentes da mesma unidade (threads reais, não só chamada sequencial) — exatamente
  uma tem sucesso.** Rodado 5x isoladamente para confirmar ausência de flakiness
- Erro forçado na criação do item → rollback → unidade continua `disponivel`, nenhum item órfão
- `PATCH /api/unidades-serializadas/<id>/status` com `{"status": "vendido"}` continua rejeitado — prova
  de que a rota genérica não abriu a porta lateral

Suíte completa: 565 testes (549 + 16), `ruff check .` limpo. Frontend não tocado nesta sprint — sem
mudança em `frontend/`.

## Riscos

Nenhum novo além dos já aceitos no schema geral (sem `FOREIGN KEY` declarada). Domínio novo, sem
consumidor além dele mesmo ainda.

## Fora de Escopo

Desconto/aprovação de admin, comissão, garantia (`vendas_garantias`), troca/avaliação de usado, reserva
com timeout, cancelamento de venda, frontend.

## Definition of Done

- [x] Critérios de aceite atendidos (IMEI nunca vendido duas vezes; Cliente como entidade própria — ver
      `VENDAS.md` para o status de cada critério do spec completo)
- [x] Testes obrigatórios passando, sem regressão (565 testes)
- [x] `CHANGELOG.md`, `PROJECT_STATUS.md`, `PRODUCT_BACKLOG.md`, `VENDAS.md`, `DATABASE.md`,
      `DOMAIN_MODEL.md` atualizados
- [x] Commits seguem Conventional Commits

## Retrospectiva

### O que funcionou bem

Investir tempo na modelação (diagrama simples + schema completo + sequência transacional) antes de
escrever qualquer código, como pedido explicitamente — nenhum retrabalho de schema durante a
implementação. A decisão de `Venda + ItemVenda` desde o início (em vez de só `Venda`) já estava correta
quando a implementação começou.

### O que poderia ter sido melhor

Nada a registrar nesta sprint.

### Dívida técnica gerada

Nenhuma nova (TD-12, prefixo `irflow_`/`fluxoly_` convivendo, já registrada em `ADR-008`, não é gerada
por esta sprint especificamente).
