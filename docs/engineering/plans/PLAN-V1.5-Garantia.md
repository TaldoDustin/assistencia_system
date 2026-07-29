# PLAN-V1.5-Garantia — Garantia (Venda + Reparo)

**Data:** 2026-07-29
**Feature:** `docs/product/features/VENDAS.md` — "V1.5 — Garantia"; `docs/product/BUSINESS_RULES.md` BR-055 a BR-066
**Status:** Aprovado pelo CTO (2026-07-29)

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — aprovada (BR-055 a BR-066, `docs/product/BUSINESS_RULES.md`, commits `9a12d03`/`2e91c5e`)
- [x] Plano Técnico — aprovado (2026-07-29)
- [ ] Implementação
- [ ] Testes
- [ ] QA Manual
- [ ] Revisão Arquitetural — obrigatória (toca mais de 3 arquivos e substitui um comportamento existente
      — o prazo fixo de 90 dias — pela nova regra, mesmo perfil de risco que motivou a etapa na V1.4)
- [ ] Encerramento

---

## Objetivo

Implementar Garantia de Venda e Garantia de Reparo como dois processos comerciais independentes, ambos
de atribuição manual e obrigatória, com snapshot histórico no momento da concessão — substituindo o
prazo fixo de 90 dias hardcoded do reparo. Regras de negócio já fechadas na discovery (BR-055 a BR-066);
este documento decide só como implementar.

---

## Escopo

- Novo cadastro **Tipos de Garantia** (nome + duração em meses), CRUD restrito a `admin`.
- Garantia de Venda: atribuída por item, na criação da venda, obrigatória.
- Garantia de Reparo: atribuída por linha de reparo (`os_reparos`), na conclusão da OS, obrigatória.
- Snapshot completo (id do tipo, nome, duração, data de início, data fim) em ambos os lados — nunca
  recalculado via JOIN ao vivo com o cadastro.
- Correção pós-concessão restrita a `admin`, com auditoria (`audit_log`), sem motivo obrigatório.
- Cancelamento (venda ou OS) invalida/zera a garantia correspondente, com evento de auditoria.
- Reescrita de `listar_garantias()` (endpoint existente `/api/garantias`) para ler a Garantia de Reparo
  por linha, substituindo o prazo fixo de 90 dias — com fallback só para dados históricos.

---

## Fora de Escopo

- Vínculo formal entre uma OS de garantia e a venda original (BR-066) — decisão de cobrar fica manual.
- Garantia de Venda para o caminho legado `estoque` (BR-060) — só `produtos`.
- Multi-tenant real / `empresa_id` (BR-066) — o cadastro é configurável só nesta loja/deploy.
- Exibir a Garantia de Venda na tela de Unidades Serializadas (`UnidadesSerializadas.jsx` já tem um
  placeholder "depende da venda") — natural evolução futura, não pedida nesta discovery; não implementado
  agora para não expandir escopo além do que foi decidido.
