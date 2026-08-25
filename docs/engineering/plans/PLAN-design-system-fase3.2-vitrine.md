# Fase 3.2 — Vitrine (Login + Shell/Sidebar + Dashboard + harmonização da Landing) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Primeira fatia de composição visual real da Fase 3 (Visual Experience Redesign) — prova de
conceito da direção "hierarquia de superfície" (`PLAN-design-system-fase3-visual-experience.md` §2) antes
de escalar para as 21 telas restantes (Tiers 2-4, §9 do mesmo documento). Aplica os recipientes da
Foundation v2 (`Panel`/`ListBlock`/`LooseMetric`, Fase 3.1) às 4 áreas de maior exposição do produto:
Login (isolado, baixo risco), Shell/Sidebar (toca todas as telas), Dashboard (hierarquia real substituindo
grid uniforme de 8 KPIs + 3 gráficos do mesmo peso), e uma auditoria de harmonização da Landing.

**Por que a Landing recebe tratamento diferente:** a "liberdade criativa total" de 2026-08-20 (§0.1 do
plano mestre) excluiu explicitamente a Landing Page pública do escopo de reinvenção — ela já tem
composição editorial própria (§1, achado 7: "a Landing é o único lugar onde composição editorial já
existe"). O Task 4 deste plano é uma auditoria de consistência (tokens/marca já aplicados corretamente?),
não um redesenho — qualquer achado de composição maior fica fora deste plano.

**Architecture:** Zero mudança de lógica de negócio, API, estado ou handlers em qualquer uma das 3 telas
que recebem composição real (Login/Layout/Dashboard) — só a estrutura JSX de apresentação. Os componentes
da Foundation v2 (`Panel`/`ListBlock`/`LooseMetric`, já testados isoladamente na Fase 3.1, nunca antes
consumidos por uma página real) são aplicados aqui pela primeira vez. Nenhuma classe `dark:` do Tailwind
(mesma regra da Fase 3.0/3.1) — toda diferença visual entre modos vem das custom properties já definidas
em `index.css`.

**Tech Stack:** React 19, Tailwind CSS v4, Vite 8, Vitest 4 + Testing Library (jsdom), Phosphor Icons.

**Spec:** `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` §2 (princípios de
hierarquia), §3/§4 (Light/Dark), §5 (tipografia — número dominante 40-56px), §6 (layout — sidebar agrupada
nos 6 Pilares, header de contexto), §8 (composição proposta do Dashboard), §9 (Tier 1 = esta fase), §12
(linha 3.2). `docs/company/BRAND_IDENTITY.md` §2 (6 Pilares Macrossistêmicos, usados para agrupar o
Sidebar).

## Global Constraints

- Nenhuma mudança de lógica de negócio, payload de API, rota ou regra de permissão em nenhuma das 3
  tarefas de composição — confirmado por diff isolado de handlers/`useEffect`/chamadas de API contra
  `main` antes do commit de cada task (mesmo critério já usado nas Fases 2/3.1).
- `Layout.test.jsx` já faz uma asserção de classe específica (`bg-sidebar-primary` no link ativo) — essa
  classe **não pode mudar de nome** no Task 2, mesmo que a estrutura ao redor dela mude (agrupamento em
  seções). Se a asserção precisar mudar, é porque a implementação divergiu da spec, não o contrário.
- Nenhum token de cor novo é criado — só reaproveitamento dos já calibrados na Fase 3.0
  (`--color-success`/`warning`/`destructive`/`info`) e da paleta categórica de gráfico (Fase 3.1,
  `lib/chart-theme.js`).
- `Panel`/`ListBlock`/`LooseMetric`/`DataTable` (Fase 3.1) são consumidos aqui pela primeira vez — qualquer
  ajuste de API desses componentes que se prove necessário durante a implementação é feito como parte da
  task que os consome (não uma task de infraestrutura separada), documentado no commit.
- Conventional Commits (`feat:`, `fix:`, `docs:`); branch `feat/design-system-fase3.2-vitrine`.
- **Achado incidental a corrigir dentro do Task 2 (não uma task separada):** `Layout.jsx::navItems` tem uma
  entrada duplicada — `{ path: "/compras", label: "Compras", ... }` (linha 24) e
  `{ path: "/compras", label: "Lista de Compras", ... }` (linha 34) apontam para a mesma rota. Como o
  Task 2 já reescreve o array inteiro para agrupar por seção, a duplicata é removida ali (mantém-se
  "Lista de Compras", rótulo mais descritivo) — não é refatoração à parte, é o mesmo array sendo tocado
  pelo mesmo motivo.
- **Decisão de agrupamento do Sidebar (proposta neste plano, sujeita a aprovação):** os 6 Pilares
  Macrossistêmicos (`BRAND_IDENTITY.md` §2) mapeiam nas 18 rotas assim — "Dashboard" fica fora de qualquer
  pilar (visão geral, não uma função de negócio); "Usuários"/"Backups" formam uma seção "Administração"
  fora dos 6 pilares (são operação de sistema, não uma função de negócio da loja):

  | Seção | Rotas |
  |---|---|
  | *(sem seção — topo)* | Dashboard |
  | Vendas | Vendas, Tabelas de Preço |
  | Operação | Estoque, Produtos, Unidades Serializadas, Lista de Compras |
  | Financeiro | Financeiro, Custos Operacionais |
  | Relacionamento | Clientes |
  | Serviços | Ordens de Serviço, Kanban, Garantias, Tipos de Reparo, Tipos de Garantia |
  | Inteligência | Relatórios |
  | Administração | Usuários, Backups |

- **Decisão de hierarquia do Dashboard (proposta neste plano, sujeita a aprovação):** a spec (§8) ilustra
  o princípio com 3 métricas de exemplo, mas o Dashboard real tem 8 KPIs. Mapeamento: **Faturamento** vira
  a métrica dominante (`Panel`, número hero 40-56px — é o número de topo de linha do negócio, mesmo papel
  do exemplo "Faturamento do período" na spec); os outros 7 KPIs (Lucro Bruto, Finalizadas, Em Aberto,
  Peças Pendentes, Urgentes, Ticket Médio, Resultado Líq.) viram uma grade de `LooseMetric` (sem moldura,
  peso secundário) logo abaixo/ao lado; gráfico de Receita continua dominante (2/3), Serviços e Técnicos
  de apoio (1/3 cada, mesma proporção já sugerida na spec); "Resumo Financeiro" (4 linhas) vira `ListBlock`
  em vez de grade de caixas com `bg-secondary` (recipiente de peso secundário, não card-dentro-de-card).

---

### Task 1: `Login.jsx` — hierarquia de superfície

**Files:**
- Modify: `frontend/src/pages/Login.jsx`

**Why this task exists:** Login nunca foi redesenhado de fato (Fase 1 só aplicou tokens/consistência
técnica). Hoje o form já é visualmente isolado (tela cheia, único elemento) mas não segue a regra de
respiro do princípio 4 (§2: "32-48px de respiro puro ao redor do elemento dominante antes de qualquer
outro") nem usa o recipiente `Panel` da Foundation v2 — usa a receita manual antiga
(`bg-card border border-border rounded-xl p-6 shadow-xl`), a mesma que `Panel` foi criado para substituir.

**Nenhuma mudança de lógica** — `handleSubmit`, `useEffect` do toast de erro via query param, e todos os
`useState` permanecem idênticos. Só a árvore JSX de apresentação muda.

- [ ] **Step 1: Criar a branch de feature**

```bash
git checkout main
git pull
git checkout -b feat/design-system-fase3.2-vitrine
```

- [ ] **Step 2: Reescrever a árvore JSX de `Login.jsx`**

Em `frontend/src/pages/Login.jsx`, importar `Panel`/`PanelContent` e substituir o `return` (linhas 44-89
atuais) por:

```jsx
import { Panel, PanelContent } from "@/components/ui/panel";

// ...

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center space-y-3">
          <img
            src="/brand/fluxoly-icon-inverted.svg"
            alt=""
            className="h-12 w-12 rounded-xl mx-auto"
          />
          <div>
            <h1 className="font-wordmark text-2xl text-foreground">Fluxoly</h1>
            <p className="text-muted-foreground text-sm mt-1">Sistema de Assistência Técnica</p>
          </div>
        </div>

        <Panel>
          <PanelContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="usuario">Usuário</Label>
                <Input
                  id="usuario"
                  placeholder="seu.usuario"
                  value={form.usuario}
                  onChange={(e) => setForm((p) => ({ ...p, usuario: e.target.value }))}
                  autoComplete="username"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="senha">Senha</Label>
                <Input
                  id="senha"
                  type="password"
                  placeholder="••••••••"
                  value={form.senha}
                  onChange={(e) => setForm((p) => ({ ...p, senha: e.target.value }))}
                  autoComplete="current-password"
                  required
                />
              </div>
              <Button type="submit" className="w-full" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Entrar
              </Button>
            </form>
          </PanelContent>
        </Panel>
      </div>
    </div>
  );
}
```

Mudanças concretas: `space-y-8` entre bloco de marca e form (era `mb-8` só no bloco de marca — agora o
respiro existe nos dois lados, não só acima); `py-12` na tela inteira garante respiro vertical mínimo em
telas baixas; form migra de `bg-card border border-border rounded-xl p-6 shadow-xl` (receita manual) para
`Panel`/`PanelContent` (mesma combinação borda+sombra, agora nomeada e reutilizável).

- [ ] **Step 3: Rodar o lint e a suite completa**

Run (a partir de `frontend/`): `npm run lint && npm run test`
Expected: PASS — não existe `Login.test.jsx` hoje; nenhum outro teste importa `Login.jsx` diretamente
(confirmado: só `App.test.jsx` referencia a rota `/login` via redirecionamento, sem renderizar o
componente).

- [ ] **Step 4: Checklist manual no browser — Light/Dark**

Run: `npm run dev`, abrir `/login` (rota pública, sem autenticação).

- [ ] Confirmar visualmente em Dark Mode (padrão): form legível, borda/sombra do `Panel` aplicadas,
  respiro visível acima e abaixo do form.
- [ ] Forçar Light Mode (`localStorage.setItem('fluxoly-theme','light')` + reload): confirmar que o
  `Panel` usa sombra como profundidade (não borda pesada), mesmo princípio já validado na Fase 3.0/3.1.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Login.jsx
git commit -m "feat(design-system): Login usa Panel da Foundation v2, respiro real (Fase 3.2)"
```

---

### Task 2: `Layout.jsx` — Sidebar agrupada pelos 6 Pilares

**Files:**
- Modify: `frontend/src/components/Layout.jsx`

**Why this task exists:** os 18 itens do Sidebar hoje são uma lista plana sem hierarquia (§1, achado 3) —
"Dashboard" e "Backups" têm o mesmo peso visual apesar de frequência de uso completamente diferente. A
spec (§6) propõe agrupar pelos 6 Pilares Macrossistêmicos já documentados na marca, conectando produto e
identidade de um jeito que hoje não existe.

**Nenhuma mudança de lógica de permissão** — os filtros `adminOnly`/`perfis` continuam exatamente iguais,
só a estrutura de dados que os carrega muda de array plano para array de seções.

- [ ] **Step 1: Escrever o teste (falhando) de agrupamento**

Adicionar a `frontend/src/components/Layout.test.jsx` (dentro do `describe` existente):

```jsx
  it("agrupa os itens do Sidebar em seções com rótulo (6 Pilares + Administração)", () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    renderLayout();

    expect(screen.getByText("Vendas")).toBeInTheDocument();
    expect(screen.getByText("Operação")).toBeInTheDocument();
    expect(screen.getByText("Financeiro")).toBeInTheDocument();
    expect(screen.getByText("Relacionamento")).toBeInTheDocument();
    expect(screen.getByText("Serviços")).toBeInTheDocument();
    expect(screen.getByText("Inteligência")).toBeInTheDocument();
    expect(screen.getByText("Administração")).toBeInTheDocument();
  });

  it("remove a entrada duplicada de /compras -- só 'Lista de Compras' aparece", () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    renderLayout();

    expect(screen.getByText("Lista de Compras")).toBeInTheDocument();
    expect(screen.queryByText("Compras")).not.toBeInTheDocument();
  });
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `npm run test -- src/components/Layout.test.jsx`
Expected: FAIL — os rótulos de seção ainda não existem, "Compras" ainda aparece duplicado.

