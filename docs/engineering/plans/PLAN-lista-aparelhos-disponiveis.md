# PLAN-lista-aparelhos-disponiveis — Lista de Aparelhos Disponíveis (ferramenta interna IR Phones)

**Data:** 2026-09-03
**Feature:** `docs/product/research/DISCOVERY_LISTA_PRECOS_PUBLICA.md` (aprovada 2026-09-03) — BR-070 a BR-078 (a formalizar em `docs/product/BUSINESS_RULES.md` no Encerramento)
**Arquitetura:** `docs/engineering/adr/ADR-013.md`
**Status:** ENCERRADO (2026-09-04) — mergeado em `main` via PR #68 (`eb13e836`)

> Documento efêmero (ADR-010). Vira histórico da decisão de implementação depois do Encerramento.

**Estado**

- [x] Discovery — aprovada (BR-070 a BR-078)
- [x] ADR-013 — aprovado pelo CTO (2026-09-03)
- [x] Plano Técnico — aprovado pelo CTO (2026-09-03)
- [x] Implementação — branch `feat/lista-aparelhos-disponiveis` (2026-09-03)
- [x] Testes — 77/77 vitest + typecheck; verificado ponta a ponta contra a API viva (583→212, 0 vazamento)
- [x] QA Manual — aprovado no deploy `estoque-gamma-nine.vercel.app` (Vercel Hobby + Upstash). Corrigidos durante: tela de bloqueio não sumia (`.lock{display:flex}` vencia `[hidden]`); ordenação natural de modelo + campo "Detalhes" editável + badge "Parado" (pedidos do CTO — ver §"Ajustes pós-QA")
- [x] Revisão Arquitetural — `/code-review high` 2026-09-04. Propriedade central OK (custo/PII nunca alcançam a Geral; auth centralizada; cookie não-forjável). 8 achados, **todos corrigidos** — ver §"Revisão Arquitetural" abaixo.
- [x] Encerramento — BR-070..080 em `BUSINESS_RULES.md`, CHANGELOG, PROJECT_STATUS (2026-09-04). Pendências operacionais pós-merge listadas no PROJECT_STATUS.

---

## Objetivo

Implementar o app standalone descrito no ADR-013: duas áreas (Geral / Estoque) atrás de senha, sobre um
snapshot do inventário do MercadoPhone regenerado a cada ~20 min, com reserva de unidade como
sobreposição própria. Não repete as regras — ver Discovery / BR-070..078.

---

## Escopo

1. Estrutura do app em `apps/lista-aparelhos-disponiveis/` (novo diretório no repo).
2. Job de sincronização MercadoPhone → 2 snapshots no Redis gerenciado (Upstash).
3. Camada serverless: sessão (2 senhas), entrega de dados por papel, reservar/desreservar.
4. Página única com tela de bloqueio + tabela agrupada (Geral e Estoque são a mesma página, conteúdo
   por papel).
5. Deploy: projeto Vercel `estoque-fluxoly`, domínio `estoque.fluxoly.com`, Redis gerenciado (Upstash), cron.
6. Testes automatizados do job e da camada serverless.
7. Ajuste de CI para lintar/testar o novo diretório.

## Fora de escopo

- Login individual / auditoria de quem reservou (ADR-013, condições de revisão).
- Escrita de volta no MercadoPhone.
- Ingestão do `.xls` (fica documentada como fallback manual, sem código nesta entrega).
- Qualquer alteração em `app.py`, `database.db`, projetos Render/Vercel do Fluxoly.
- Acessórios, peças, serviços, AirPods, Apple Pencil (BR-074).

---

## Impacto no banco

**Nenhum.** Não há SQLite. O estado persistente é o Redis gerenciado (Upstash):

| Chave KV | Tipo | Conteúdo |
|---|---|---|
| `snapshot:geral` | string (JSON) | `{ geradoEm, itens: [...] }` — allowlist Geral |
| `snapshot:estoque` | string (JSON) | `{ geradoEm, itens: [...] }` — allowlist Estoque (+ custo/margem/dias) |
| `reservas` | hash | `imei → { vendedor, reservadoEm }` |
| `sync:last` | string | ISO timestamp + resultado do último job (para healthcheck) |

`reservas` é a única escrita feita por usuário; os `snapshot:*` só pelo job.

---

## Impacto no backend (serverless, `apps/lista-aparelhos-disponiveis/api/`)

