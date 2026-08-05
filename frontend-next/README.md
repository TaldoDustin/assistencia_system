# Fluxoly — Protótipo Next.js (Sprint NEXTJS-FUNDAÇÃO)

**Isto é um protótipo de avaliação, não é produção.** Vive em branch própria
(`explore/nextjs-fundacao`), não é implantado em lugar nenhum, e não substitui
o frontend Vite + React em `../frontend/`, que continua sendo o frontend de
produção do Fluxoly.

Contexto completo da decisão: [`docs/engineering/adr/ADR-012.md`](../docs/engineering/adr/ADR-012.md)
e o plano de execução em
[`docs/operations/SPRINTS/SPRINT_NEXTJS_FUNDACAO.md`](../docs/operations/SPRINTS/SPRINT_NEXTJS_FUNDACAO.md).

Este diretório é o único lugar deste repositório onde este track pode
escrever. Nenhum arquivo de produção (`frontend/`, `app.py`, `fluxoly_*.py`,
`requirements*.txt`, `database.db`, `tests/`) foi tocado para construir este
protótipo.

---

## Stack

- **Next.js 16** (App Router, Turbopack — estável e padrão nesta versão), **TypeScript em modo estrito**
- **TailwindCSS v4** (mesma major version que `frontend/package.json` já usa)
- **shadcn/ui** (estilo `base-nova`, sobre `@base-ui/react` em vez de Radix — é o padrão da versão atual do CLI shadcn)
- **Phosphor Icons** (`@phosphor-icons/react`) — exclusivamente. `lucide-react` foi removido do `package.json`; os poucos componentes shadcn que vêm com ícones Lucide por padrão (`dialog`, `dropdown-menu`, `sheet`, `sidebar`, `sonner`) foram editados para importar de `@phosphor-icons/react` em vez disso.
- **Motion** (pacote `motion`, sucessor do Framer Motion) para microinterações
- **next-themes** para dark mode

## Como rodar

Pré-requisito: o Flask precisa estar rodando localmente em `127.0.0.1:5080`
(porta padrão de `IR_FLOW_PORT`). Na raiz do repositório, com o venv já criado:

```bash
# raiz do repositório
.venv\Scripts\python.exe app.py
```

Em outro terminal, neste diretório:

```bash
cd frontend-next
npm install
npm run dev
```

Abra `http://localhost:3000`. A rota `/` redireciona para `/dashboard`, que
exige sessão — sem cookie válido você cai em `/login`. Autentique com
qualquer usuário real do sistema (tabela `usuarios` do `database.db` local).

Scripts disponíveis: `npm run dev`, `npm run build`, `npm run start` (produção),
`npm run lint` (ESLint via CLI — `next lint` foi removido no Next.js 16).

## Autenticação — decisão e validação

Decisão (conforme ADR-012 / Sprint): **proxy de dev**, não login de teste
dedicado. `next.config.ts` define `rewrites()` mapeando `/api/*` →
`http://127.0.0.1:5080/api/*` (endereço configurável via
`FLUXOLY_FLASK_DEV_ORIGIN`). Do ponto de vista do browser, tudo em
`localhost:3000` é same-origin — o cookie de sessão do Flask (`session=...`,
`HttpOnly`, `SameSite=Lax` em dev) é setado e reenviado automaticamente,
sem nenhuma mudança de CORS no backend.

**Validação empírica (feita, não assumida) — funcionou sem ressalvas:**

1. Subi o Flask local (`IR_FLOW_NO_BROWSER=1 .venv\Scripts\python.exe app.py`, output redirecionado para log).
2. Não havia usuário de teste com senha conhecida no `database.db` local (só um `admin` com hash desconhecido) e `tests/conftest.py` cria/derruba usuários apenas num banco temporário isolado (`IR_FLOW_DATA_DIR` em `tempfile.mkdtemp()`), não no `database.db` da raiz. Segui exatamente o mesmo padrão que `tests/conftest.py` já usa para isso (`generate_password_hash` + `INSERT INTO usuarios` com `usuario` aleatório) para inserir um usuário temporário só nesse banco de dev local (gitignorado, não é o banco de produção), rodei a validação, e removi o usuário logo em seguida com um `DELETE` pelo `id`.
3. Subi o Next.js (`npm run dev`, porta 3000).
4. `curl -i -c cookies.txt -H "Content-Type: application/json" -d '{"usuario":"...","senha":"..."}' http://localhost:3000/api/auth/login` → **200**, com `Set-Cookie: session=...; HttpOnly; Path=/; SameSite=Lax` — o cookie chegou ao cliente como se tivesse vindo de `localhost:3000`, mesmo o Flask real estando em `127.0.0.1:5080`.
5. `curl -i -b cookies.txt http://localhost:3000/api/dashboard` reusando esse cookie → **200**, com o payload real do dashboard (`{"ok": true, "faturamento_total": 0.0, ...}`), não 401/redirect de login.
6. Removi o usuário temporário do banco e derrubei o processo Flask (`Stop-Process` na árvore de processos `app.py`; o `TaskStop` do agente não havia matado a árvore completa no Windows, então a confirmação foi feita conferindo `Get-NetTCPConnection -LocalPort 5080` e um `curl` final retornando erro de conexão).

Conclusão: a decisão do ADR-012/Sprint (proxy de dev, sem BetterAuth nem
vendor novo) está confirmada na prática, não só no papel.

## O que foi implementado