- [ ] **Step 3: Reescrever `navItems` e `SidebarNav` em `Layout.jsx`**

Substituir `navItems` (linhas 22-42 atuais) por um array de seções:

```jsx
const navSections = [
  {
    label: null, // sem rótulo -- item de topo, fora de qualquer pilar
    items: [{ path: "/", label: "Dashboard", icon: SquaresFour }],
  },
  {
    label: "Vendas",
    items: [
      { path: "/vendas", label: "Vendas", icon: ShoppingCart, perfis: ["admin", "vendedor"] },
      { path: "/precos", label: "Tabelas de Preço", icon: Tag, adminOnly: true },
    ],
  },
  {
    label: "Operação",
    items: [
      { path: "/estoque", label: "Estoque", icon: Package },
      { path: "/produtos", label: "Produtos", icon: ShoppingBag },
      { path: "/unidades-serializadas", label: "Unidades Serializadas", icon: Barcode },
      { path: "/compras", label: "Lista de Compras", icon: ClipboardText },
    ],
  },
  {
    label: "Financeiro",
    items: [
      { path: "/financeiro", label: "Financeiro", icon: CurrencyDollar, perfis: ["admin", "financeiro"] },
      { path: "/custos", label: "Custos Operacionais", icon: CurrencyDollar, adminOnly: true },
    ],
  },
  {
    label: "Relacionamento",
    items: [{ path: "/clientes", label: "Clientes", icon: UserCircle }],
  },
  {
    label: "Serviços",
    items: [
      { path: "/ordens", label: "Ordens de Serviço", icon: ClipboardText },
      { path: "/kanban", label: "Kanban", icon: Kanban },
      { path: "/garantias", label: "Garantias", icon: Shield },
      { path: "/reparos", label: "Tipos de Reparo", icon: Wrench },
      { path: "/tipos-garantia", label: "Tipos de Garantia", icon: Shield, adminOnly: true },
    ],
  },
  {
    label: "Inteligência",
    items: [{ path: "/relatorios", label: "Relatórios", icon: ChartBar, adminOnly: true }],
  },
  {
    label: "Administração",
    items: [
      { path: "/usuarios", label: "Usuários", icon: Users, adminOnly: true },
      { path: "/backup", label: "Backups", icon: HardDrives, adminOnly: true },
    ],
  },
];
```

