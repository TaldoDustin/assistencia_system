# DISCOVERY — Lista de Aparelhos Disponíveis (ferramenta interna de apoio a vendas/estoque)

**Status:** ✅ APROVADA pelo Product Owner (CTO) em 2026-09-03 — segue para o Plano Técnico (ADR-010 etapa 2).
**Data:** 2026-09-03 (revisões no mesmo dia: pivô para uso interno → mapeamento do `.xls` → confirmação da API com token → gate)
**Origem:** pedido do CTO — "criar uma cópia" da lista de preços da Skyline
(`https://tabelaprecos.gruposkytech.com/lista-precos.html`), rebrandada para Fluxoly, alimentada por
dados do MercadoPhone, com deduplicação, acessível por link com senha.

> Este documento **decide regras de negócio**, não implementação. Onde guardar dado, stack de build,
> onde roda o script → Plano Técnico, depois deste gate.

---

## 0. O que a ferramenta é (depois de 2 pivôs)

Não é a página pública da Skyline. É uma **ferramenta interna** com **duas áreas**, cada uma atrás de
uma senha (tela de bloqueio estilo "desbloquear celular"):

| Área | Senha | Quem usa | Vê |
|---|---|---|---|
| **Geral** | senha A | Vendedores | Modelo, atributos, grade, **preço de venda**, disponibilidade. Aparelhos **reservados somem** daqui. |
| **Estoque** | senha B | Organizador de estoque | Tudo da Geral **+ custo/margem + dias em estoque**, e a ação de **reservar** um aparelho (que o tira da Geral e o joga na lista de "Reservados"). |

Objetivo: vendedor sabe na hora o que há para vender e por quanto; o organizador de estoque controla o
que já está comprometido.

---

## 1. Referência (Skyline) — o que aproveitar

Página estática (HTML + CSS inline + 2 JS sem libs) que consome 1 webhook e renderiza tabela filtrável:
busca textual, filtro Marca, filtro Qualidade, 3 KPIs, header sticky, export `.xlsx` gerado no browser.
**Aproveitar toda essa estrutura de UI.** Não aproveitar: o modelo de dados (grades da Skyline, webhook
público que vaza custo/estoque deles).

---

## 2. Decisões do CTO (2026-09-03)

| # | Decisão | Valor |
|---|---|---|
| D-1 | Marca no header | **IR Phones** (a loja). A identidade Pulse do Fluxoly pode aparecer discreta como "powered by", a decidir no Plano. |
| D-2 | Arquitetura base | **Página estática standalone + build**, **+ um armazenamento mínimo só para as reservas** (QA-23 = opção b). Todo o resto é snapshot estático. |
| D-3 | Acesso | **Duas senhas → duas áreas** (Geral / Estoque). Tela de bloqueio simples; senha certa abre a área correspondente. Sem contas individuais. |
| D-4 | Dedup | **IMEI completo**, só no backend/script. Nunca vai íntegro para o navegador. |
| D-5 | Fonte de dados | **API nova do MercadoPhone** (`platform.mercadophone.tech`, `X-API-Key` — token fornecido pelo CTO). `GET /api/v1/inventory` paginado + tabelas de lookup. `.xls` deixa de ser necessário. |
| D-6 | Exibição + reserva | Unidade a unidade. Identificador visível = **últimos 4 dígitos do IMEI**, estendido (5, 6…) **só nos IDs que colidiriam**. O organizador de estoque marca unidades como **reservadas**. |
| D-7 | Layout | Agrupar por **modelo + grade** para legibilidade (não lista plana crua). |
| D-8 | Preço | `valorVenda` do MercadoPhone (um número — `valorVenda2/3`, `valorPrazo`, `parcelas` vêm nulos). |
| D-9 | Escopo | **Só aparelhos Apple serializados**: `tipoProduto` ∈ {IPHONE, IPAD, MACBOOK, APPLE WATCH}. Fora: acessórios (`snAcessorio=1`), serviços ("TAXA DE ENTREGA"), fones/caixas de som JBL, brindes. |
| D-10 | Custo | `valorCusto` e margem **só na área Estoque**. Nunca na Geral. |
| D-11 | Domínio | `estoque.fluxoly.com`. Deploy na **Vercel** (estático); **Render** só se o armazenamento de reservas precisar de um backend próprio. |

---

## 3. QA-1 (IMEI × exibição) — RESPONDIDA

