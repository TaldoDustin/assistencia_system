# VENDAS_GAP_ANALYSIS.md — Revisão de Consistência (2026-07-22)

**O que é:** análise de consistência entre `docs/product/features/VENDAS.md` (rascunho de 2026-07-09,
atualizado em 2026-07-11 e 2026-07-20/21) e o estado real do código em `main` nesta data. Não é uma
nova especificação — não substitui `VENDAS.md` nem `docs/engineering/adr/ADR-007.md`, que continuam
sendo a fonte de verdade. Objetivo único: economizar a etapa de redescoberta quando o Épico Vendas for
aberto para planejamento (`discuss-phase`).

**Não decide nada novo.** Toda decisão de produto listada aqui já estava em aberto em `VENDAS.md` —
este documento só confirma que continua em aberto.

---

## 1. O que continua válido em `VENDAS.md`

| Seção | Validade | Nota |
|---|---|---|
| Fluxo completo (linha 39-89) | ✅ Válido, sem mudança | Nenhum domínio construído desde 09/jul contradiz o desenho (Atendimento → escolha → reserva → pagamento → garantia → entrega) |
| Casos de erro (linha 124-132) | ✅ Válido, sem mudança | Nenhum foi implementado ainda, nenhum foi invalidado por decisão posterior |
| Critérios de aceite (linha 233-240) | ✅ Válido, sem mudança | Nenhum item já contradito pelo que existe hoje |
| Decisões já tomadas (linha 93-106) | ✅ Válido, sem mudança | Reaproveitar `admin`/`vendedor`/`tecnico`, reserva com expiração, comissão sobre margem, garantia própria por tipo — nenhuma dessas premissas quebrou |
| Modelo de dados — tabela `vendas`/`vendas_garantias` (linha 151-185) | ✅ Válido, **já ajustado** | O próprio documento já tem uma nota (2026-07-20/21) reconciliando `estoque_unidade_id` para apontar a `unidades_serializadas.id` pós-ADR-007. Não há gap aqui — o documento já se autoatualizou |
| BR-017 a BR-022 (`docs/product/BUSINESS_RULES.md`) | ✅ Válido | Regras extraídas das decisões acima, nenhuma delas foi implementada nem contradita ainda |

**Conclusão da seção 1:** o documento de fluxo de negócio em si não está desatualizado. O gap real está
na camada técnica (seção 2), não na camada de produto.

---

## 2. O que mudou desde 09/jul — e se já está refletido

| Mudança | Já refletido em `VENDAS.md`/ADR-007? | Detalhe |
|---|---|---|
| Domínio **Produtos** implementado (catálogo comercial) | ✅ Sim | Nota de 2026-07-20/21 no próprio `VENDAS.md` já reconhece o catálogo e aponta `estoque_unidade_id` para a tabela correta |
| **`unidades_serializadas`** substituiu `estoque_unidades` | ✅ Sim | Mesma nota acima; ADR-007 é a fonte de verdade do novo modelo |
| **Clientes** virou domínio próprio (tabela `clientes` real, não texto solto) | ✅ Sim, desde o início | Já era a decisão original de 09/jul ("Cria tabela `clientes` própria no V1"); a tabela existe hoje em `app.py` (`CREATE TABLE IF NOT EXISTS clientes`) — a decisão foi executada, não mudou o desenho |
| **Auditoria (`audit_log`/`irflow_audit.py`)** existe e é reutilizável | ❌ **Gap** | `VENDAS.md` não cita `irflow_audit.py` na seção "Dependências". `unidades_serializadas` já usa `registrar_log_auditoria()` para `status_change` — Vendas deveria reutilizar o mesmo padrão (criação de venda, aprovação/rejeição de desconto, transições de status) em vez de inventar um mecanismo próprio. **Recomendação para o discuss-phase:** adicionar `irflow_audit.py` como dependência explícita |
| **Centralização de referências** (`irflow_reference_data.py`, `GET /api/constantes`) | 🟡 Tangencial | Não afeta o fluxo de negócio, mas reduz risco de divergência quando a tela de Vendas precisar ler categoria/condição de produto — já é fonte única, nada a fazer |
| **Máquina de estados de `unidades_serializadas` — implementação parcial** | ❌ **Gap mais importante** | ADR-007 desenha o ciclo completo (`Disponível → Reservado → Vendido → Em Garantia → Troca → Descartado`), mas `irflow_unidades_serializadas_service.py` hoje só implementa `disponivel → em_reparo`, `em_reparo → {disponivel, devolvido}`, `devolvido → disponivel`. As transições `disponivel → reservado` e `reservado → vendido` — que ADR-007 já documenta como propriedade do domínio Vendas — **não existem ainda em `TRANSICOES_VALIDAS`**. Isso é trabalho de implementação do Épico Vendas, não um gap de documentação |
| Colunas `venda_id`, `reservado_por`, `reservado_ate` já existem no schema de `unidades_serializadas` | ✅ Já preparado | Adicionadas antecipadamente (ADR-007) mas nunca usadas — nenhuma migração nova será necessária para reserva/venda, só wiring de código |
| `irflow_vendas_service.py` | ✅ Confirma o esperado | Existe hoje só como stub com docstring, confirmando que `irflow_clientes_service.py` e `irflow_unidades_serializadas_service.py` já são pré-requisitos entregues — consistente com "Dependências" de `VENDAS.md` |

**Conclusão da seção 2:** nenhuma mudança de produto invalidou o fluxo desenhado em 09/jul. As duas
lacunas reais são técnicas e pequenas: (a) citar `irflow_audit.py` como dependência explícita, (b)
lembrar que a máquina de estados de `unidades_serializadas` precisa ganhar as transições de
`reservado`/`vendido` como parte da implementação de Vendas — não antes.

---

## 3. Decisões que ainda dependem do Product Owner

Sem mudança em relação a `VENDAS.md` seção "O que ainda está em aberto" — nenhuma foi respondida desde
09/jul:

- Valor exato do timeout de reserva de IMEI (minutos)
- Percentual de comissão sobre margem
- Limite de desconto do vendedor sem aprovação de admin
- Prazo de garantia por tipo de aparelho (novo vs. seminovo)
- Critérios exatos do checklist de avaliação de usado + tabela de referência por modelo
- Quais telas cada perfil vê (vendedor vs. admin vs. técnico) — decisão de UX
- **Cliente piloto** (levantado em conversa de 2026-07-22, ainda não em nenhum documento formal): qual
  loja/cliente valida o MVP primeiro, e o que essa loja precisa obrigatoriamente conseguir fazer no
  primeiro dia — essa resposta deveria virar o critério de corte do MVP, em vez de suposição de
  engenharia

---

## Resumo objetivo

Dos itens de `VENDAS.md` revisados: **fluxo, casos de erro, critérios de aceite e modelo de dados
continuam 100% válidos** (o próprio documento já se autocorrigiu para o ADR-007). **Dois pontos técnicos
merecem entrar explicitamente no discuss-phase** (reuso de `irflow_audit.py`; transições de estado
`reservado`/`vendido` ainda não implementadas). **Seis decisões de produto continuam pendentes do PO**,
as mesmas cinco de 09/jul mais a definição do cliente piloto.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — fonte de verdade do fluxo de negócio (não alterado por esta análise)
- `docs/engineering/adr/ADR-007.md` — fonte de verdade da máquina de estados de `unidades_serializadas` (não alterado por esta análise)
- `irflow_unidades_serializadas_service.py` — implementação atual de `TRANSICOES_VALIDAS`
- `irflow_vendas_service.py` — stub do domínio, aguardando aprovação do épico