Substituir `SidebarNav` (linhas 44-72 atuais) por:

```jsx
function SidebarNav({ currentPath, user }) {
  const { closeMobile } = useSidebar();

  return (
    <SidebarContent>
      {navSections.map((section) => {
        const visibleItems = section.items
          .filter((item) => !item.adminOnly || user?.perfil === "admin")
          .filter((item) => !item.perfis || item.perfis.includes(user?.perfil));

        if (visibleItems.length === 0) return null;

        return (
          <div key={section.label ?? "top"} className="space-y-1">
            {section.label && (
              <p className="px-3 pt-3 pb-1 text-xs font-medium uppercase tracking-wider text-sidebar-foreground/40">
                {section.label}
              </p>
            )}
            {visibleItems.map(({ path, label, icon }) => {
              const isActive = path === "/" ? currentPath === "/" : currentPath.startsWith(path);
              return (
                <Link
                  key={path}
                  to={path}
                  onClick={closeMobile}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                  }`}
                >
                  {createElement(icon, { className: "h-4 w-4 shrink-0" })}
                  {label}
                </Link>
              );
            })}
          </div>
        );
      })}
    </SidebarContent>
  );
}
```

Nenhuma outra função de `Layout.jsx` muda — `SidebarUserFooter`, `AppSidebar`, `Layout` (export default)
permanecem idênticos.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `npm run test -- src/components/Layout.test.jsx`
Expected: PASS (7 testes — 5 já existentes + 2 novos deste step). As 5 asserções pré-existentes continuam
válidas sem alteração: `bg-sidebar-primary` no link ativo não mudou de nome, só o elemento pai que o
envolve.

- [ ] **Step 5: Rodar lint e a suite completa do frontend**

Run: `npm run lint && npm run test`
Expected: PASS — 0 erros.

- [ ] **Step 6: Checklist manual no browser — Light/Dark, 3 perfis**

Run: `npm run dev`, logar como admin, técnico e vendedor (`scripts/seed_demo.py` ou banco local).

- [ ] Confirmar que as seções aparecem com o rótulo correto e só os itens permitidos por perfil.
- [ ] Confirmar que a seção "Vendas" desaparece por completo para um perfil sem `Vendas` visível (ex.:
  técnico) — `visibleItems.length === 0` deve esconder a seção inteira, não deixar um rótulo órfão.
- [ ] Confirmar em Light Mode que o rótulo de seção (`text-sidebar-foreground/40`) é legível mas discreto.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/Layout.jsx frontend/src/components/Layout.test.jsx
git commit -m "feat(design-system): agrupar Sidebar pelos 6 Pilares Macrossistêmicos (Fase 3.2)"
```