- Backfill retroativo de garantia para vendas/OS já concluídas antes desta sprint (ver "Estratégia de
  Migração").

---

## Impacto no Banco

**Tabela nova — `tipos_garantia`** (aditiva):

```sql
CREATE TABLE IF NOT EXISTS tipos_garantia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    duracao_meses INTEGER NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
)
```

`ativo` permite ao `admin` aposentar uma política sem apagá-la (mesmo padrão de `produtos.ativo`) — nunca
afeta garantias já concedidas, que são snapshot (ver abaixo). `duracao_meses = 0` representa "sem
garantia" quando a loja optar por cadastrar esse tipo (BR-055, não obrigatório existir).

**`vendas_itens` — colunas aditivas:**

```sql
ALTER TABLE vendas_itens ADD COLUMN tipo_garantia_id INTEGER
ALTER TABLE vendas_itens ADD COLUMN garantia_nome TEXT
ALTER TABLE vendas_itens ADD COLUMN garantia_duracao_meses INTEGER
ALTER TABLE vendas_itens ADD COLUMN garantia_data_inicio TEXT
ALTER TABLE vendas_itens ADD COLUMN garantia_data_fim TEXT
```

Nullable no schema (compatibilidade com linhas já existentes antes desta sprint) — a obrigatoriedade de
BR-056 é imposta pelo `service`, nunca pelo schema (mesmo padrão já usado em todo o domínio Vendas: o
schema é permissivo, a regra de negócio vive no código).

**`os_reparos` — colunas aditivas** (mesmo conjunto, aplicado por linha de reparo, não por OS):

```sql
ALTER TABLE os_reparos ADD COLUMN tipo_garantia_id INTEGER
ALTER TABLE os_reparos ADD COLUMN garantia_nome TEXT
ALTER TABLE os_reparos ADD COLUMN garantia_duracao_meses INTEGER
ALTER TABLE os_reparos ADD COLUMN garantia_data_inicio TEXT
ALTER TABLE os_reparos ADD COLUMN garantia_data_fim TEXT
```

**Auditoria:** reaproveita `audit_log` já existente — `entidade='venda_item'`/`'os_reparo'`,
`acao='garantia_concedida'` (na atribuição original) e `acao='garantia_alterada'` (na correção
admin-only), `valor_anterior`/`valor_novo` como JSON (mesmo shape de `comissao_alterada`, BR-049). Nenhuma
tabela de auditoria nova — é exatamente o ponto que a Discovery pediu para não reinventar.

**Sem `FOREIGN KEY` real** (`tipo_garantia_id`) — mesmo padrão já usado em todo o schema (`cliente_id`,
`produto_id` etc. são FKs lógicas, sem constraint SQLite). O snapshot (`garantia_nome`/
`garantia_duracao_meses`) garante que a linha continua correta mesmo se o `tipos_garantia` referenciado
for editado ou desativado depois.

**Índices:** nenhum novo necessário — consultas de garantia são sempre por `venda_id`/`os_id`, já
cobertos pelos índices existentes.

---

## Impacto no Backend

**Novo módulo compartilhado — `fluxoly_tipos_garantia_{repository,service,controller}.py`** (nasce
`fluxoly_*`, ADR-008): CRUD simples de Tipos de Garantia. Vive como módulo próprio, não dentro de
`fluxoly_vendas_*` nem de `irflow_os.py`, porque é consumido pelos dois domínios (Vendas e Assistência) —
nenhum dos dois é dono do cadastro.

- `GET /api/tipos-garantia` — lista, qualquer autenticado (precisa popular o campo de seleção nas telas
  de venda e de conclusão de OS).
- `POST/PUT /api/tipos-garantia` — só `admin`.
- Sem `DELETE` — usar `ativo=0` (mesmo padrão de desativação, não exclusão, já usado em `produtos`).

**Função compartilhada de cálculo — `irflow_core.py::calcular_data_fim_garantia(data_inicio, duracao_meses)`:**
pura, sem I/O, soma meses de calendário tratando overflow de dia (ex.: 31/01 + 1 mês → 28/02 ou 29/02, ano
bissexto). Único lugar que faz essa conta — chamado tanto por `fluxoly_vendas_service.py` quanto por
`irflow_os.py`, para não duplicar a mesma lógica de data em dois domínios (ponto que a própria discovery
pediu para resolver, "sem duplicar regra de negócio").

**`fluxoly_vendas_service.py` (Garantia de Venda):**
- `iniciar_venda` passa a exigir `tipo_garantia_id` no payload — rejeita com erro claro se ausente
  (BR-056). Resolve o tipo, congela snapshot (nome/duração), calcula `garantia_data_fim` a partir da data
  da venda, grava tudo no item.
- `cancelar_venda`: zera a Garantia de Venda do item cancelado, mesmo ponto onde a comissão já é zerada
  (mesma transação, mesmo evento de auditoria) — BR-058.
- Nova função `corrigir_garantia_item(...)`: só `admin`, sem motivo, mesmo compare-and-swap já usado em
  Ajuste Comercial/Comissão (rejeita se a venda não está mais `concluida`) — BR-059.
- Novo endpoint `PATCH /api/vendas/<id>/itens/<id>/garantia` e `GET .../historico-garantia` (mesmo padrão
  de `historico-comissao`).

**`irflow_os.py` / rota de status (Garantia de Reparo):**
- Ao mudar o status de uma OS para `Finalizado` (`atualizar_status_os`), o payload passa a exigir uma
  atribuição de `tipo_garantia_id` por linha de `os_reparos` da OS — rejeita a conclusão se faltar
  qualquer uma (BR-061). Resolve, congela snapshot e calcula `garantia_data_fim` a partir de
  `data_finalizado`, por linha.
- Ao mudar o status de uma OS `Finalizado` para `Cancelado` (ou qualquer cancelamento pós-conclusão),
  zera a Garantia de Reparo de todas as linhas já concedidas, com evento de auditoria — BR-064.
- Nova função de correção (mesmo shape de `corrigir_garantia_item`), só `admin`, sem motivo — BR-065.
- Novo endpoint `PATCH /api/ordens/<id>/reparos/<reparo_id>/garantia` e `GET .../historico-garantia`.

**`listar_garantias()` (`irflow_blueprints_api.py`) — reescrita:**
- Passa a iterar por linha de `os_reparos` (não mais por OS inteira) — uma OS com 3 reparos gera até 3
  entradas de garantia, cada uma com seu próprio prazo (BR-062).
- Para reparos com `tipo_garantia_id` preenchido (dados novos, pós-migração): usa `garantia_data_fim`
  gravado.
- Para reparos com `tipo_garantia_id` `NULL` (dados históricos, anteriores a esta sprint): mantém o
  fallback ao cálculo fixo de 90 dias (`GARANTIA_REPARO_DIAS_PADRAO`) a partir de `data_finalizado` —
  única forma de não fazer garantias antigas "desaparecerem" da tela sem inventar um dado que nunca foi
  de fato concedido (ver "Estratégia de Migração").
- `Clientes.jsx` consome o mesmo endpoint (`garantiasApi.list`) — resposta reestruturada por linha de
  reparo é compatível desde que o frontend agrupe por OS ao exibir (ver "Impacto no Frontend").

---

## Impacto no Frontend

- **Nova página "Tipos de Garantia"** (menu próprio, mesmo padrão de Tipos de Reparo/Tabelas de Preço) —
  CRUD simples, só visível/editável por `admin`.
- **`Vendas.jsx` (Nova Venda):** novo campo obrigatório "Tipo de Garantia" (select), junto de forma de
  pagamento/desconto.
- **`VendaDetalhe.jsx`:** exibir a Garantia de Venda concedida ao item; seção de correção (visível só
  para `admin`) com histórico — mesmo padrão visual já usado para Ajuste Comercial/Comissão.
- **Conclusão de OS (`EditOrder.jsx` ou onde o status muda para `Finalizado`):** exigir seleção de Tipo de
  Garantia por reparo antes de confirmar a conclusão.
- **`Garantias.jsx`:** ajustar para exibir uma linha por reparo (com seu próprio prazo), não mais uma
  linha agregada por OS — ainda agrupável visualmente por OS na mesma tela.
- **`Clientes.jsx`:** ajustar o consumo do endpoint reestruturado, mantendo a experiência atual (lista de
  garantias do cliente).
- **`frontend/src/api/client.js`:** novo objeto `tiposGarantia` (list/create/update); novos métodos em
  `vendas` (`atribuirGarantiaItem`/`historicoGarantiaItem`) e em `ordens` (equivalentes por reparo).

---

## Estratégia de Migração

1. Todas as colunas novas são aditivas (`ALTER TABLE ADD COLUMN`) — sem recriação de tabela, sem janela
   de manutenção.
2. Vendas e OS já concluídas antes desta sprint ficam com `tipo_garantia_id` `NULL` — **nunca
   backfilled**: não inventar uma garantia que nunca foi de fato concedida no momento da venda/conclusão
   original (mesmo princípio já usado com `desconto_aprovado_em`, BR-054).
3. `listar_garantias()` mantém o fallback ao cálculo fixo de 90 dias exclusivamente para linhas com
   `tipo_garantia_id NULL` — dado histórico continua visível na tela, só que sob a regra antiga; qualquer
   OS concluída a partir desta sprint é sempre obrigatória (BR-061), nunca cai nesse fallback.
4. `GARANTIA_REPARO_DIAS_PADRAO` (`irflow_core.py`) permanece definida, mas passa a ser usada só nesse
   fallback histórico — comentário no código deixando isso explícito (mesmo tratamento de
   "deprecada, mantida por compatibilidade" já usado em `limite_desconto_livre`).

---

## Testes

- **`tipos_garantia` (novo módulo):** CRUD, só `admin` cria/edita, leitura aberta a qualquer autenticado,
  desativar (`ativo=0`) não afeta garantias já concedidas.
- **`calcular_data_fim_garantia()` — tratada como peça crítica, testada isoladamente** (aprovação do CTO,
  2026-07-29): casos de calendário que costumam gerar erro, cada um com teste dedicado — `31/01 + 1 mês`,
  `29/02` em ano bissexto, meses de 30 e 31 dias, virada de ano (`ex.: 11/2026 + 3 meses`). Compartilhada
  por dois domínios (Vendas e Assistência) — um erro aqui se propaga para os dois, não é lógica
  descartável.
- **Garantia de Venda:** atribuição obrigatória na criação (rejeita sem `tipo_garantia_id`), snapshot
  correto, `garantia_data_fim` calculado certo, cancelamento zera com auditoria, correção só `admin` sem
  motivo, correção rejeitada se venda não está `concluida`, histórico expõe os eventos.
- **Garantia de Reparo:** atribuição obrigatória na conclusão (rejeita `Finalizado` sem garantia em
  alguma linha de reparo), múltiplos reparos com garantias diferentes mantêm cada um sua própria data,
  cancelamento pós-conclusão zera com auditoria, correção só `admin` sem motivo, histórico por reparo.
- **`listar_garantias()`:** dado histórico (`tipo_garantia_id NULL`) cai no fallback de 90 dias; dado novo
  usa `garantia_data_fim` gravado; uma OS com múltiplos reparos gera múltiplas entradas.
- **Regressão:** `vendedor`/`tecnico`/`estoque` não podem corrigir garantia (403); criar venda sem
  `tipo_garantia_id` é rejeitado; finalizar OS sem atribuir garantia a todo reparo é rejeitado.

---

## Critérios de Aceite

- [ ] Todos os casos de teste acima implementados e passando
- [ ] `ruff check .` / `npm run lint` / `npm run build` sem erros novos
- [ ] Nenhuma regressão na suíte existente
- [ ] `listar_garantias()` continua funcionando para dados históricos (fallback) e passa a funcionar por
      linha de reparo para dados novos
- [ ] QA manual: criar venda exigindo Tipo de Garantia → concluir OS exigindo Tipo de Garantia por
      reparo → admin corrige uma garantia (sem motivo) → cancelar venda/OS zera a garantia → tela de
      Garantias e perfil do cliente mostram os dados corretamente

---

## Riscos

| Risco | Mitigação |
|---|---|
| Reescrever `listar_garantias()` de "por OS" para "por reparo" quebra o contrato de resposta para os dois consumidores atuais (`Garantias.jsx`, `Clientes.jsx`) | Atualizar os dois no mesmo PR; teste de regressão explícito para cada consumidor |
| Esquecer o fallback histórico faz garantias antigas desaparecerem da tela | Teste de regressão dedicado com dado "pré-migração" (`tipo_garantia_id NULL`) |
| Cálculo de meses de calendário mal feito gera datas erradas em meses de 28-31 dias ou viradas de ano | Função utilitária isolada (`calcular_data_fim_garantia`) com testes de caso de borda dedicados, nunca duplicada inline em cada domínio |
| Duplicar a lógica de cálculo/snapshot entre Vendas e Assistência | Função compartilhada em `irflow_core.py`, chamada pelos dois `service`s — nenhum dos dois reimplementa |
| Exigir Tipo de Garantia bloquear a conclusão de OS existentes em andamento no momento do deploy | Só afeta a transição para `Finalizado` a partir do deploy — OS já finalizadas antes não são reabertas nem exigem retroativamente |

---

## Rollback

Aditivo em ambos os lados (tabela nova + colunas novas) — reverter o código é suficiente; nenhuma coluna
precisa ser recriada. `tipos_garantia` pode permanecer no schema sem uso se o revert acontecer, mesmo
padrão já aceito no projeto.

---

## Questões em Aberto

Nenhuma questão de **negócio** nova encontrada durante este plano — a Discovery (BR-055 a BR-066) já
fechou todos os pontos de regra necessários, incluindo o ajuste de motivo/auditoria (`2e91c5e`). As
decisões de implementação abaixo não são regra de negócio, são registradas aqui só para o CTO confirmar
antes da aprovação:

- Nome e localização do novo módulo compartilhado (`fluxoly_tipos_garantia_*`) — proposto por ser
  consumido igualmente por Vendas e Assistência, sem pertencer a nenhum dos dois.
- Local da função de cálculo de data (`irflow_core.py::calcular_data_fim_garantia`) — proposto por já ser
  o lugar de utilitários puros compartilhados no projeto (`normalizar_status_os`, `to_float`, etc.).