Runtime: funções JS/TS na Vercel (ADR-013 Q5). Camadas: cada rota é fina; a lógica de
filtro/dedup/allowlist vive em `lib/` e é compartilhada com o job e testada isolada.

| Rota | Método | Papel | O que faz |
|---|---|---|---|
| `/api/session` | POST | — | body `{ senha }`; compara (constant-time) com `SENHA_GERAL`/`SENHA_ESTOQUE`; set-cookie `sess` assinado HMAC (`{role, iat}`), `HttpOnly`, `Secure`, `SameSite=Lax`, ~12 h. Rate-limit por IP no KV. |
| `/api/session` | DELETE | — | limpa o cookie |
| `/api/inventory` | GET | geral/estoque | lê `snapshot:<role>` do KV; para `estoque`, funde `reservas` (marca reservados); para `geral`, **remove** os reservados. Devolve JSON. |
| `/api/reservar` | POST | **estoque** | body `{ imei, vendedor }`; grava em `reservas`; 409 se já reservado |
| `/api/desreservar` | POST | **estoque** | body `{ imei }`; remove de `reservas` |
| `/api/sync` | POST | — (segredo) | header `x-sync-secret: $SYNC_SECRET`; roda o job; idempotente |
| `/api/health` | GET | — | idade do último snapshot + contagem de itens/reservas (sem dado sensível) |

**Gate de acesso:** feito na camada de API, não em edge middleware. A página (`index.html`/`app.js`/
`styles.css`/`xlsx.js`) é 100% estática e sem dado sensível — sempre carrega e mostra a tela de
bloqueio. `/api/inventory|reservar|desreservar` exigem cookie `sess` válido; `role=geral` recebe 403
em `reservar`/`desreservar`. (Edge middleware exigiria reimplementar o HMAC em Web Crypto sem ganho
real de segurança, já que nenhum asset estático carrega dado protegido.)

### Job de sync (`lib/build-snapshot.ts`, chamado por `/api/sync` e pelo cron)

1. Pagina `GET https://platform.mercadophone.tech/api/v1/inventory?limit=300&page=N` (header
   `X-API-Key: $MERCADOPHONE_API_KEY`) até esgotar (`total`).
2. **Filtro de inclusão** (BR-074): `snAcessorio === 0` **e** `tipoProdutoId ∈ {3719, 4959, 4960, 4961}`
   (IPHONE/MACBOOK/APPLE WATCH/IPAD).
3. **Filtro de disponibilidade** (BR-075): manter só situações com `snExibirPdv === 1` — hoje
   `produtoDisponibilidadeId ∈ {1, 62177}`. Resolver via `GET /api/v1/catalog/availability` no início
   do job (não hardcodar os ids).
4. **Dedup** (BR-072): por `imei`; sem `imei` real (`null`/`0`), por `id`. Se dois registros com o mesmo
   IMEI, vence o de `dataModificacao` mais recente.
5. **Identificador curto** (BR-073): base = últimos 4 dígitos do `imei`. Calcular o menor comprimento
   `L ≥ 4` tal que, **para cada grupo de colisão**, os sufixos de comprimento `L` fiquem únicos —
   estendendo **só os itens em colisão** (os demais ficam com 4). Sem IMEI → mostrar o `id` prefixado
   (`#<id>`).
6. **Campos** — montar por **allowlist** (nunca blocklist):
   - **Geral:** `idCurto, tipoProduto, modelo (aparelhoDescricao), armazenamento (gbDescricao || lookup storage-sizes.size), cor (corDescricao), estado (estadoProdutoDescricao → rótulo), saudeBateria, comDetalhe (bool: produtoDisponibilidadeId===62177), precoVenda (valorVenda), dataEntrada`
   - **Estoque:** os de Geral **+** `custo (valorCusto), margem (valorVenda - valorCusto), margemPct, diasEmEstoque (hoje - dataEntrada)`
   - **Nunca:** `valorCusto` (no Geral), `fornecedorNome/Id`, `clienteNome/Id`, `obs`, `observacaoCatalogo`, `ncm/cfop*/cst/cest/codEan`, `serialNumber`, `imei`/`imei2` completos.
7. Rótulos de estado (BR-070/QA-31): `LACRADO→"Lacrado"`, `SEMINOVO→"Seminovo"`, `SEMINOVO`+comDetalhe→`"Seminovo (com detalhe)"`, `OPEN BOX→"Open box"`, `NOVO→"Novo"`, `CPO→"CPO"`.
8. Ordenar por `modelo`, depois `estado`, depois `precoVenda`.
9. `SET snapshot:geral`, `SET snapshot:estoque`, `SET sync:last`.