- Exibição unidade a unidade; ID curto do final do IMEI.
- **Para quê:** referência interna — "me vê o 8890" para achar a unidade exata.
- **Desempate:** só os IDs que colidem crescem (`8890` único fica `8890`; par vira `68890`/`28890`).
- **Estabilidade:** ok o ID mudar quando entra outra unidade terminada igual.
- **Layout:** agrupado por modelo + grade (D-7).
- **Risco:** baixo — ferramenta interna e sufixo isolado não clona/bloqueia aparelho (precisa dos 15
  dígitos). IMEI completo só no script; snapshot que vai ao navegador leva só o sufixo cortado.

---

## 4. Modelo de dados — API nova do MercadoPhone (confirmado com o token, 2026-09-03)

`GET https://platform.mercadophone.tech/api/v1/inventory?limit=100&page=N` — header `X-API-Key`.
`total` 583, paginação `page`/`limit`. Cada item traz (campos relevantes):

| Campo API | Uso |
|---|---|
| `id` | identificador interno (é o "Cód." do `.xls`) |
| `imei` / `imei2` | IMEI principal / segundo SIM. `imei` = chave de dedup + fonte do ID visível |
| `serialNumber` | nº de série |
| `aparelhoDescricao` | modelo limpo, ex. `IPHONE 12 PRO MAX` (sem GB/cor) |
| `disponibilidade` (texto) / `produtoDisponibilidadeId` | situação — ver 4.2 |
| `snAcessorio` (0/1) · `snPeca` · `snServico` | flags de tipo |
| `tipoProdutoDescricao` / `tipoProdutoId` | `IPHONE` (3719) · `MACBOOK` (4959) · `APPLE WATCH` (4960) · `IPAD` (4961) · AIRPODS/PENCIL/etc. |
| `estadoProdutoId` | condição — lookup `product-conditions`: 2279 `LACRADO`, 2280 `SEMINOVO`, 2281 `OPEN BOX`, 4417 `NOVO`, 22563 `CPO`. `null` para serviço/acessório |
| `marcaId` / `marcaDescricao` | 1717 = APPLE |
| `corId` / `corDescricao` | ex. `BRANCO`, `TITÂNIO PRETO` |
| `gbId` / `gbDescricao` | ex. `128GB`, `256GB`. **Vem preenchido no registro do aparelho** (o `.null` que eu tinha visto era em acessório). Fallback: `catalog/storage-sizes` → campo `size`. QA-40 resolvida. |
| `estadoProdutoDescricao` | `LACRADO` / `SEMINOVO` / `OPEN BOX` / `NOVO` / `CPO` |
| `tipoProdutoDescricao` | `IPHONE` / `IPAD` / `MACBOOK` / `APPLE WATCH` / … |
| `saudeBateria` | % de saúde da bateria — **exibir na Geral** (iPhone/Watch/Mac quando houver) |
| `descricao` | string já formatada: `"<id> - IPHONE 13 - BRANCO - 128GB -  Estado: SEMINOVO -  IMEI: … -  IMEI 2: … -  SN: …"` |
| `valorVenda` | preço de venda (único preenchido) |
| `valorVenda2` / `valorVenda3` / `valorPrazo` / `parcelas` | vêm `null` em todos os aparelhos — não usar |
| `valorCusto` | custo — **só área Estoque** |
| `fornecedorNome` / `fornecedorId` | fornecedor — **não publicar em nenhuma das duas telas** |
| `dataEntrada` | data de entrada (dá para calcular "dias em estoque") |
| `snExibirCatalogo` (0/1) | flag "exibir no catálogo" — vem `0` em quase tudo hoje, **não usar como filtro** (ver QA-5) |

### 4.1 Filtro eletrônico × acessório (D-9) — agora limpo

`snAcessorio` separa 337 não-acessórios de 246 acessórios. Mas "não-acessório" ainda inclui
`TAXA DE ENTREGA` (tipo SERVIÇOS) e fones/caixas JBL (tipo FONE DE OUVIDO / CAIXA DE SOM), ambos com
`estadoProdutoId = null`. **Regra proposta:** incluir se `snAcessorio == 0` **e**
`tipoProdutoId ∈ {3719, 4959, 4960, 4961}` (iPhone/MacBook/Apple Watch/iPad). Confirmar se AirPods/
Apple Pencil entram (QA-39).