---

### Task 3: `Dashboard.jsx` — hierarquia real (Panel dominante + LooseMetric + ListBlock)

**Files:**
- Modify: `frontend/src/pages/Dashboard.jsx`

**Why this task exists:** 8 KPIs idênticos em grid + 3 gráficos do mesmo tamanho — nenhum dado tem
tratamento de "isso é o mais importante" (§1, achado 1). Aplica a decisão de hierarquia registrada em
Global Constraints: Faturamento vira o `Panel` dominante com número hero; os outros 7 KPIs viram
`LooseMetric`; Resumo Financeiro vira `ListBlock`.

**Nenhuma mudança de lógica** — `fetchData`, `useEffect`, cálculo de `revenueData`/`techData`/
`servicesData`/`hasAnyData`/`isEmpty`, e os handlers de filtro permanecem idênticos. Só o `return` (bloco
JSX de apresentação, dentro do `else` de `isEmpty`) muda.

- [ ] **Step 1: Escrever o teste (falhando) de composição**

Adicionar a `frontend/src/pages/Dashboard.test.jsx` (dentro do `describe` existente):

```jsx
  it("Faturamento aparece como métrica dominante (Panel), os outros KPIs como métricas soltas", async () => {
    mockGet.mockResolvedValue(dadosComResultado);
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByText("Ticket Médio")).toBeInTheDocument());

    // Faturamento continua presente e com tratamento "hero" (texto maior que os outros números)
    const faturamentoValor = screen.getByText("R$ 1.000,00");
    expect(faturamentoValor.className).toMatch(/text-(4|5)xl/);
  });
```

