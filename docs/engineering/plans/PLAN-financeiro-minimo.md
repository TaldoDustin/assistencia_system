# PLAN-financeiro-minimo — Financeiro Mínimo (Caixa, Contas a Pagar/Receber)

**Data:** 2026-08-08
**Feature:** `docs/company/RELEASE_STRATEGY.md` — "Financeiro mínimo"; `docs/product/BUSINESS_RULES.md` BR-067 a BR-069
**Status:** Encerrado (2026-08-10) — ciclo ADR-010 completo (Discovery → Plano Técnico → Implementação →
Testes → QA Manual → Revisão Arquitetural → Encerramento)

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — aprovada (BR-067 a BR-069, `docs/product/BUSINESS_RULES.md`, 2026-08-08)
- [x] Plano Técnico — revisado contra o código real de Vendas, 2 refinamentos incorporados (commit `9cab1e9`)
- [x] Implementação (backend) — migration `m0002` (commit `5910bb7`), domínio Caixa + Contas a Pagar/
  Receber + hook de Vendas + registro dos blueprints (commit `c1bcc61`)
- [x] Implementação (frontend, 2026-08-09) — `frontend/src/pages/Financeiro.jsx` (rota `/financeiro`,
  três abas: Movimentações, Contas a Pagar, Contas a Receber), módulos `caixa`/`contasPagar`/
  `contasReceber` em `client.js`, item de navegação com gate `admin`/`financeiro`. Sem o relatório de
  fluxo de caixa (fora do escopo desta fatia, decisão do CTO).
- [x] Testes — 38 testes novos (`tests/test_caixa.py`, `tests/test_contas_pagar.py`,
  `tests/test_contas_receber.py`) + suíte completa (734/734) verde
- [x] QA Manual (backend) — fluxo de ponta a ponta via requisição HTTP real contra servidor isolado
  (`IR_FLOW_DATA_DIR` dedicado): login, venda → entrada de caixa, cancelamento → estorno, saldo
  recalculado, Conta a Pagar → baixa → saída de caixa, Conta a Receber → baixa → entrada de caixa
- [x] QA Manual (frontend, 2026-08-09) — navegador real, banco isolado: CRUD/ações das três abas, saldo
  recalculado a cada mutação, gate de perfil nos dois sentidos. Bug de UI encontrado e corrigido no
  mesmo ciclo (contador de total pós-exclusão em Contas a Pagar/Receber).
- [x] Validação Fatia 3 — integração Vendas↔Caixa (2026-08-09) — venda real → 1 movimentação
  `origem='venda'` correta → cancelamento → estorno correto, permanece no histórico → revenda da mesma
  unidade sem colisão/duplicação → 2 ciclos completos → suíte automatizada reconfirmada verde. Achado de
  UX corrigido no mesmo ciclo: botão "Estornar" restrito a `origem === "manual"` em `Financeiro.jsx`.
- [x] Revisão Arquitetural (2026-08-10) — percorridos os 4 eixos do gate (`ADR-010.md` seção "Etapa 6")
  contra o código real de `main` pós-merge:
  1. **Coerência do domínio** — confirmado por grep: existe exatamente um caminho de escrita em
     `movimentacoes_caixa` (`fluxoly_caixa_repository.py::inserir/estornar`), chamado só de 3 lugares
     (manual, hooks de Vendas, baixa de Contas a Pagar/Receber). Nenhum caminho paralelo.
  2. **Autorização centralizada** — `usuario_pode_financeiro()` duplicada em 4 controllers; já era risco
     aceito e documentado (TD-14, seção Riscos deste plano) — gate satisfeito, nada implícito.
  3. **Vazamento de dado** — todas as 12 rotas do Financeiro checam `usuario_pode_financeiro()` antes de
     qualquer acesso a dado; nenhuma rota esquecida sem gate.
  4. **Consistência da máquina de estados** — **achado real, registrado em KI-034**:
     `ajustar_desconto_item()` (BR-043, Ajuste Comercial Autorizado, já existia desde V1.3) recalcula
     `vendas.valor_total` após a venda concluída, mas não resincroniza a movimentação de caixa
     correspondente — o saldo do Caixa e um estorno posterior ficam com o valor original, não o
     corrigido. Não é regressão desta sprint (interação nova entre regra antiga e feature nova). Decisão
     do CTO: não bloqueia o encerramento, registrado em `KNOWN_ISSUES.md` (KI-034) para correção em
     sprint própria, preservando a mesma atomicidade já estabelecida no domínio (uma transação, um
     cursor).
- [x] Encerramento (2026-08-10) — `PROJECT_STATUS.md`, `CHANGELOG.md`,
  `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` e `docs/operations/KNOWN_ISSUES.md` (KI-034)
  atualizados. Nenhuma dívida técnica nova além de KI-034 (já registrada) e TD-14 (já aceita).