### 4.2 `produtoDisponibilidade` — só 4 valores, sem "Reservado" (confirmado via `catalog/availability`)

| id | nome | `snExibirPdv` | Geral mostra? |
|---|---|---|---|
| 1 | Disponível para venda | 1 | ✅ |
| 62177 | DISPONIVEL COM DETALHE | 1 | ✅ com etiqueta "com detalhe" |
| 2 | Laboratório | null | ❌ (em conserto) |
| 61058 | ANALISE | 0 | ❌ (em triagem) |

**Filtro da Geral = `snExibirPdv == 1`.** Hoje ≈ 212 aparelhos "Disponível" + 4 "com detalhe".

### 4.3 Nunca publicar — inclui dado pessoal

⚠️ **Achado (2026-09-03):** vários registros trazem `clienteNome` + `clienteId` e `fornecedorNome` com
**nome completo de pessoa física** (ex.: "LEONARDO DE SOUZA NOGUEIRA") — é quem vendeu/consignou o
aparelho para a loja. **Isso é dado pessoal.**

| Campo | Geral | Estoque |
|---|---|---|
| `valorCusto` | ❌ | ✅ (+ margem calculada) |
| `clienteNome` / `clienteId` / `fornecedorNome` / `fornecedorId` | ❌ | ❌ (não é útil para o organizador; e é PII) |
| `ncm` / `cfop*` / `cst` / `cest` / `codEan` (fiscais) | ❌ | ❌ |
| `obs` / `observacaoCatalogo` | ❌ | ❌ (texto livre, pode ter PII) |

O script de build deve montar os dois snapshots com uma **allowlist** de campos, não uma blocklist.

### 4.4 O `.xls` (histórico)

O export `.xls` que o CTO mandou (584 linhas, colunas `Cód.`/`Descrição completa`/`IMEI`/`Valor venda`/
`Valor custo`/`Quantidade`/`Data Entrada`/`Dias em Estoque`/`Disponibilidade`/`Modelo`/`GB`/`Marca`/
`Categoria`/`Sub-categoria`/`Fornecedor`) tem os **mesmos dados** da API, +coluna `GB` em texto (útil
para QA-40) e −`saudeBateria`. Fica como **fallback manual** se a API cair; não é o caminho principal.

---

## 5. Questões abertas

### Reserva / estado

> **QA-23 — RESOLVIDA (2026-09-03): opção (b), armazenamento próprio.**
> O CTO confirmou pela tela do MercadoPhone que a lista de estoque só tem 4 situações — `Disponível
> para venda` · `Laboratório` · `ANALISE` · `DISPONIVEL COM DETALHE` — **não existe "Reservado"**. Não
> dá para apoiar a reserva num status do MercadoPhone. Logo: a reserva é uma **sobreposição nossa** —
> uma lista pequena (IMEI/`Cód.` + vendedor + data) num armazenamento leve, lida pelo build da área
> Geral (para esconder) e escrita pela área Estoque. A escolha do mecanismo concreto (Vercel KV /
> Upstash / tabela no backend Fluxoly / etc.) é do **Plano Técnico**; pode exigir um ADR curto porque
> adiciona um serviço com estado. **Risco aceito:** quem tem a senha B pode reservar/desreservar
> (senha compartilhada não é login real) — ok para ferramenta interna.

<details><summary>Opções consideradas (histórico)</summary>
  - **(a)** O organizador marca "Reservado" **dentro do MercadoPhone**; a ferramenta só reflete no
    próximo sync. Zero infra nova. **CTO acha que existe no sync do MercadoPhone (2026-09-03).**
  - **(b)** Um backend mínimo só para a sobreposição de reservas (função serverless + KV tipo Vercel
    KV/Upstash, ou um endpoint no Fluxoly). A Geral lê essa lista para esconder reservados.
  - **(c)** Rota no app Fluxoly (Flask+React) com tabela de reservas — contradiz D-2, mas é o "jeito
    certo" se a ferramenta crescer.
  - *Proposta: (a) se confirmado; senão (b).*

  **⚠️ Verificação pendente — (a) não confirmável pelos documentos.** O `.xls` enviado tem só 4 valores
  de `Disponibilidade` (`Disponível para venda`, `Laboratório`, `ANALISE`, `DISPONIVEL COM DETALHE`) —
  **nenhum "Reservado"** nas 584 linhas. A doc pública da API nova (`/api/v1/catalog/availability`) não
  enumera os valores sem o token, e a API nova **não tem endpoint de escrita** em inventory (só `GET` e
  `POST` de criação) — ou seja, mesmo que o status exista, o Fluxoly **não conseguiria setá-lo via API
  nova**; só o organizador, na tela do MercadoPhone. **Ação p/ o CTO:** abrir o MercadoPhone e conferir
  (1) existe status/situação "Reservado" para uma unidade de estoque? (2) ao marcar, o item some do
  export `.xls`? — **CTO conferiu (2026-09-03): a lista do MercadoPhone só tem os 4 status, não há
  "Reservado".** → opção (b).