(Ajustar a string de moeda formatada se `formatCurrency` produzir um separador diferente — checar
`frontend/src/lib/constants.js::formatCurrency` antes de escrever o valor exato esperado.)

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `npm run test -- src/pages/Dashboard.test.jsx`
Expected: FAIL — o número de Faturamento ainda usa `text-2xl` (mesmo tamanho dos outros KPIs), não
`text-4xl`/`text-5xl`.

- [ ] **Step 3: Reescrever o bloco de apresentação de `Dashboard.jsx`**

Adicionar os imports (junto aos já existentes):

```jsx
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";
import { ListBlock, ListBlockItem } from "@/components/ui/list-block";
import { LooseMetric } from "@/components/ui/loose-metric";
```

Substituir o bloco `{/* KPIs */}` até o fechamento de `{/* Cost Summary */}` (linhas 198-239 atuais) por:

```jsx
              {/* Métrica dominante */}
              <Panel>
                <PanelHeader>
                  <PanelTitle>Faturamento do período</PanelTitle>
                </PanelHeader>
                <PanelContent className="pt-0">
                  <p className="text-4xl sm:text-5xl font-bold text-card-foreground tracking-tight">
                    {formatCurrency(data?.faturamento_total)}
                  </p>
                </PanelContent>
              </Panel>

              {/* Métricas soltas -- peso secundário, sem moldura */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4">
                <LooseMetric label="Lucro Bruto" value={formatCurrency(data?.lucro_total)} />
                <LooseMetric label="Finalizadas" value={data?.ordens_finalizadas ?? "—"} />
                <LooseMetric label="Em Aberto" value={data?.ordens_abertas ?? "—"} valueClassName="text-warning" />
                <LooseMetric label="Peças Pendentes" value={data?.shopping_pendentes ?? "—"} />
                <LooseMetric label="Urgentes" value={data?.shopping_urgentes ?? "—"} valueClassName="text-destructive" />
                <LooseMetric label="Ticket Médio" value={formatCurrency(data?.ticket_medio)} />
                <LooseMetric
                  label="Resultado Líq."
                  value={formatCurrency(data?.resultado_liquido)}
                  valueClassName={data?.resultado_liquido >= 0 ? "text-success" : "text-destructive"}
                />
              </div>

              {/* Charts -- 1 principal (2/3) + 2 de apoio (1/3 cada) */}
              <Suspense fallback={<div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4"><ChartFallback /><ChartFallback /></div>}>
                <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
                  <RevenueChartCard data={revenueData} />
                  <TechnicianProfitChartCard data={techData} />
                </div>
              </Suspense>
              <div className="grid lg:grid-cols-3 gap-4">
                <Suspense fallback={<ChartFallback />}>
                  <ServicesChartCard data={servicesData} />
                </Suspense>

                {/* Resumo Financeiro -- bloco de lista, peso secundário */}
                <div className="lg:col-span-2">
                  <h3 className="text-sm font-medium text-card-foreground mb-2">Resumo Financeiro</h3>
                  <ListBlock>
                    {[
                      { label: "Custo de Peças", value: data?.custo_consumido_periodo, color: "text-destructive" },
                      { label: "Custos Operacionais", value: data?.custos_operacionais_periodo, color: "text-warning" },
                      { label: "Faturamento", value: data?.faturamento_total, color: "text-success" },
                      { label: "Lucro Bruto", value: data?.lucro_total, color: "text-info" },
                    ].map((item) => (
                      <ListBlockItem key={item.label}>
                        <span className="text-sm text-muted-foreground">{item.label}</span>
                        <span className={`text-sm font-semibold ${item.color}`}>{formatCurrency(item.value)}</span>
                      </ListBlockItem>
                    ))}
                  </ListBlock>
                </div>
              </div>
```