---

## Objetivo

Entregar o "Financeiro mínimo" já escopado em `RELEASE_STRATEGY.md` — Caixa, Entradas, Saídas, Contas a
Pagar, Contas a Receber, Fluxo de Caixa simples — como primeira feature de negócio construída diretamente
sobre o sistema formal de migrations (TD-03), seguindo a convenção controller/service/repository
(`ENGINEERING_GUIDE.md` §3.1).

## Escopo

- Tabela `movimentacoes_caixa` (entradas/saídas manuais + automáticas, com estorno).
- Tabela `contas_pagar` (CRUD, status `pendente`/`pago`/`cancelado`, baixa gera saída de caixa).
- Tabela `contas_receber` (CRUD, status `pendente`/`recebido`/`cancelado`, baixa gera entrada de caixa) —
  **sem FK para `vendas`** (BR-068).
- Hook em `fluxoly_vendas_service.py`: Venda `concluida` → cria entrada de caixa; Venda cancelada → estorna
  a entrada correspondente; idempotente (BR-069).
- Relatório de Fluxo de Caixa simples (agregação por período, sem tabela nova).
- Tela nova no frontend, visível só para perfis `admin`/`financeiro` (gate já existe:
  `usuario_pode_financeiro()`, `fluxoly_vendas_controller.py:35-42`).

## Fora de Escopo

- Integração automática Custos Operacionais ↔ Caixa (BR-067 — módulos permanecem independentes).
- Qualquer relação entre Contas a Receber e Vendas/inadimplência de cliente (BR-068).
- DRE, conciliação bancária, integrações bancárias, múltiplos caixas/frentes de caixa, automação financeira
  avançada (tudo isso é `RELEASE_STRATEGY.md` 2.x, não 1.0).
- Testes novos para `custos_operacionais` **não são critério de aceite** desta feature — podem entrar junto
  se pequenos e isolados (decisão do CTO), mas não bloqueiam o encerramento se não entrarem.

## Impacto no Banco

Primeira migration de negócio sobre o mecanismo formal da TD-03 —
`migrations/versions/m0002_financeiro_minimo.py`, registrada em `migrations/registry.py`.

