# BUSINESS_RULES.md — Livro de Regras de Negócio

Regras de negócio da Fluxoly em um único lugar, numeradas e rastreáveis — não código, não schema, apenas
a regra em si e de onde ela vem. Antes deste documento, essas regras estavam espalhadas entre
`docs/product/features/VENDAS.md`, comportamento implícito do código, e conversas — cada uma reconstruída
do zero sempre que alguém precisava confirmar "isso já é uma regra ou é só o que o código faz hoje?".

**Última revisão:** 2026-07-10
**Regra de escrita:** toda entrada tem status e fonte. Nenhuma regra aqui foi inventada — ou vem do
código real (lido linha a linha, citado com arquivo/função), ou de uma decisão já registrada em
`VENDAS.md`/`BRAND_IDENTITY.md`, ou de input direto do Product Owner nesta conversa.

**Legenda de status:**
- ✅ **Implementado** — o código hoje aplica essa regra; verificado lendo o código-fonte diretamente.
- 📋 **Especificado** — decisão de negócio já tomada (`VENDAS.md` ou Product Owner), mas o domínio ainda
  não existe no código (Vendas).
- 🟡 **Observado, não confirmado como decisão** — comportamento real do código, mas sem registro de que
  foi uma escolha deliberada de negócio (ver nota em cada caso).

---

## Autenticação e Usuários

**BR-001 — ✅ Implementado**
Login só é bem-sucedido se o usuário está ativo (`ativo = 1`) e o hash da senha confere.
*Fonte: `irflow_blueprints_auth.py`, `POST /api/auth/login`; `docs/engineering/DATABASE.md` tabela `usuarios`.*

**BR-002 — ✅ Implementado**
Um usuário não pode desativar nem excluir a própria conta enquanto está logado.
*Fonte: `docs/engineering/DATABASE.md` tabela `usuarios`; `tests/test_users.py`.*

**BR-003 — ✅ Implementado**
Perfis (`admin`, `tecnico`, `vendedor`) são checados por lista explícita de perfis permitidos por rota
(`ROUTE_PERMISSIONS`) — não existe hierarquia entre perfis.
*Fonte: `docs/engineering/ARCHITECTURE.md` seção 4.*

---

## Estoque

**BR-004 — ✅ Implementado**
Consumo de peça é sempre debitado por lote, do mais antigo para o mais novo (FIFO).
*Fonte: `irflow_os.py::_consumir_lotes_fifo`.*

**BR-005 — ✅ Implementado**
Um item de estoque não pode ser excluído enquanto estiver em uso (`os_pecas`) em uma OS que não esteja
`Finalizado` nem `Cancelado`.
*Fonte: `irflow_blueprints_api.py::deletar_estoque`.*

**BR-006 — ✅ Implementado**
Devolução de peça ao estoque cria um novo lote de retorno — nunca reincorpora silenciosamente ao lote de
origem, preservando rastreabilidade de que aquela quantidade voltou por devolução.
*Fonte: `irflow_os.py::_criar_lote_retorno`.*

**BR-007 — ✅ Implementado**
Quantidade de estoque nunca fica negativa — todo decremento é limitado a zero (`MAX(0, quantidade - 1)`).
*Fonte: `irflow_os.py::consumir_peca_da_os`; corrigido como hotfix B-11 na Sprint 2.5.*

---

## Ordens de Serviço (Assistência)

**BR-008 — ✅ Implementado**
Excluir uma OS que não está `Finalizado` nem `Cancelado` devolve automaticamente todas as peças
consumidas ao estoque.
*Fonte: `irflow_blueprints_api.py::deletar_ordem`.*

**BR-009 — ✅ Implementado**
Excluir uma OS que já está `Finalizado` ou `Cancelado` **não** devolve peças novamente — a devolução já
ocorreu quando o status mudou, evitando duplicar o retorno ao estoque.
*Fonte: mesma função de BR-008.*