**Nota sobre o layout de gráficos:** a proporção `2fr_1fr` para Receita/Técnicos substitui o
`repeat(auto-fit,minmax(420px,1fr))` anterior (que dava peso igual aos dois) — em telas largas o gráfico de
Receita (o principal, per §8) ganha 2/3 do espaço; abaixo de `lg`, ambos colapsam para largura total
(comportamento de `grid-cols-1`, preservado).

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `npm run test -- src/pages/Dashboard.test.jsx`
Expected: PASS — incluindo o teste novo do Step 1. Reconferir os textos "Finalizadas"/"Ticket Médio" ainda
aparecem (agora como `label` de `LooseMetric`, não `title` de `KpiCard`) — os testes existentes buscam por
texto, não por componente, então continuam passando sem alteração.

- [ ] **Step 5: Verificar se `KpiCard.jsx`/`KpiCard.test.jsx` ficam órfãos**

`KpiCard` deixa de ser usado por `Dashboard.jsx` neste plano. Rodar:

```bash
grep -rn "KpiCard" frontend/src --include="*.jsx" --include="*.js" | grep -v "KpiCard.jsx\|KpiCard.test.jsx"
```

Se não houver nenhum outro consumidor (esperado — `KpiCard` só existia para o Dashboard), **não remover o
arquivo nesta task** (regra do `CLAUDE.md`: nunca remover código sem confirmar) — registrar como achado
não bloqueante em `KNOWN_ISSUES.md` na Task 4 (Validação), decisão de remover ou não fica para o CTO.

- [ ] **Step 6: Rodar lint e a suite completa do frontend**

Run: `npm run lint && npm run test`
Expected: PASS — 0 erros.

- [ ] **Step 7: Checklist manual no browser — Light/Dark, dados reais e estado vazio**

Run: `npm run dev`, logar, abrir o Dashboard com dados reais (seed) e depois com um filtro de data sem
resultado (estado vazio).

- [ ] Confirmar que o número de Faturamento tem tratamento visivelmente maior/mais pesado que as métricas
  soltas ao lado.
- [ ] Confirmar que as métricas soltas (`LooseMetric`) não têm moldura nem fundo, só número+rótulo.
- [ ] Confirmar em Light Mode que o `Panel` do Faturamento usa sombra como profundidade e o `ListBlock` do
  Resumo Financeiro usa só divisor entre linhas, sem card-dentro-de-card.
- [ ] Confirmar que o estado vazio (`DashboardEmpty`) e o estado de erro em tela cheia (`DashboardError`)
  continuam inalterados (não fazem parte do escopo desta task).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/Dashboard.jsx frontend/src/pages/Dashboard.test.jsx