</details>

- **QA-24 — RESOLVIDA:** reserva **não expira** automaticamente. Sai quando o organizador tira ou o
  aparelho é vendido.
- **QA-25 — RESOLVIDA:** a reserva guarda só **vendedor + data**. Nunca nome/dado do cliente.

### Fonte e atualização

- **QA-26 — RESOLVIDA:** caminho principal = **API nova** (token fornecido). `.xls` só como fallback.
- **QA-27 — N/A** (não há upload manual no fluxo normal).
- **QA-28 — RESOLVIDA:** snapshot regenera **a cada 20 min** (automático).
- **QA-40 — RESOLVIDA:** o registro do aparelho já traz `gbDescricao` ("128GB"). Fallback:
  `catalog/storage-sizes` → campo `size`. Não precisa do `.xls`.
- **QA-39 — RESOLVIDA:** AirPods / Apple Pencil **não entram**. Só iPhone / iPad / MacBook / Apple Watch.

### Preço e conteúdo

- **QA-29 — RESOLVIDA:** **um preço** (`valorVenda`). `valorVenda2/3`, `valorPrazo`, `parcelas` vêm
  nulos na API — não há "à vista/parcelado" para exibir.
- **QA-30 — RESOLVIDA (default aceito):** `DISPONIVEL COM DETALHE` **aparece na Geral** com etiqueta
  "com detalhe". `Laboratório`/`ANALISE` ficam de fora.
- **QA-31 — RESOLVIDA (default aceito):** rótulos de estado `Lacrado` / `Seminovo` / `Seminovo (com
  detalhe)` / `CPO`.
- **QA-32 — RESOLVIDA (default aceito):** Geral = ID · Modelo · Armazenam. · Cor · Estado · Preço.
  Estoque = + Custo · Margem · Dias em estoque. `Fornecedor` fica fora das duas telas.
- **QA-33 — RESOLVIDA (default aceito):** unidade sem IMEI real → ID visível = `Cód.` do MercadoPhone.

### Página

- **QA-13 — RESOLVIDA:** header com a marca **IR Phones**.
- **QA-34 — RESOLVIDA:** `estoque.fluxoly.com`, deploy Vercel (+ Render se o backend de reservas exigir).
- **QA-35 — RESOLVIDA:** botão "baixar Excel" **nas duas áreas**.
- **QA-36 — RESOLVIDA:** pt-BR / R$ fixo.
- **QA-41 — RESOLVIDA:** exibir `saudeBateria` (%) na Geral para iPhone / Apple Watch / MacBook quando
  o valor existir.

### Registro

- **QA-37 — RESOLVIDA:** sem dado de cliente em nenhuma área (ver §4.3 — `clienteNome`/`fornecedorNome`
  são PII e ficam de fora dos dois snapshots; snapshot montado por allowlist de campos).
- **QA-38 — RESOLVIDA:** reuso da *estrutura* da tabela da Skyline aceito como decisão consciente — a
  identidade visual (IR Phones / tokens Fluxoly) torna o resultado distinto; concorrente não tem acesso
  à ferramenta (interna, com senha).
- **QA-42 (nova) — Token do MercadoPhone.** Foi colado no chat em texto puro. Deve entrar **só** como
  secret na Vercel/Render/GitHub Actions, **nunca** no repositório. Recomendação: **rotacionar** o
  token no painel do MercadoPhone depois que o setup estiver pronto (precedente:
  `project_pending_gemini_key_rotation`). O token dá leitura de todo o inventário (custo, fornecedor,
  `clienteId`, saúde de bateria) — não há endpoint de escrita, então o risco de vazamento é exposição
  de leitura, mas ainda assim rotacionar.

---

## 6. Regras de negócio candidatas (BR-070+)

