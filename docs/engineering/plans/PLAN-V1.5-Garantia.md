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
- [x] Implementação — concluída (commits `ea53bbb`..`0551339`, ver branch `feat/vendas-v1-5-garantia`)
- [x] Testes — 693 testes no total (14 em `tests/test_tipos_garantia.py`, mais os de
      `test_garantia_reparo.py`/`test_listar_garantias.py`/`test_vendas.py`), `ruff check .` limpo,
      `npm run lint`/`npm run build` sem erros novos. 1 falha pré-existente e não relacionada
      (`tests/test_sentry_init.py`, erro de ambiente Windows ao carregar `_overlapped`/asyncio, não
      reproduz em CI/produção)
- [x] QA Manual — concluído em 2026-07-30, ver seção "QA Manual" abaixo
- [x] Revisão Arquitetural — concluída em 2026-07-30, ver seção "Revisão Arquitetural" abaixo
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

## QA Manual

Executado em 2026-07-30, servidor Flask real + Vite real + banco isolado (`IR_FLOW_DATA_DIR`, nunca
`database.db`), navegador real via Claude in Chrome para os fluxos com UI e `curl` para o único fluxo sem
UI (correção de Garantia de Reparo, ver "Impacto no Frontend" — não incluído no escopo original).

- **Tipos de Garantia (BR-055):** criado "Garantia Padrão" (12m) e "Sem Garantia" (0m) via UI; lista,
  duração formatada ("Sem garantia" para 0m), badge Ativo/Inativo corretos.
- **Garantia de Venda obrigatória (BR-056):** `Nova Venda` bloqueia com toast "Selecione o Tipo de
  Garantia." se o campo não for preenchido; venda concluída com sucesso após selecionar.
- **Snapshot e correção (BR-057/BR-059):** `VendaDetalhe.jsx` exibe "Garantia Padrão — até
  <data>" corretamente; correção pelo admin (Garantia Padrão → Sem Garantia) recalcula
  `garantia_data_fim` a partir da `garantia_data_inicio` original (não reemite a partir de hoje) e
  registra 2º evento no histórico.
- **Cancelamento zera a garantia (BR-058):** cancelar a venda zera o snapshot (`Sem garantia
  registrada`) e o botão "Corrigir garantia" desaparece (correção só permitida em venda `concluida`).
- **Garantia de Reparo obrigatória por linha (BR-061):** dialog "Garantia de Reparo" ao clicar
  "Finalizar OS" bloqueia com toast se qualquer reparo ficar sem seleção; testado com 2 reparos
  (Troca de Bateria/Troca de Tela) recebendo tipos de garantia diferentes (BR-062) — confirmado que
  cada linha mantém seu próprio prazo.
- **`listar_garantias()` por linha (BR-062/BR-063):** `Garantias.jsx` mostra 2 entradas para a mesma OS,
  agrupadas visualmente (OS/Cliente/Modelo/Data não repetidos na 2ª linha), cada uma com o badge de
  prazo correto (`365d restantes` para 12m, `Vencendo (0d)` para 0m).
- **Cancelamento pós-conclusão zera a Garantia de Reparo (BR-064):** cancelar a OS Finalizada remove
  as linhas de `Garantias.jsx` (a query já filtra `status='Finalizado'`) — confirmado via API que o
  snapshot foi zerado, não só que a OS saiu do status.
- **Correção da Garantia de Reparo (BR-065), via `curl` (sem UI no escopo do plano):** `vendedor`
  recebe 403; `admin` corrige com sucesso (200) e o histórico registra o evento com `valor_anterior`/
  `valor_novo` completos — validado contra o servidor real, não só o `flask.testing` client.
- **Reasserir Finalizado não exige garantia de novo / edição preserva snapshot:** editada a OS #2
  (já Finalizada) alterando só `valor_cobrado`, sem tocar Status — nenhum dialog de garantia apareceu
  e a garantia já corrigida (Sem Garantia) permaneceu intacta após salvar. Valida na prática o rewrite
  de `salvar_reparos_os` (DELETE+INSERT cego → sync não-destrutivo) feito especificamente para não
  apagar esse snapshot numa edição comum.
- **Caso de borda investigado (não é um gap):** cogitou-se que uma OS finalizada sem nenhum reparo
  selecionado desapareceria silenciosamente de `listar_garantias()` (o `JOIN` com `os_reparos` virou
  `INNER JOIN`). Testado diretamente: `criar_ordem` já rejeita `"Selecione ao menos um reparo."` — uma
  OS sem reparo nunca existe, então o cenário é impossível por construção. Nenhuma ação necessária.