git commit -m "feat(design-system): Dashboard com hierarquia real (Panel dominante + LooseMetric + ListBlock)"
```

---

### Task 4: Auditoria de harmonização da Landing

**Files:** nenhum arquivo modificado a priori — esta task é uma auditoria; qualquer correção encontrada é
adicionada aqui antes do commit.

**Why this task exists:** a Landing está fora da autorização de liberdade criativa total (§0.1 do plano
mestre) — não é redesenhada. Mas precisa continuar consistente com a identidade Pulse já aplicada em
`index.css`/ícone/wordmark (PR #61). Auditoria prévia (nesta sessão de planejamento) já confirmou: nenhum
hex hardcoded em `frontend/src/components/landing/*.jsx` (`grep -rn "#[0-9A-Fa-f]{3,6}"` → 0 resultados),
raio/sombra seguem a mesma escala do resto do produto (`rounded-lg`/`rounded-xl`/`shadow-*`), e
`LandingNavbar`/`LandingFooter` já usam `fluxoly-icon-inverted.svg` (ícone Pulse correto desde o PR #61).
Ou seja, a auditoria prévia já não encontrou nada a corrigir — este task confirma isso ao vivo antes de
fechar a fase.

- [ ] **Step 1: Confirmar a wordmark da Landing usa Space Grotesk (já deveria, classe global)**

`grep -n "font-wordmark\|Fluxoly" frontend/src/components/landing/*.jsx` — confirmar que qualquer texto
"Fluxoly" estilizado como logotipo usa a classe `.font-wordmark` (já `Space Grotesk` desde o PR #61), não
uma declaração de fonte própria da Landing.

- [ ] **Step 2: Checklist manual no browser — Landing em Light/Dark**

Run: `npm run dev`, abrir `/` deslogado.

- [ ] Confirmar visualmente que a Landing está com a mesma cor de assinatura (`#FF3D5A`) e ícone Pulse do
  resto do produto (não uma paleta própria desatualizada).
- [ ] Rolar as 14 seções e confirmar que nenhuma usa um radius/sombra fora da escala padrão do Tailwind
  (mesma checagem já feita no PR #49, sem regressão esperada).

- [ ] **Step 3: Se o Step 1 ou 2 encontrar uma divergência real**

Corrigir o arquivo específico (troca pontual de classe/token, mesmo padrão das correções de KI-050),
adicionar ao commit desta task com uma nota explicando o achado. **Se nada for encontrado** (resultado
esperado, dado o levantamento prévio), seguir para o Step 4 sem alteração de código.

- [ ] **Step 4: Commit (mesmo que sem mudança de código)**

Se o Step 3 não encontrou nada: nenhum commit de código é necessário para este task — a confirmação vira
parte do registro da Task 5 (Validação). Se encontrou algo:

```bash
git add <arquivo(s) corrigido(s)>
git commit -m "fix(design-system): harmonização pontual da Landing com a identidade Pulse (Fase 3.2)"
```

---

### Task 5: Validação final, documentação e PR

**Files:**
- Modify: `docs/engineering/ENGINEERING_GUIDE.md` (nova seção 3.5)
- Modify: `docs/operations/PROJECT_STATUS.md`
- Modify: `docs/operations/CHANGELOG.md`
- Modify: `docs/operations/KNOWN_ISSUES.md` (novo achado sobre `KpiCard.jsx` órfão, se confirmado no Task 3
  Step 5)
- Modify: `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md:298` (linha 3.2 da tabela)

- [ ] **Step 1: Rodar a suite completa e o lint uma última vez**

Run (a partir de `frontend/`): `npm run test && npm run lint && npm run build`
Expected: PASS — 0 erros, build de produção sem erro.

- [ ] **Step 2: Checklist manual final — os 3 perfis, Light/Dark, ponta a ponta**

Run: `npm run dev`, logar como admin/técnico/vendedor.

- [ ] Login → Dashboard → navegar por pelo menos 1 item de cada seção do Sidebar, confirmando que a
  navegação e os filtros de perfil continuam funcionando exatamente como antes (só a apresentação mudou).
- [ ] Alternar tema (automático/claro/escuro) na Sidebar em pelo menos 2 telas (Login, Dashboard) e
  confirmar transição suave, sem elemento ilegível em nenhum dos dois modos.

- [ ] **Step 3: Adicionar a seção 3.5 em `ENGINEERING_GUIDE.md`**

Em `docs/engineering/ENGINEERING_GUIDE.md`, logo após o fim da seção 3.4, adicionar:

```markdown
## 3.5 Fluxoly Design System (Fase 3.2 — Vitrine)

Formalizado em `docs/engineering/plans/PLAN-design-system-fase3.2-vitrine.md`. Primeira fase a redesenhar
composição de telas reais (Login, Shell/Sidebar, Dashboard) usando os recipientes da Foundation v2
(Fase 3.1) — prova de conceito da hierarquia de superfície antes de escalar para as Fases 3.3-3.5.

### Sidebar agrupado pelos 6 Pilares Macrossistêmicos

`Layout.jsx::navSections` substitui o array plano `navItems` — rotas agrupadas em Vendas/Operação/
Financeiro/Relacionamento/Serviços/Inteligência (`BRAND_IDENTITY.md` §2) + uma seção "Administração" fora
dos pilares (Usuários/Backups, operação de sistema, não função de negócio). Uma seção inteira desaparece
quando nenhum item dela é visível para o perfil da sessão — nunca um rótulo de seção órfão.

### Dashboard — 1 métrica dominante, resto secundário

Faturamento do período usa `Panel` com número hero (`text-4xl`/`text-5xl`); os outros 7 KPIs usam
`LooseMetric` (sem moldura); Resumo Financeiro usa `ListBlock` em vez de grade de caixas com fundo próprio.
`KpiCard.jsx` fica sem consumidor após esta fase — decisão de remover ou manter é do CTO (ver
`KNOWN_ISSUES.md`, se registrado).

### Login e Landing

`Login.jsx` migra a moldura do form para `Panel`, com respiro adicional acima/abaixo (`py-12`,
`space-y-8`). A Landing Page **não** é redesenhada nesta fase (fora da liberdade criativa total, ver
`PLAN-design-system-fase3-visual-experience.md` §0.1) — só auditada por consistência de token/marca.
```

- [ ] **Step 4: Atualizar `docs/operations/PROJECT_STATUS.md`**

Adicionar nova seção logo acima de "## ✅ Fase 3.1 do Fluxoly Design System", mesmo formato das fases
anteriores (título, o que foi entregue, validação, decisão do CTO, próximo passo → Fase 3.3).

- [ ] **Step 5: Atualizar `docs/operations/CHANGELOG.md`**

Adicionar entrada no topo de `## [Não lançado]` resumindo: Sidebar agrupado, Dashboard com hierarquia real,
Login com `Panel`, auditoria da Landing.

- [ ] **Step 6: Atualizar `docs/operations/KNOWN_ISSUES.md` (se aplicável)**

Se `KpiCard.jsx` ficou sem consumidor (Task 3, Step 5), registrar um novo KI documentando isso — mesmo
padrão de achado não bloqueante já usado em KI-047/048/049/051/052/053.

- [ ] **Step 7: Atualizar a tabela de faseamento do plano mestre**

Em `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md`, linha 3.2, trocar a descrição de
escopo por `✅ Concluído — PR #<número real>, <data do merge>`.

- [ ] **Step 8: Commit da documentação**

```bash
git add docs/engineering/ENGINEERING_GUIDE.md docs/operations/PROJECT_STATUS.md docs/operations/CHANGELOG.md docs/operations/KNOWN_ISSUES.md docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md
git commit -m "docs(design-system): registrar conclusão da Fase 3.2 (Vitrine)"
```

- [ ] **Step 9: Push e abrir o PR**

```bash
git push -u origin feat/design-system-fase3.2-vitrine
gh pr create --title "feat(design-system): Fase 3.2 — Vitrine (Login + Shell/Sidebar + Dashboard)" --body "$(cat <<'EOF'
## Resumo
- Login: form migra para Panel (Foundation v2), respiro real acima/abaixo
- Shell/Sidebar: 18 itens agrupados nos 6 Pilares Macrossistêmicos + seção Administração; duplicata de /compras removida
- Dashboard: Faturamento vira métrica dominante (Panel, número hero); outros 7 KPIs viram LooseMetric; Resumo Financeiro vira ListBlock
- Landing: auditoria de consistência (nenhuma mudança de código esperada, já herda os tokens corretamente)
- KpiCard.jsx fica sem consumidor -- decisão de remover fica para o CTO

## Plano
docs/engineering/plans/PLAN-design-system-fase3.2-vitrine.md

## Test plan
- [x] Suite de testes completa (frontend) passando
- [x] Lint sem erros, build de produção ok
- [x] Checklist manual: Light/Dark, 3 perfis, navegação ponta a ponta
EOF
)"
```

Aguardar CI verde antes de considerar mergeável — não fazer merge sem aprovação (protocolo padrão do
repositório, `CLAUDE.md`).

---

## Self-Review

**Cobertura da spec:** §2 (hierarquia de superfície) → Task 3 (Dashboard: 1 dominante + secundários +
apoio); §6 (sidebar agrupada, header de contexto) → Task 2 cobre o agrupamento; header de contexto
compartilhado (mencionado na spec como proposta, não decisão fechada) **não está neste plano** — cada
página ainda resolve título+ação com seu próprio `flex justify-between`; decisão de extrair um componente
compartilhado fica para uma fase futura quando mais telas estiverem migradas (evita abstrair cedo demais
com 1 único caso de uso real). §8 (composição do Dashboard) → Task 3, mapeamento de 8 KPIs reais
documentado no Global Constraints (a spec só ilustra com 3). §9 (Tier 1 = Vitrine) → as 4 áreas cobertas
(Login/Shell/Dashboard/Landing).

**Fora de escopo, deliberadamente:** redesenho de composição da Landing (fora da liberdade criativa total,
§0.1); header de contexto compartilhado (ver acima); remoção de `KpiCard.jsx` (decisão do CTO, não deste
plano); qualquer tela fora do Tier 1 (Orders/Vendas/Stock/etc. — Fase 3.3+).

**Consistência de nomes:** `Panel`/`PanelHeader`/`PanelTitle`/`PanelContent`, `ListBlock`/`ListBlockItem`,
`LooseMetric` — mesma API já testada na Fase 3.1, nenhum prop novo introduzido. `navSections` (Task 2)
é uma estrutura de dados nova, mas o formato de item individual (`path`/`label`/`icon`/`adminOnly`/
`perfis`) é idêntico ao `navItems` anterior — só a árvore ao redor mudou, os filtros de permissão
(`.filter`) são os mesmos dois já existentes, reaplicados por seção.

**Placeholders:** nenhum "TBD"/"implementar depois" nos steps de código. Os únicos valores entre `<>`
(número do PR, data do merge) são preenchidos depois que o PR real existe, mesmo padrão das Fases 3.0/3.1.