**BR-010 — ✅ Implementado**
Mudar o status de uma OS para `Cancelado` (vindo de um status não-cancelado) devolve as peças ao estoque.
*Fonte: `irflow_blueprints_api.py::atualizar_status_os`.*

**BR-011 — ✅ Implementado**
Editar uma OS não-cancelada (`PUT /api/ordens/<id>`) devolve as peças atualmente registradas e reconsome
as peças do novo payload — é uma substituição atômica, não um ajuste incremental.
*Fonte: `irflow_blueprints_api.py::atualizar_ordem`.*

**BR-012 — ✅ Implementado**
Peça incompatível com o modelo da OS bloqueia a atualização inteira (rollback) — nunca é salva
silenciosamente como incompatível.
*Fonte: `irflow_os.py::modelo_compativel`, usado em `atualizar_ordem`.*

**BR-013 — ✅ Implementado (era bug, corrigido em 2026-07-10)**
Editar uma OS (`PUT`) ou mudar seu status (`PATCH .../status`) exige um `status` explícito e válido no
payload — requisição sem `status` ou com valor desconhecido é rejeitada com erro, nunca silenciosamente
aceita. `data_finalizado` só recebe valor quando o **novo** status explicitamente enviado é `Finalizado`
(preservando a data original se já existia); ao mudar deliberadamente para qualquer outro status,
`data_finalizado` é limpo (`NULL`) — mas só quando o chamador de fato pediu essa mudança.
*Fonte: `atualizar_ordem` e `atualizar_status_os`, `irflow_blueprints_api.py`.* **Histórico:** até
2026-07-10 esta regra não existia — `normalizar_status_os()` sem `status_padrao=""` fazia `status`
ausente/inválido ser silenciosamente normalizado para `"Em andamento"`, então editar uma OS Finalizada
sem reenviar `status` a reabria e apagava `data_finalizado` sem erro. Corrigido via
`hotfix/status-os-padrao-vazio` (KI-015, `docs/operations/KNOWN_ISSUES.md`) — as duas correções já
existiam prontas na branch `test/sprint-2-4-regras-negocio-os` desde 2026-07-07 mas nunca haviam chegado
a `main`.

**BR-014 — ✅ Implementado**
O vendedor informado em uma OS deve ser um vendedor cadastrado válido, **exceto** quando o cliente é
`"IR Phones"` — um bucket interno de relatório, isento dessa validação.
*Fonte: `irflow_os.py::vendedor_valido`, usado em `atualizar_ordem`.*

---

## Compras / Lista de Compras (Shopping List)

**BR-015 — ✅ Implementado**
Todo item de lista de compras segue um workflow de status (`PENDENTE` → outros estados → `RECEBIDO` ou
cancelado), com timestamp próprio por transição (`purchased_at`, `received_at`, `cancelled_at`).
*Fonte: `docs/engineering/DATABASE.md` tabela `shopping_list`.*

**BR-016 — ✅ Implementado**
Toda mudança em um item da lista de compras é auditada — log com valor anterior, valor novo, usuário e
ação.
*Fonte: `docs/engineering/DATABASE.md` tabela `shopping_list_logs`.*

---

## Clientes

**BR-023 — ✅ Implementado**
Cadastro de cliente exige nome e ao menos um contato (telefone ou e-mail) — sem isso o cliente não pode
ser reencontrado depois.
*Fonte: `irflow_clientes_service.py::criar_cliente`/`atualizar_cliente`; `docs/product/features/CLIENTES.md`
"Decisões estruturais".*

**BR-024 — ✅ Implementado**
Cliente com OS vinculada (`os.cliente_id`) não pode ser excluído — mesmo padrão de BR-005 (item de
estoque em uso não pode ser excluído).
*Fonte: `irflow_clientes_service.py::excluir_cliente`, `irflow_clientes_repository.py::possui_os_vinculada`;
`docs/product/features/CLIENTES.md` "Casos de erro".*

---