Timeout defensivo por request (~30 s), retry com backoff (mesma lógica de `fetchWebhook` em
`skyline-precos.js` / do script de comissão). Se a API falhar, **não** sobrescrever o snapshot anterior
— só registrar erro em `sync:last`.

---

## Impacto no frontend (`apps/lista-aparelhos-disponiveis/public/` + `index.html`)

Página única, HTML/CSS/JS puro (ADR-013 Q5), estrutura de UI reaproveitada da referência Skyline
(tabela filtrável, busca, KPIs, header sticky, export `.xlsx` sem lib), identidade **IR Phones** +
tokens Fluxoly.

- **Tela de bloqueio:** campo de senha estilo "desbloquear celular", POST `/api/session`, sem revelar
  qual senha (Geral vs Estoque) foi digitada além do resultado.
- **Após entrar:** `GET /api/inventory`. A página adapta as colunas ao `role` devolvido.
  - Geral: `ID · Modelo · Armazenam. · Cor · Estado · Bateria · Preço`
  - Estoque: `+ Custo · Margem · Dias` e, por linha, botão **Reservar**; aba/again "Reservados" lista o
    `reservas` com botão **Liberar**.
- **Agrupamento** (D-7/BR): cabeçalho de grupo por `modelo + estado`, com contagem e faixa de preço;
  grupos colapsáveis. Busca textual + filtros `Modelo`, `Estado`, `Armazenamento`.
- **Bateria:** badge (verde ≥85, âmbar 80–84, vermelho <80) — só quando `saudeBateria != null`.
- **Export `.xlsx`** (QA-35): o gerador sem-lib da Skyline (`makeXlsxBlob`), nas duas áreas, exportando
  as colunas visíveis do papel atual.
- **Auto-refresh:** re-`GET /api/inventory` a cada 5 min e ao voltar o foco da aba (padrão
  `SkylineVersion`); banner "atualizado há X min" a partir de `geradoEm`.
- pt-BR / `Intl.NumberFormat('pt-BR', {currency:'BRL'})` fixo (QA-36).

`client.js` do Fluxoly **não** é tocado (app separado).

---

## Estratégia de migração / deploy

Sem migração de schema. Sequência de provisionamento (ADR-013 DoD):

1. Criar projeto Vercel `estoque-fluxoly` a partir de `apps/lista-aparelhos-disponiveis/` (root
   directory do projeto).
2. Provisionar Redis gerenciado (Upstash), vincular só a esse projeto.
3. Env vars no projeto Vercel: `MERCADOPHONE_API_KEY`, `SENHA_GERAL`, `SENHA_ESTOQUE`,
   `COOKIE_SIGNING_SECRET`, `SYNC_SECRET` (+ as do KV, automáticas).
4. Cadência do sync: conta Vercel é **Hobby** → `.github/workflows/estoque-sync.yml` (`schedule */20`,
   `curl` com `Authorization: Bearer $SYNC_SECRET`). Precisa da var de repo `ESTOQUE_SYNC_URL` + secret
   `ESTOQUE_SYNC_SECRET`. `vercel.json` mantém um cron diário só como rede de segurança.
5. Rodar `/api/sync` uma vez à mão, conferir `snapshot:*` e `/api/health`.
6. Apontar `estoque.fluxoly.com` (CNAME) para o projeto.
7. Primeiro acesso real das duas senhas.
8. **Rotacionar `MERCADOPHONE_API_KEY`** no MercadoPhone (QA-42).

---

## Testes

`apps/lista-aparelhos-disponiveis/` com seu próprio runner (Vitest). Fixtures = respostas reais
capturadas da API (anonimizadas quanto a `clienteNome`/`fornecedorNome`).