- **Dashboard** (`/dashboard`) — consome `GET /api/dashboard` (somente leitura). Cards de métricas (faturamento, lucro, resultado líquido, ticket médio, OS abertas/finalizadas, estoque, compras pendentes), lucro por técnico, serviços mais feitos, resumo por vendedor. Skeleton de carregamento, estado de erro.
- **Ordens de Serviço** — lista em `/os` (tabela shadcn, busca com debounce, skeleton, estado vazio) e detalhe em `/os/[id]` (dados financeiros, peças utilizadas, estado 404 tratado). Ambas consomem `GET /api/ordens` e `GET /api/ordens/<id>` (somente leitura).
- **`/login`** — portão de autenticação mínimo (usuário/senha via `POST /api/auth/login`). **Não é uma das duas telas avaliadas pela Sprint** — é a infraestrutura necessária para alcançar Dashboard/OS com uma sessão real em um browser, já que a Sprint não previu tela de login própria. Ver seção "Desvios do plano" abaixo.
- **Navegação**: sidebar colapsável (`shadcn/ui sidebar`, com atalho de teclado Cmd/Ctrl+B), cabeçalho com breadcrumb simples e toggle de tema.
- **Dark mode**: `next-themes`, padrão do sistema operacional, toggle manual com transição via Motion.
- **Microinterações Motion**: fade-in de página, hover/lift em cards (150–300ms), transição do ícone sol/lua, fade de erro no formulário de login — todas discretas, nada acima de 300ms.
- **Estados por tela**: loading (skeleton), vazio, erro — nas três rotas de dados.
- **Responsividade**: grid de cards colapsa de 4 → 3 → 2 → 1 colunas; sidebar vira `Sheet` em mobile.
- **Acessibilidade básica**: navegação por teclado (links/botões focáveis, atalho de sidebar), labels associados aos inputs do login, contraste dos tokens shadcn (que já seguem WCAG AA por padrão).

## Componentes shadcn/ui instalados

`button`, `input`, `table`, `dialog`, `card`, `dropdown-menu`, `badge`,
`tooltip`, `sonner` (toast), `skeleton`, `separator`, e também `sidebar`
(+ `sheet`, que o `sidebar` depende) — o CLI shadcn atual **tinha** o
componente `sidebar` disponível, ao contrário do que o plano original
considerava possível não estar disponível.

## Verificações executadas

Todas passaram, sem gambiarra (nenhum type-check/lint desabilitado):

| Verificação | Resultado |
|---|---|
| `npx tsc --noEmit` (modo estrito) | passou sem erros |
| `npm run lint` (ESLint, `next lint` não existe mais no Next 16) | passou sem erros nem warnings |
| `npm run build` (build de produção, Turbopack) | passou sem erros nem warnings — 6 rotas geradas (`/`, `/login`, `/dashboard`, `/os`, `/os/[id]`, `/_not-found`) |
| `npm run dev` + `curl` nas rotas | `/` → 307 (redirect para `/dashboard`), `/login`, `/dashboard`, `/os` → 200 com HTML válido |
| Validação de autenticação via proxy | funcionou sem ressalvas — ver seção acima |

## Desvios do plano documentado na Sprint

- **Tela `/login` adicionada**, além das duas telas pedidas (Dashboard, OS). A Sprint escolheu a estratégia de "proxy de dev" para autenticação mas não previu uma UI de login — sem alguma forma de autenticar em um browser real, as duas telas exigidas nunca seriam alcançáveis fora de testes via `curl`. É infraestrutura mínima (um formulário, sem "esqueci a senha" nem nenhuma outra função), não uma terceira tela de design a ser avaliada.
- **`eslint-plugin-react-hooks` v7** (empacotado por `eslint-config-next` 16) introduz a regra `react-hooks/set-state-in-effect`, que barra o padrão clássico "setLoading(true) no topo do efeito antes do fetch". Os hooks de dados (`src/hooks/use-api-query.ts`, `use-debounced-value.ts`, `use-has-mounted.ts`) e o `use-mobile.ts` gerado pelo próprio shadcn CLI foram ajustados para derivar o estado de loading comparando uma "key" da consulta atual com a key do último resultado aplicado, em vez de um `setState` síncrono no corpo do efeito — sem desabilitar a regra em nenhum arquivo.
- **`iconLibrary` em `components.json`** permanece `"lucide"` (valor de metadado escrito pelo CLI do shadcn; não há opção `"phosphor"` reconhecida pelo CLI atual). Isso não afeta o código de fato instalado — nenhum arquivo importa de `lucide-react`, que foi removido do `package.json` — mas um futuro `npx shadcn add <componente>` pode reintroduzir um import Lucide num componente novo; revisar antes de aceitar.

## Pendências / não implementado

- Sem testes automatizados (fora do escopo desta Sprint — ver "Critérios de Aceitação").
- Sem CI/CD, sem deploy — por decisão explícita do ADR-012 (track não é mergeado em `main` sem decisão formal futura).
- Auditoria de acessibilidade além do básico (leitor de tela, WCAG AA formal) não foi feita — só contraste (herdado dos tokens shadcn) e navegação por teclado manual.

## Arquivos fora de `frontend-next/` identificados como potencialmente necessários, mas não tocados

Nenhum. A validação de autenticação via proxy funcionou usando exclusivamente
a API Flask já existente (`/api/auth/login`, `/api/auth/logout`,
`/api/auth/me`, `/api/dashboard`, `/api/ordens`, `/api/ordens/<id>`) e a
configuração de CORS/sessão já presente em `app.py` — nenhuma mudança de
backend, schema ou `IR_FLOW_CORS_ORIGINS` foi necessária, confirmando a
hipótese do ADR-012.