## Unidades_Serializadas (rastreamento por IMEI/serial)

*Tabela evoluída de `estoque_unidades` na migração ADR-007 (2026-07-21) — mesmas regras abaixo,
estendidas para cobrir origem em `estoque` OU `produtos`.*

**BR-025 — ✅ Implementado**
Uma unidade individual por IMEI só pode ser cadastrada com origem em exatamente um de: um item de
estoque marcado com `requer_imei = 1`, ou um produto marcado com `requer_rastreio_unidade = 1` —
cadastro sem nenhuma origem, com ambas, ou em item/produto não marcado é rejeitado.
*Fonte: `irflow_unidades_serializadas_service.py::criar_unidade`; `docs/product/features/IMEI.md`
"Decisões estruturais"; ADR-007 (Regra de Ouro).*

**BR-026 — ✅ Implementado**
Transição de status de uma unidade só é permitida entre `disponivel`, `em_reparo` e `devolvido`
(`disponivel ↔ em_reparo`, `em_reparo → devolvido`, `devolvido → disponivel` direto) — `reservado` e
`vendido` existem no schema para o futuro módulo de Vendas, mas nenhuma transição desta sprint os
produz ou aceita como destino.
*Fonte: `irflow_unidades_serializadas_service.py::TRANSICOES_VALIDAS`; `docs/product/features/IMEI.md`,
decisão confirmada com o usuário em 2026-07-11 (devolvido → disponivel direto).*

---

## Produtos (catálogo comercial)

Domínio novo, Sprint Comercial 0.1 — catálogo de itens à venda (iPhone, Apple Watch, AirPods,
Acessório), separado do domínio Estoque (peças de reparo). Decisão de arquitetura investigada e
confirmada com o usuário antes de implementar: `estoque.tipo`/`qualidade` são listas fechadas
hardcoded para peça de reparo, incompatíveis com o vocabulário de um catálogo comercial.

**BR-027 — ✅ Implementado**
`categoria` de um produto só pode ser uma das quatro da lista fechada (iPhone, Apple Watch, AirPods,
Acessório) e `condicao` só pode ser uma de (Novo, Seminovo, Vitrine) — valor fora dessas listas é
**rejeitado com 400**, nunca normalizado/mascarado para um valor default.
*Fonte: `irflow_produtos_service.py::_validar_campos`; `PRODUTOS_CATEGORIAS`/`PRODUTOS_CONDICOES` em
`irflow_reference_data.py`. Decisão deliberada: `_normalizar_tipo_estoque`/`_normalizar_qualidade_estoque`
mascaram entrada desconhecida com um default silencioso — esse padrão já causou duas dívidas reais
neste projeto (KI-015, KI-016), não repetido em código novo.*

**BR-028 — ✅ Implementado**
Margem de um produto (preço de venda − preço de custo) nunca é persistida como coluna — é sempre
calculada no momento da leitura, e é `None` quando o preço de custo não foi informado.
*Fonte: `irflow_produtos_service.py::_produto_para_dict`; mesmo princípio de BR-019 (`vendas.margem`).*

**BR-029 — ✅ Implementado**
Criar, editar ou excluir um produto do catálogo é restrito ao perfil `admin` (preço/margem é dado
sensível); listar e consultar é permitido a qualquer usuário autenticado (vendedor precisa consultar o
catálogo numa venda).
*Fonte: `irflow_produtos_controller.py`. Decisão de negócio V1, conservadora — abrir criação/edição
para outros perfis é decisão pendente de validação com cliente real, ver
`docs/company/CUSTOMER_FEEDBACK.md`.*

---

## Vendas (especificado, não implementado)

Decisões já tomadas em conversa entre Product Owner e engenharia (2026-07-09), registradas em
`docs/product/features/VENDAS.md` — nenhuma delas está no código ainda.