```sql
CREATE TABLE movimentacoes_caixa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,              -- 'entrada' | 'saida'
    valor REAL NOT NULL,             -- sempre positivo; sinal vem de `tipo`
    descricao TEXT,
    origem TEXT NOT NULL DEFAULT 'manual',  -- 'manual' | 'venda' | 'conta_pagar' | 'conta_receber'
    origem_id INTEGER,               -- FK lógica para vendas.id / contas_pagar.id / contas_receber.id
    estornada INTEGER NOT NULL DEFAULT 0,
    usuario_id INTEGER,
    criado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_movimentacoes_caixa_origem ON movimentacoes_caixa (origem, origem_id);
CREATE INDEX idx_movimentacoes_caixa_tipo_estornada ON movimentacoes_caixa (tipo, estornada);

-- Guardião real de BR-069 ("uma venda nunca gera duas entradas ativas") no banco,
-- não só na aplicação -- mesmo padrão de idx_vendas_itens_unidade_ativa (V1.2).
-- Achado da revisão final do plano (2026-08-08): checagem só em código não seria
-- suficiente por si só, dado o precedente já estabelecido pelo projeto.
CREATE UNIQUE INDEX idx_movimentacoes_caixa_venda_ativa
    ON movimentacoes_caixa (origem_id) WHERE origem = 'venda' AND estornada = 0;

CREATE TABLE contas_pagar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    categoria TEXT,
    valor REAL NOT NULL,
    data_vencimento TEXT,
    status TEXT NOT NULL DEFAULT 'pendente',   -- 'pendente' | 'pago' | 'cancelado'
    movimentacao_caixa_id INTEGER,             -- preenchida quando status vira 'pago'
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE contas_receber (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    categoria TEXT,
    valor REAL NOT NULL,
    data_vencimento TEXT,
    status TEXT NOT NULL DEFAULT 'pendente',   -- 'pendente' | 'recebido' | 'cancelado'
    movimentacao_caixa_id INTEGER,             -- preenchida quando status vira 'recebido'
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Sem `FOREIGN KEY` declarada (mesmo padrão do resto do schema — integridade via aplicação). `origem_id`
em `movimentacoes_caixa` é polimórfica (aponta para tabelas diferentes conforme `origem`) — mesmo padrão
já aceito em outros pontos do schema onde a FK lógica muda de alvo conforme uma coluna irmã.

## Impacto no Backend

- `fluxoly_caixa_controller.py`/`_service.py`/`_repository.py` — CRUD de movimentação manual + cálculo de
  saldo (`SOMA(entradas não estornadas) − SOMA(saídas não estornadas)`, BR-069) + relatório de fluxo de
  caixa.
- `fluxoly_contas_pagar_controller.py`/`_service.py`/`_repository.py` — CRUD + transição de status (baixa
  gera saída de caixa via `fluxoly_caixa_service`, nunca SQL direto — mesma regra de dependência entre
  domínios do `ENGINEERING_GUIDE.md` §3.1).
- `fluxoly_contas_receber_controller.py`/`_service.py`/`_repository.py` — espelho de Contas a Pagar.
- Ponto de integração único em `fluxoly_vendas_service.py`: **`registrar_entrada_de_venda(cursor, venda_id,
  valor, usuario_id)`** chamada de dentro de `iniciar_venda()` (antes do `conn.commit()` da linha 231,
  hoje) e **`estornar_entrada_de_venda(cursor, venda_id, usuario_id)`** chamada de dentro de
  `cancelar_venda()` (antes do `conn.commit()` da linha 404, hoje) — ambas recebendo `cursor`, nunca
  abrindo conexão própria. Achado da revisão final do plano (2026-08-08): `iniciar_venda()`/
  `cancelar_venda()` já fazem várias operações cross-domínio na mesma transação passando `cursor`
  explicitamente (`unidades_service.marcar_como_vendida(cursor, ...)`,
  `unidades_service.liberar_unidade_para_venda(cursor, ...)`) — `fluxoly_caixa_service` precisa seguir
  exatamente esse padrão, senão a criação da venda e a entrada de caixa virariam duas transações
  separadas, quebrando a garantia de atomicidade da BR-069. A idempotência real é garantida pelo índice
  único `idx_movimentacoes_caixa_venda_ativa` (ver "Impacto no Banco") — não só por uma checagem prévia em
  código, mesmo espírito do `UNIQUE INDEX` que já protege `vendas_itens` contra corrida.
- Autorização: `usuario_pode_financeiro()` (já existe) estendida para todas as rotas novas.

## Impacto no Frontend

Tela nova (`Caixa.jsx` ou `Financeiro.jsx`) — listagem de movimentações, lançamento manual, CRUD de Contas
a Pagar/Receber, card de saldo, relatório de fluxo de caixa. Visível só para `admin`/`financeiro`, mesmo
princípio de UX por perfil do `ENGINEERING_GUIDE.md` §4.0.

## Estratégia de Migração

Aditiva — `migrations/versions/m0002_financeiro_minimo.py`, DDL puro (sem backfill, já que são tabelas
novas sem dado legado a migrar). Segue exatamente o contrato de `apply(cursor, conn)` já validado na Fatia
1 da TD-03.

## Testes

- `fluxoly_caixa_*`: CRUD, cálculo de saldo (entradas/saídas/estornadas), idempotência do hook de Vendas
  (criar entrada 2x para a mesma venda não duplica), estorno no cancelamento de venda.
- `fluxoly_contas_pagar_*`/`fluxoly_contas_receber_*`: CRUD, transição de status, baixa gera movimentação
  de caixa correspondente.
- Migration `m0002`: mesmo padrão de `tests/test_migrations.py` (banco vazio, idempotência, ordem).
- Testes de `custos_operacionais` — opcional, não bloqueia encerramento (decisão do CTO).

## Critérios de Aceite

Os 6 itens de "Financeiro mínimo" do `RELEASE_1.0_MASTER_CHECKLIST.md` (Caixa, Entradas, Saídas, Contas a
Pagar, Contas a Receber, Fluxo de Caixa simples) marcados como entregues, com BR-067 a BR-069 respeitadas.

## Riscos

- TD-14 (autorização ad-hoc por perfil) se repete mais uma vez — aceitável, padrão já conhecido e aceito.
- `origem_id` polimórfico em `movimentacoes_caixa` exige disciplina de aplicação (sem `FOREIGN KEY` real)
  — mesmo risco estrutural já aceito no resto do schema.
- Primeira feature real usando `migrations/` — qualquer atrito no fluxo (registry, `apply(cursor, conn)`,
  `schema_migrations`) é sinal para revisar o mecanismo da TD-03, não só a feature.

## Rollback

Roll-forward only (TD-03, decisão já aprovada) — se `m0002` precisar ser desfeita, uma migration `m0003`
nova reverte o efeito, nunca editar `m0002` depois de aplicada em qualquer ambiente.

## Questões em Aberto

Nenhuma — BR-067, BR-068 e BR-069 fecham as decisões de negócio necessárias para este escopo. Se algo
técnico exigir uma decisão de negócio nova durante a implementação, volta para Discovery antes de
prosseguir (Princípio da Separação de Decisões, ADR-010).