| Módulo | Cobre |
|---|---|
| `lib/filter.test` | inclui iPhone/iPad/MacBook/Watch; exclui acessório (`snAcessorio=1`), TAXA DE ENTREGA, JBL, AirPods; exclui `Laboratório`/`ANALISE`; mantém `com detalhe` |
| `lib/dedup.test` | mesmo IMEI 2× → 1 (vence `dataModificacao`); sem IMEI → chave `id` |
| `lib/short-id.test` | 4 dígitos quando único; **só** os colididos vão a 5/6; estabilidade dado o mesmo conjunto; sem IMEI → `#id` |
| `lib/allowlist.test` | **`snapshot:geral` nunca contém** `valorCusto`, `fornecedorNome`, `clienteNome`, `obs`, campos fiscais, `imei` completo (teste de propriedade sobre fixture inteira); `snapshot:estoque` não contém `clienteNome`/`fornecedorNome` |
| `lib/labels.test` | mapa de estado + "(com detalhe)"; margem/margemPct |
| `api/session.test` | senha certa → cookie com papel certo; senha errada → 401; rate-limit; `role=geral` → 403 em `reservar` |
| `api/inventory.test` | papel geral não recebe reservados nem custo; papel estoque recebe ambos |
| `api/reservar.test` | reserva grava; 2ª reserva do mesmo IMEI → 409; desreservar remove |
| `build-snapshot.test` | API falhando → snapshot anterior preservado, erro em `sync:last` |

Sem Playwright nesta entrega (mesma linha do resto do projeto; QA manual cobre o fluxo visual).

---

## Critérios de aceite

1. Sem cookie válido, nenhuma rota além de `/api/session` e da tela de bloqueio responde com dados.
2. `GET /api/inventory` com `role=geral`: resposta **não contém** custo, margem, fornecedor, cliente,
   IMEI completo, nem itens reservados (verificado por teste sobre a fixture inteira).
3. `GET /api/inventory` com `role=estoque`: contém custo/margem/dias e a marcação de reservado.
4. `POST /api/reservar` só funciona com `role=estoque`; item reservado some da Geral no próximo
   `GET /api/inventory`.
5. Filtro de inclusão/disponibilidade bate com BR-074/075 sobre dados reais (contagem conferida
   manualmente uma vez contra o painel do MercadoPhone).
6. Identificador curto: único na lista exibida; só os colididos passam de 4 dígitos.
7. Job grava os 2 snapshots; falha de API não zera a lista.
8. `estoque.fluxoly.com` no ar, isolado — nenhuma env var/binding compartilhado com Fluxoly/Demo
   (checado na Revisão Arquitetural).
9. Suíte do novo diretório verde no CI; lint 0 erro.
10. Token do MercadoPhone rotacionado após o deploy.

---

## Riscos

| Risco | Mitigação |
|---|---|
| Campo de preço/condição da API muda de nome ou vem nulo | `allowlist.test` sobre fixture real; job registra item sem `valorVenda` como "sob consulta" em vez de quebrar; alerta em `sync:last` se >X% sem preço |
| `snExibirPdv`/ids de disponibilidade mudam no MercadoPhone | job resolve via `catalog/availability` a cada execução, não hardcoda |
| Token exposto no chat | rota-lo após deploy (critério 10); só como secret; sem endpoint de escrita na API reduz o dano |
| Redis gerenciado (Upstash) indisponível | `/api/inventory` serve o último snapshot em cache de módulo; `/api/health` acusa; reservas ficam somente-leitura |
| Senha compartilhada vaza para fora da loja | ferramenta interna, sem dado de cliente; trocar a senha é 1 env var + redeploy; sem custo exposto no papel Geral |
| Plano Vercel não permite cron sub-diário | fallback GitHub Actions já previsto no deploy |
| `.xlsx` export com muitos itens trava o browser | mesmo gerador da Skyline já roda com ~300 linhas; limitar export ao filtro atual |
| Someone screenshots IMEI-suffix + preço e repassa a concorrente | sufixo não identifica aparelho fora da loja; sem custo; risco aceito na Discovery (QA-38) |

---

## Rollback

- App isolado: **despublicar o projeto Vercel** `estoque-fluxoly` remove a ferramenta inteira, zero
  efeito em produção.
- Reverter o diretório `apps/lista-aparelhos-disponiveis/` no repo.
- Remover o workflow de cron (se usado) e revogar o `MERCADOPHONE_API_KEY`.
- Nada a migrar de volta — KV é descartável.

---

## Questões em aberto

Nenhuma questão de **negócio** pendente — a Discovery fechou BR-070..078 e as QA-1..42. Se a
implementação revelar uma regra não decidida, este plano **pausa** e volta para a Discovery (ADR-010).

Pendências **operacionais** (não de negócio, não bloqueiam a aprovação do plano):
- Valores de `SENHA_GERAL` / `SENHA_ESTOQUE` — o CTO define no provisionamento.
- Confirmar o plano da conta Vercel (define cron nativo × GitHub Actions).

---

## Ajustes pós-QA (2026-09-04, pedidos do CTO durante o QA Manual)