**BR-017 — 📋 Especificado**
Um IMEI só pode estar reservado ou vendido em um atendimento por vez; a reserva expira automaticamente se
a venda não fechar, liberando o aparelho.
*Fonte: `VENDAS.md` — "Fluxo completo", "Decisões já tomadas".*

**BR-018 — 📋 Especificado**
Desconto acima do limite do vendedor exige aprovação de um `admin`; sem admin disponível, a venda fica
bloqueada em "aguardando aprovação" — nunca há bypass.
*Fonte: `VENDAS.md` — "Decisões já tomadas", "Casos de erro".*

**BR-019 — 📋 Especificado**
Comissão do vendedor é sempre calculada sobre a margem (venda − custo), nunca sobre o valor bruto.
*Fonte: `VENDAS.md` — "Decisões já tomadas", "Critérios de aceite".*

**BR-020 — 📋 Especificado**
Garantia de venda tem prazo próprio por tipo de aparelho (novo/seminovo), independente do prazo fixo de
90 dias hardcoded do reparo.
*Fonte: `VENDAS.md` — "Decisões já tomadas".*

**BR-021 — 📋 Especificado**
Aparelho escolhido sem estoque disponível no momento da confirmação gera erro explícito antes do
pagamento, nunca depois.
*Fonte: `VENDAS.md` — "Casos de erro".*

**BR-022 — ✅ Implementado (pré-requisito pronto; Vendas em si segue não implementado)**
Cliente é uma entidade própria (tabela `clientes`) — implementado na Sprint P0.1 como fundação
reutilizável, antes do módulo de Vendas em si existir. `os.cliente_id` (aditivo, nullable) já permite
vincular uma OS a um cliente, mas nenhuma venda existe ainda para aplicar a regra "nenhuma venda salva
nome como texto solto" — isso será validado quando `VENDAS.md` for implementado.
*Fonte: `irflow_clientes_service.py` (BR-023, BR-024); `VENDAS.md` — "Critérios de aceite";
`docs/engineering/DOMAIN_MODEL.md` seção 1.12.*

### Regras candidatas — exemplos citados nesta conversa (2026-07-10), pendentes de confirmação formal

O Product Owner citou estes exemplos ao propor este documento. Onde já existe decisão formal em
`VENDAS.md`, cito o BR correspondente. Onde não existe ainda, registro como candidata — não como regra
confirmada, para não inflar o número de "especificadas" com algo ainda não decidido no spec oficial.

- *"Um IMEI só pode pertencer a um aparelho"* — já coberto por BR-017 (reserva/venda por atendimento).
- *"Uma venda nunca pode existir sem um vendedor"* — **candidata**, não está em `VENDAS.md` "Decisões já
  tomadas" hoje; consistente com `VENDAS.md` "Quem usa" (vendedor conduz a venda), mas não formalizada
  como regra de validação.
- *"Uma reserva expira automaticamente"* — já coberto por BR-017.
- *"Garantia nunca pode ser alterada após emitida"* — **candidata**, não está em `VENDAS.md` hoje.
- *"Uma venda cancelada devolve o IMEI ao estoque"* — **candidata**, análoga a BR-010 (OS cancelada
  devolve estoque) mas `VENDAS.md` não trata cancelamento de venda explicitamente ainda.

Recomendação: formalizar essas 3 candidatas em `VENDAS.md` "Decisões já tomadas" (não aqui) na próxima
revisão do spec de Vendas — este documento reflete o que já foi decidido em outro lugar, não decide por
conta própria.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — fonte das regras de Vendas (BR-017 a BR-022)
- `docs/product/features/CLIENTES.md` — fonte das regras de Clientes (BR-023, BR-024)
- `docs/engineering/DOMAIN_MODEL.md` — domínios e arquivos onde cada regra implementada vive
- `docs/engineering/DATABASE.md` — schema citado nas regras de Estoque/Compras
- `docs/operations/KNOWN_ISSUES.md` — bugs já corrigidos que originaram alguma regra (ex.: BR-007 ↔ B-11)