| Candidata | Enunciado |
|---|---|
| BR-070? | A área **Geral** expõe modelo, armazenamento, cor, estado, saúde de bateria, preço de venda e disponibilidade. **Nunca** custo, margem, fornecedor, nome de cliente, IMEI completo, campos fiscais ou texto livre. Snapshot montado por **allowlist** de campos. |
| BR-071? | A área **Estoque** acrescenta custo, margem e dias em estoque, e é a única que pode registrar reservas. Também **não** expõe nome de cliente/fornecedor (PII). |
| BR-072? | Unidades de fontes diferentes (API / `.xls` de fallback) são deduplicadas por IMEI completo; sem IMEI real, pelo `id`/`Cód.` do MercadoPhone. |
| BR-073? | Identificador visível de uma unidade = últimos 4 dígitos do IMEI, +1 dígito por vez apenas nas unidades cujo identificador colidiria com outra exibida. |
| BR-074? | Só entram aparelhos com `snAcessorio == 0` e `tipoProdutoId ∈ {IPHONE, IPAD, MACBOOK, APPLE WATCH}` (+AirPods/Pencil se QA-39). Acessórios, peças, serviços e brindes nunca entram. |
| BR-075? | Só aparecem unidades cuja situação tem `snExibirPdv == 1` (`Disponível para venda`, `DISPONIVEL COM DETALHE`). `Laboratório`/`ANALISE` ficam de fora. `DISPONIVEL COM DETALHE` recebe etiqueta "com detalhe". |
| BR-076? | Unidade reservada (na área Estoque) sai da Geral e aparece só na lista "Reservados". A reserva não expira: sai por ação do organizador ou quando a unidade some do estoque do MercadoPhone (venda). |
| BR-077? | A reserva registra vendedor + data, **nunca** dado do cliente. |
| BR-078? | O MercadoPhone não tem status "Reservado"; a reserva é um registro exclusivo desta ferramenta e não é escrito de volta no MercadoPhone. |

---

## 7. Esforço (P/M/G)

| Bloco | Esforço |
|---|---|
| UI (tabela, filtros, busca, agrupamento por modelo, 2 áreas, tela de bloqueio, export) | **M** |
| Ingestão API MercadoPhone (paginação + 4 lookups + normalização) | **M** |
| Estado de reservas — armazenamento leve próprio + ação reservar/desreservar | **M** |
| Dedup IMEI + geração dos 2 snapshots (Geral sem custo / Estoque com custo) | **M** |
| Deploy Vercel + 2 senhas + cron de sync | **P–M** |
| Ciclo ADR-010 completo (>3 arquivos → Revisão Arquitetural obrigatória; reserva pode puxar ADR curto) | **M** |

Total: **G**.

---

## 8. Estado do gate

✅ **APROVADA pelo CTO em 2026-09-03.** Todas as QA fechadas (QA-1 a QA-42). D-1..D-11 confirmados.
BR-070..BR-078 rascunhadas — a redação final entra em `BUSINESS_RULES.md` no Encerramento.

**Pendências operacionais (não bloqueiam o Plano):**
- As duas senhas (Geral / Estoque) — o CTO define no deploy.
- Rotacionar o token do MercadoPhone depois do setup (QA-42).

**Próxima etapa:** Plano Técnico → `docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md`.
Decide: mecanismo de armazenamento da reserva (pode puxar ADR curto), estrutura de build/deploy,
allowlist de campos dos 2 snapshots, agrupamento visual, testes. **Gate do CTO no Plano antes de
qualquer código.**

---

## Documentos relacionados

- `docs/engineering/adr/ADR-010.md` — o ciclo desta feature
- `docs/product/BUSINESS_RULES.md` — onde BR-070+ entram
- `docs/company/BRAND_IDENTITY.md` §10 — identidade Pulse
- `fluxoly_mercadophone.py` · `docs/operations/INCIDENTS/INC-003-*` — integração MercadoPhone atual (só OS, API legada)
- `project_pending_gemini_key_rotation` (memória) — precedente de segredo colado em texto puro
- Referência externa: `https://tabelaprecos.gruposkytech.com/lista-precos.html`
- API: `https://platform.mercadophone.tech/` (`/llms-full.txt`, `/openapi.json`)
- Arquivo de amostra analisado: `6a9a024f69a8d.xls` (export MercadoPhone, 584 linhas, 2026-09-03)