Aditivo ao escopo original, aprovado pelo CTO na conversa. Não altera nenhuma BR-070..078;
acrescenta BR-079 e BR-080 (a formalizar no Encerramento).

### A. Ordenação natural da lista (`lib/ordenar.ts`)
Antes: alfabético por `modelo`. Agora: **tipo** (iPhone → iPad → MacBook → Apple Watch) →
**modelo em ordem natural** (`Intl.Collator numeric` — IPHONE 9 < 11 < 11 PRO < 11 PRO MAX < …) →
**estado** (Lacrado/Novo/Open box/CPO antes de Seminovo; "com detalhe" por último) → **preço** crescente.
Como o front agrupa por `modelo + estado` preservando ordem de inserção, os grupos saem na sequência
certa (ex.: "17 PRO MAX Lacrado" imediatamente antes de "17 PRO MAX Seminovo").
**BR-080 (candidata):** a lista é ordenada por tipo → modelo (ordem natural) → estado → preço.

### B. Campo "Detalhes" — nota de condição curada (`api/detalhe.ts`, overlay no Redis)
Texto livre por unidade (≤280 chars), ex.: "marca de uso leve na traseira", "tela trocada — original".
- **Editável só na área Estoque** (`POST /api/detalhe`, role estoque); texto vazio limpa.
- **Visível também na área Geral** (read-only) — decisão explícita do CTO: o vendedor precisa da
  informação para falar com o cliente.
- Guardado no hash `detalhes` do Redis (chave = `id` do MercadoPhone), igual à reserva. `editadoEm`
  registrado; **sem `editadoPor`** (não há login individual — desvio consciente da proposta inicial,
  atribuição não agrega em ferramenta de senha compartilhada).
- **BR-079 (candidata):** a nota de "Detalhes" é conteúdo curado manualmente na área Estoque, exibido
  nas duas áreas. A responsabilidade de não incluir dado pessoal é de quem edita (a ferramenta não
  sanitiza). O MercadoPhone **não** tem campo equivalente aproveitável — o `obs` deles é nota interna
  com PII ("… com o marcelo, celular pagbank"), deliberadamente fora do snapshot.

### Testes acrescentados
`test/ordenar.test.ts` (5), `test/detalhe.test.ts` (5). Suíte: 71/71.

---

## Revisão Arquitetural (2026-09-04)

`/code-review high` sobre a branch inteira. **Propriedade central verificada e sã:** custo, margem,
IMEI completo e PII (nome de cliente/fornecedor) nunca alcançam a área Geral nem o navegador de quem
não é estoque; toda rota de dados passa por `papelDoRequest` (cookie HMAC); não há caminho para forjar
um cookie de estoque sem `COOKIE_SIGNING_SECRET`.

8 achados, nenhum bloqueador de segurança — **todos corrigidos antes do merge** (commit(s) de fix na
branch):

| # | Sev | Achado | Correção |
|---|---|---|---|
| 1 | Alto (op.) | `getStore()` caía em silêncio para `MemoryStore` se o Redis sumisse em produção | `getStore()` lança erro se `process.env.VERCEL` e sem credencial de Redis (falha alto) |
| 2 | Médio | Rate-limit de login contava acertos e era por IP → loja atrás de um NAT se auto-bloqueava | Só falhas contam; senha certa nunca é bloqueada; limite 20/5min |
| 3 | Médio | Paginação do MercadoPhone truncava em silêncio se uma página viesse vazia | Aborta com erro se página vazia antes de esgotar `total` → sync preserva o snapshot anterior |
| 4 | Médio | `/api/sync` aceitava o segredo em `?secret=` (vai pro log da Vercel) | Removido; só header (`Authorization: Bearer` / `x-sync-secret`) |
| 5 | Baixo | `incr`+`expire` do rate-limit não atômicos → chave podia ficar sem TTL | `expire` incondicional (janela deslizante) |
| 6 | Baixo | `cookies.txt` de teste commitado | `git rm` + entrada no `.gitignore` |
| 7 | Baixo | `verificarToken` não validava `exp` numérico | `typeof payload.exp !== "number"` → rejeita |
| 8 | Baixo | `Cache-Control: no-store` só nas respostas 200 | Header `no-store` para `/api/(.*)` no `vercel.json` |

Testes acrescentados: `test/mercadophone.test.ts` (3 — paginação/truncamento), `test/store.test.ts`
(2 — fallback proibido em produção), rate-limit reescrito em `test/api.test.ts`. Suíte: 77/77.