**Achado (KI-028, registrado em `KNOWN_ISSUES.md`, não corrigido nesta sessão):** `garantia_data_fim`/
`garantia_data_inicio` (datas puras, sem horário) aparecem um dia antes do valor real gravado no banco em
qualquer tela — `new Date("2027-07-30").toLocaleDateString("pt-BR")` é interpretado como UTC-meia-noite e
renderizado no fuso local (`America/Sao_Paulo`, UTC-3). O dado no banco está sempre correto; é só exibição.
Mesmo padrão já existe em outras telas (`Garantias.jsx`, `Clientes.jsx`, `OperationalCosts.jsx`,
`Reports.jsx`, `Stock.jsx`), mas os campos de garantia são sempre data pura, então o efeito é
determinístico. Não atende nenhum critério objetivo de interrupção (`ENGINEERING_GUIDE.md` §11) — não
interrompeu o QA, foi caracterizado e reportado ao usuário (CTO) para decisão sobre corrigir agora ou
depois.

---

## Revisão Arquitetural

Aplicadas as 4 perguntas de `docs/engineering/adr/ADR-010.md` "Etapa 6":

1. **Coerência do domínio** — a V1.5 não revoga nenhuma regra existente; ela *substitui* o prazo fixo de
   90 dias para reparos novos, mantendo `GARANTIA_REPARO_DIAS_PADRAO` deliberadamente vivo só como
   fallback de dado histórico (`tipo_garantia_id IS NULL`), documentado em comentário no código e na
   seção "Estratégia de Migração" deste plano. Não há leitura/escrita órfã de uma regra descontinuada.
2. **Autorização centralizada** — `corrigir_garantia_item` (Vendas) e `corrigir_garantia_reparo_route`
   (Assistência) checam `usuario_perfil != "admin"` inline, cada uma no seu próprio módulo — mesmo padrão
   já usado por Ajuste Comercial e Comissão (não há uma função de autorização única no projeto para isso
   hoje; a V1.5 não piora nem resolve essa característica pré-existente).
3. **Risco de vazamento de dado** — Garantia de Venda é **deliberadamente aberta** a qualquer perfil
   autenticado (diferente da Comissão, que é ocultada) — decisão de BR-057 confirmada no código
   (`_item_para_dict` sempre inclui os campos de garantia, sem função de ocultação). Nenhum vazamento:
   é o comportamento pretendido, não um esquecimento.
4. **Consistência da máquina de estados** — validado no QA Manual: cancelamento (venda ou OS) zera a
   garantia na mesma transação; correção só é aceita em venda `concluida`/OS `Finalizado` (compare-and-
   swap); reasserir um status já `Finalizado` não reabre a exigência de garantia; editar uma OS já
   Finalizada preserva o snapshot já concedido (fix deliberado em `salvar_reparos_os`, sem o qual um
   DELETE+INSERT cego apagaria a garantia em qualquer edição não relacionada a status).

**Achado adicional (fora das 4 perguntas, documentado aqui por não ser bug de regra de negócio):**
`vendas_itens.garantia_data_inicio`/`os_reparos.garantia_data_inicio` usam `date.today()` (Python, fuso
local do processo), enquanto `vendas.criado_em`/`os.data_finalizado` usam `datetime('now')` do SQLite
(UTC). Os dois podem divergir por um dia perto da virada de meia-noite UTC (observado nesta sessão: venda
com `criado_em` "31/07/2026 00:10" e `garantia_data_inicio` "2026-07-30"). Não é um bug de regra de
negócio — cada campo está internamente correto para a sua própria definição de "hoje" — mas é uma
inconsistência de fonte de tempo que já existia antes da V1.5 (outros campos `data`/`data_finalizado` no
projeto também vêm de `datetime('now')` UTC) e que a V1.5 não introduz de propósito nem piora
estruturalmente. Registrado aqui como observação, não como ação — combinado com KI-028, é o tipo de
detalhe que fica mais visível quando datas puras são exibidas de forma inconsistente entre telas.

**Gate:** nenhuma inconsistência transversal ficou sem documentação — coerência do domínio, autorização e
vazamento de dado confirmados sem achado; máquina de estados confirmada consistente; os dois achados
(KI-028 e a divergência de fonte de tempo UTC vs. local) estão registrados, não deixados implícitos.

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
