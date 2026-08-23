# Fase 3.1 — Foundation v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evoluir a Foundation do Fluxoly Design System para os dois modos (Light+Dark, infra pronta na
Fase 3.0) — três novos recipientes de composição (`Panel`/`ListBlock`/`LooseMetric`, substituindo o `Card`
uniforme como recipiente universal), um `DataTable` real, um tema único para os gráficos Recharts, e a
correção do KI-050 (9 telas com classes Tailwind hardcoded que não reagem ao tema). Nenhuma tela é
redesenhada nesta fase — só componentes compartilhados (`components/ui/`, `lib/`) e o fix pontual de
KI-050 (troca de token de cor, sem mudança de composição).

**Architecture:** Todos os componentes novos usam exclusivamente as custom properties CSS já definidas em
`index.css` (Fase 3.0) — nenhum usa o prefixo `dark:` do Tailwind (que segue só `prefers-color-scheme` e
ignoraria o override manual via `data-theme`, o mesmo motivo pelo qual `index.css` define dois blocos de
override em vez de usar `dark:`). `Panel` funciona nos dois modos com uma única classe porque combina
borda (visível no Dark, quase invisível no Light) + sombra (visível no Light, invisível no Dark). A sombra
não reage ao tema — é um valor fixo do Tailwind (`shadow-sm`); funciona nos dois modos porque é sutil o
bastante para ler como profundidade no Light Mode e simplesmente não aparecer contra um fundo já
quase-preto no Dark Mode. Nenhuma lógica condicional de tema é necessária em nenhum componente desta
fase. Os gráficos (SVG via Recharts,
que não recebe classes Tailwind em props como `stroke`/`fill`) usam strings `var(--color-*)` diretamente —
o navegador resolve o valor a cada re-render, reagindo à troca de tema automaticamente.

**Tech Stack:** React 19, Tailwind CSS v4, Vite 8, Vitest 4 + Testing Library (jsdom), Recharts.

**Spec:** `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (§0.1 liberdade criativa,
§0.2 identidade Pulse, §2 princípios de composição, §3/§4 Light/Dark, §7 evolução de componentes, §12
faseamento — linha 3.1); `docs/operations/KNOWN_ISSUES.md` KI-050. Este plano implementa exatamente a
linha 3.1 da tabela de faseamento — nenhuma tela é redesenhada aqui (isso é Fase 3.2+).

## Global Constraints

- Nenhum componente de página (`pages/`) é redesenhado nesta fase, exceto a troca pontual de classe de cor
  exigida pelo KI-050 (Tasks 4 e 5) — que é correção de bug (contraste/reatividade ao tema), não mudança de
  composição/layout. Ver `PLAN-design-system-fase3-visual-experience.md` §12, linha 3.1: "Nenhuma tela
  redesenhada ainda (mesmo princípio da Foundation da Fase 2)".
- Nenhuma classe com o prefixo `dark:` do Tailwind em nenhum componente novo — este projeto não usa o
  variant de classe do Tailwind para tema (seria inconsistente com o override manual via `data-theme`, que
  já existe desde a Fase 3.0). Toda diferença visual entre os dois modos vem só das custom properties CSS
  já resolvidas por token (`--color-*`).
- Identidade de marca já decidida (não é decisão deste plano): `#FF3D5A`/`#29E0C9` (Pulse), tokens
  `--color-success`/`--color-warning`/`--color-destructive`/`--color-info` já calibrados para WCAG AA nos
  dois modos (Fase 3.0). Nenhum token novo de cor é criado nesta fase — só reaproveitamento dos 4 já
  existentes.
- `DataTable`/`Panel`/`ListBlock`/`LooseMetric` são construídos e testados isoladamente, **sem** substituir
  nenhuma tabela/card existente em nenhuma página — mesmo princípio do PR 1 (Foundation) da Fase 2
  (`PLAN-design-system-fase2.md`): construir o vocabulário antes de migrar telas.
- Zero mudança de lógica de negócio, API, schema ou permissões — escopo 100% frontend/apresentação
  (`frontend/src/`).
- Testes isolados, nenhum toca `database.db` (não aplicável — não há backend envolvido).
- Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`); branch `feat/design-system-fase3.1-foundation-v2`.
- **Decisão registrada nesta plano (Task 5):** o token `financeiro: "text-purple-400"` em `Users.jsx`
  (papel/perfil de usuário) fica **fora** desta correção — não existe token semântico de roxo na paleta
  Pulse, e inventar um novo token de cor não está no escopo de uma correção de bug (KI-050). Registrado
  como novo achado não bloqueante (KI-051) na Task 6, mesmo padrão de KI-047/KI-048 (Fase 2) — achado
  registrado, não corrigido, não bloqueia o merge.

---

### Task 1: Recipientes de composição — `Panel` / `ListBlock` / `LooseMetric`

**Files:**
- Create: `frontend/src/components/ui/panel.jsx`
- Create: `frontend/src/components/ui/panel.test.jsx`
- Create: `frontend/src/components/ui/list-block.jsx`
- Create: `frontend/src/components/ui/list-block.test.jsx`
- Create: `frontend/src/components/ui/loose-metric.jsx`
- Create: `frontend/src/components/ui/loose-metric.test.jsx`

**Interfaces:**
- Produces: `Panel`/`PanelHeader`/`PanelTitle`/`PanelDescription`/`PanelContent` (mesma API de
  `Card`/`CardHeader`/`CardTitle`/`CardDescription`/`CardContent`, recipiente "dominante"); `ListBlock`/
  `ListBlockItem({ interactive?: boolean })` (recipiente "bloco de lista", sem moldura própria);
  `LooseMetric({ label, value, className?, valueClassName?, labelClassName? })` (recipiente "métrica
  solta", sem moldura nenhuma). Nenhum é consumido por nenhuma página nesta fase — ficam disponíveis para
  as Fases 3.2+.
- Consumes: `cn` de `@/lib/utils` (já existente); `interactiveRowClassName` de `@/lib/interaction` (já
  existente, Fase 2).

- [ ] **Step 1: Criar a branch de feature**

```bash
git checkout main
git pull
git checkout -b feat/design-system-fase3.1-foundation-v2
```

- [ ] **Step 2: Escrever o teste (falhando) do `Panel`**

Criar `frontend/src/components/ui/panel.test.jsx`:

```jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Panel, PanelHeader, PanelTitle, PanelDescription, PanelContent } from "./panel";

describe("Panel", () => {
  it("renderiza com borda e sombra (recipiente dominante, funciona nos dois modos sem classe dark:)", () => {
    render(<Panel data-testid="panel">conteúdo</Panel>);
    const panel = screen.getByTestId("panel");
    expect(panel.className).toContain("border");
    expect(panel.className).toContain("shadow-sm");
    expect(panel.className).not.toContain("dark:");
  });

  it("compõe header/title/description/content", () => {
    render(
      <Panel>
        <PanelHeader>
          <PanelTitle>Faturamento do período</PanelTitle>
          <PanelDescription>Últimos 30 dias</PanelDescription>
        </PanelHeader>
        <PanelContent>R$ 84.320</PanelContent>
      </Panel>
    );
    expect(screen.getByText("Faturamento do período")).toBeInTheDocument();
    expect(screen.getByText("Últimos 30 dias")).toBeInTheDocument();
    expect(screen.getByText("R$ 84.320")).toBeInTheDocument();
  });

  it("aceita className extra sem substituir as classes base", () => {
    render(<Panel data-testid="panel" className="max-w-xl" />);
    const panel = screen.getByTestId("panel");
    expect(panel.className).toContain("max-w-xl");
    expect(panel.className).toContain("rounded-xl");
  });
});
```

- [ ] **Step 3: Rodar e confirmar que falha**

Run (a partir de `frontend/`): `npm run test -- src/components/ui/panel.test.jsx`
Expected: FAIL — `Failed to resolve import "./panel"`.

- [ ] **Step 4: Implementar `panel.jsx`**

Criar `frontend/src/components/ui/panel.jsx`:

```jsx
import { cn } from "@/lib/utils";

/**
 * Recipiente "dominante" da Fase 3.1 (Foundation v2) — para o único elemento de maior peso de
 * cada tela (ex.: métrica hero do Dashboard, painel principal de uma tela de detalhe). Ver
 * docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md §7/§8.
 *
 * Diferente de `Card` (recipiente genérico, ainda usado em toda parte): `Panel` sempre combina
 * borda sutil + sombra. A borda dá a separação no Dark Mode (sombra não é visível em fundo quase
 * preto); a sombra dá a profundidade no Light Mode (spec §3: "sombra é a ferramenta de
 * profundidade no light"). Como os dois (`--color-border` e a cor de sombra do navegador) já
 * reagem ao tema sozinhos, uma única classe funciona nos dois modos — não precisa de variante
 * condicional por tema (`dark:` do Tailwind não é usado neste projeto, ver Global Constraints).
 */
export function Panel({ className, ...props }) {
  return (
    <div
      className={cn("rounded-xl border border-border bg-card text-card-foreground shadow-sm", className)}
      {...props}
    />
  );
}

export function PanelHeader({ className, ...props }) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}

export function PanelTitle({ className, ...props }) {
  return (
    <h3
      className={cn("text-lg font-semibold leading-none tracking-tight text-card-foreground", className)}
      {...props}
    />
  );
}

export function PanelDescription({ className, ...props }) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
}

export function PanelContent({ className, ...props }) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `npm run test -- src/components/ui/panel.test.jsx`
Expected: PASS (3 testes).

- [ ] **Step 6: Escrever o teste (falhando) do `ListBlock`**

Criar `frontend/src/components/ui/list-block.test.jsx`:

```jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ListBlock, ListBlockItem } from "./list-block";

describe("ListBlock", () => {
  it("separa os itens com divisor, sem moldura própria", () => {
    render(<ListBlock data-testid="block" />);
    // Checagem por token exato, não substring: "divide-border" contém "border" como
    // substring e faria um regex /\bborder\b/ (limite de palavra bate no hífen) dar falso
    // positivo mesmo numa implementação correta.
    const classes = screen.getByTestId("block").className.split(" ");
    expect(classes).toContain("divide-y");
    expect(classes).not.toContain("border");
    expect(classes.some((c) => c.startsWith("rounded"))).toBe(false);
    expect(classes).not.toContain("bg-card");
  });

  it("renderiza itens", () => {
    render(
      <ListBlock>
        <ListBlockItem>Item 1</ListBlockItem>
        <ListBlockItem>Item 2</ListBlockItem>
      </ListBlock>
    );
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
  });

  it("ListBlockItem interativo ganha hover/foco de interactiveRowClassName", () => {
    render(<ListBlockItem interactive data-testid="item">Item</ListBlockItem>);
    expect(screen.getByTestId("item").className).toContain("hover:bg-accent/50");
  });

  it("ListBlockItem não interativo não ganha classes de hover", () => {
    render(<ListBlockItem data-testid="item">Item</ListBlockItem>);
    expect(screen.getByTestId("item").className).not.toContain("hover:bg-accent/50");
  });
});
```

- [ ] **Step 7: Rodar e confirmar que falha**

Run: `npm run test -- src/components/ui/list-block.test.jsx`
Expected: FAIL — `Failed to resolve import "./list-block"`.

- [ ] **Step 8: Implementar `list-block.jsx`**

Criar `frontend/src/components/ui/list-block.jsx`:

```jsx
import { cn } from "@/lib/utils";
import { interactiveRowClassName } from "@/lib/interaction";

/**
 * Recipiente "bloco de lista" da Fase 3.1 (Foundation v2) — para listas de peso secundário que
 * não precisam da moldura completa do `Panel` (spec §7: "sem moldura própria, só divisor sutil
 * entre linhas"). `ListBlockItem` reaproveita `interactiveRowClassName` (hover/foco, já usado em
 * linhas de tabela desde a Fase 2) quando `interactive` é passado.
 */
export function ListBlock({ className, ...props }) {
  return <div className={cn("divide-y divide-border", className)} {...props} />;
}

export function ListBlockItem({ className, interactive = false, ...props }) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 py-3",
        interactive && interactiveRowClassName,
        className
      )}
      {...props}
    />
  );
}
```

- [ ] **Step 9: Rodar e confirmar que passa**

Run: `npm run test -- src/components/ui/list-block.test.jsx`
Expected: PASS (4 testes).

- [ ] **Step 10: Escrever o teste (falhando) do `LooseMetric`**

Criar `frontend/src/components/ui/loose-metric.test.jsx`:

```jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LooseMetric } from "./loose-metric";

describe("LooseMetric", () => {
  it("renderiza valor e rótulo", () => {
    render(<LooseMetric value="23" label="Vendas hoje" />);
    expect(screen.getByText("23")).toBeInTheDocument();
    expect(screen.getByText("Vendas hoje")).toBeInTheDocument();
  });

  it("não tem moldura (sem border nem bg-card)", () => {
    const { container } = render(<LooseMetric value="23" label="Vendas hoje" />);
    expect(container.firstChild.className).not.toMatch(/\bborder\b/);
    expect(container.firstChild.className).not.toContain("bg-card");
  });

  it("aceita className extra no valor e no rótulo", () => {
    render(
      <LooseMetric value="R$ 890" label="Ticket médio" valueClassName="text-primary" labelClassName="uppercase" />
    );
    expect(screen.getByText("R$ 890").className).toContain("text-primary");
    expect(screen.getByText("Ticket médio").className).toContain("uppercase");
  });
});
```

- [ ] **Step 11: Rodar e confirmar que falha**

Run: `npm run test -- src/components/ui/loose-metric.test.jsx`
Expected: FAIL — `Failed to resolve import "./loose-metric"`.

- [ ] **Step 12: Implementar `loose-metric.jsx`**

Criar `frontend/src/components/ui/loose-metric.jsx`:

```jsx
import { cn } from "@/lib/utils";

/**
 * Recipiente "métrica solta" da Fase 3.1 (Foundation v2) — número + rótulo pequeno, sem moldura
 * nenhuma (spec §7/§8, ex.: "Vendas hoje / Ticket médio / OS abertas" lado a lado no Dashboard).
 */
export function LooseMetric({ label, value, className, valueClassName, labelClassName }) {
  return (
    <div className={cn("flex flex-col gap-0.5", className)}>
      <span className={cn("text-2xl font-bold text-card-foreground tracking-tight", valueClassName)}>
        {value}
      </span>
      <span className={cn("text-xs text-muted-foreground", labelClassName)}>{label}</span>
    </div>
  );
}
```

- [ ] **Step 13: Rodar e confirmar que passa**

Run: `npm run test -- src/components/ui/loose-metric.test.jsx`
Expected: PASS (3 testes).

- [ ] **Step 14: Rodar a suite completa do frontend**

Run: `npm run test`
Expected: PASS — nenhum componente/página existente importa esses arquivos ainda, zero risco de regressão.

- [ ] **Step 15: Commit**

```bash
git add frontend/src/components/ui/panel.jsx frontend/src/components/ui/panel.test.jsx frontend/src/components/ui/list-block.jsx frontend/src/components/ui/list-block.test.jsx frontend/src/components/ui/loose-metric.jsx frontend/src/components/ui/loose-metric.test.jsx
git commit -m "feat(design-system): recipientes Panel/ListBlock/LooseMetric (Foundation v2)"
```

---

### Task 2: `DataTable` — tabela real da Foundation

**Files:**
- Create: `frontend/src/components/ui/data-table.jsx`
- Create: `frontend/src/components/ui/data-table.test.jsx`

**Interfaces:**
- Consumes: `cn` de `@/lib/utils`; `interactiveRowClassName` de `@/lib/interaction`.
- Produces: `DataTable({ columns, rows, getRowKey, stickyHeader?, onRowClick?, className? })`. `columns`:
  `Array<{ key: string, header: string, render?: (row) => ReactNode, className?: string, headerClassName?:
  string }>`. Não consumido por nenhuma página nesta fase — migração tela a tela é Fase 3.2+.

- [ ] **Step 1: Escrever o teste (falhando)**

Criar `frontend/src/components/ui/data-table.test.jsx`:

```jsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DataTable } from "./data-table";

const columns = [
  { key: "nome", header: "Nome" },
  { key: "valor", header: "Valor", render: (row) => `R$ ${row.valor}` },
];
const rows = [
  { id: 1, nome: "Item A", valor: 10 },
  { id: 2, nome: "Item B", valor: 20 },
];

describe("DataTable", () => {
  it("renderiza cabeçalhos e células, usando render() quando informado", () => {
    render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} />);
    expect(screen.getByText("Nome")).toBeInTheDocument();
    expect(screen.getByText("Valor")).toBeInTheDocument();
    expect(screen.getByText("Item A")).toBeInTheDocument();
    expect(screen.getByText("R$ 10")).toBeInTheDocument();
    expect(screen.getByText("R$ 20")).toBeInTheDocument();
  });

  it("renderiza uma linha por item de rows, sem linha extra quando vazio", () => {
    const { container } = render(<DataTable columns={columns} rows={[]} getRowKey={(r) => r.id} />);
    expect(container.querySelectorAll("tbody tr")).toHaveLength(0);
  });

  it("stickyHeader aplica sticky top-0 no <thead>", () => {
    const { container } = render(
      <DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} stickyHeader />
    );
    expect(container.querySelector("thead").className).toContain("sticky");
  });

  it("sem stickyHeader, o <thead> não tem a classe sticky", () => {
    const { container } = render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} />);
    expect(container.querySelector("thead").className).not.toContain("sticky");
  });

  it("onRowClick é chamado ao clicar na linha e ao pressionar Enter com foco nela", async () => {
    const onRowClick = vi.fn();
    render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} onRowClick={onRowClick} />);
    const user = userEvent.setup();

    await user.click(screen.getByText("Item A"));
    expect(onRowClick).toHaveBeenCalledWith(rows[0]);

    screen.getByText("Item B").closest("tr").focus();
    await user.keyboard("{Enter}");
    expect(onRowClick).toHaveBeenCalledWith(rows[1]);
  });

  it("sem onRowClick, as linhas não são focáveis nem clicáveis", () => {
    render(<DataTable columns={columns} rows={rows} getRowKey={(r) => r.id} />);
    const row = screen.getByText("Item A").closest("tr");
    expect(row).not.toHaveAttribute("tabindex");
  });
});
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `npm run test -- src/components/ui/data-table.test.jsx`
Expected: FAIL — `Failed to resolve import "./data-table"`.

- [ ] **Step 3: Implementar `data-table.jsx`**

Criar `frontend/src/components/ui/data-table.jsx`:

```jsx
import { cn } from "@/lib/utils";
import { interactiveRowClassName } from "@/lib/interaction";

/**
 * Tabela real da Foundation (Fase 3.1) — substitui o padrão de HTML cru com bordas manuais
 * repetido por arquivo (ex.: Reports.jsx, OperationalCosts.jsx, Users.jsx). Ainda não é usada por
 * nenhuma tela nesta fase (mesmo princípio da Foundation da Fase 2 — construir antes de migrar,
 * ver PLAN-design-system-fase2.md "PR 1"); a migração tela a tela é escopo das Fases 3.2+.
 *
 * @param {{
 *   columns: Array<{ key: string, header: string, render?: (row: any) => import("react").ReactNode, className?: string, headerClassName?: string }>,
 *   rows: Array<any>,
 *   getRowKey: (row: any) => string | number,
 *   stickyHeader?: boolean,
 *   onRowClick?: (row: any) => void,
 *   className?: string,
 * }} props
 */
export function DataTable({ columns, rows, getRowKey, stickyHeader = false, onRowClick, className }) {
  return (
    <div className={cn("overflow-x-auto rounded-xl border border-border", className)}>
      <table className="w-full text-sm">
        <thead className={cn(stickyHeader && "sticky top-0 z-10 bg-card")}>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  "text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider",
                  col.headerClassName
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row) => (
            <tr
              key={getRowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              tabIndex={onRowClick ? 0 : undefined}
              onKeyDown={
                onRowClick
                  ? (e) => {
                      if (e.key === "Enter") onRowClick(row);
                    }
                  : undefined
              }
              className={cn(onRowClick && interactiveRowClassName, onRowClick && "cursor-pointer")}
            >
              {columns.map((col) => (
                <td key={col.key} className={cn("px-4 py-3", col.className)}>
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `npm run test -- src/components/ui/data-table.test.jsx`
Expected: PASS (6 testes).

- [ ] **Step 5: Rodar a suite completa do frontend**

Run: `npm run test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/data-table.jsx frontend/src/components/ui/data-table.test.jsx
git commit -m "feat(design-system): DataTable real da Foundation (header sticky, hover, onRowClick)"
```

---

### Task 3: Tema único de gráfico (`lib/chart-theme.js`) + wiring nos 3 chart cards

**Files:**
- Create: `frontend/src/lib/chart-theme.js`
- Create: `frontend/src/lib/chart-theme.test.js`
- Modify: `frontend/src/components/dashboard/RevenueChartCard.jsx:44-80`
- Modify: `frontend/src/components/dashboard/ServicesChartCard.jsx:9-21,90-111`
- Modify: `frontend/src/components/dashboard/TechnicianProfitChartCard.jsx:13-22,59-93`

**Interfaces:**
- Produces: `CHART_GRID_STROKE`, `CHART_AXIS_TICK`, `CHART_CURSOR_STROKE` (strings/objeto `var(--color-*)`,
  para props de eixo/grid/cursor do Recharts), `CHART_PALETTE` (array de 5 `var(--color-chart-N)`),
  `chartColor(index)` (cicla a paleta). Consumido pelas 3 modificações abaixo.

**Why this task exists:** os 3 cards de gráfico do Dashboard usam `stroke="hsl(222 47% 19%)"` — o mesmo
azul-marinho hardcoded que a Fase 3.0 já removeu de `index.css` por não corresponder a nenhum token da
marca (comentário em `index.css`: "não correspondia a nenhum token da marca") — e paletas de cor fixas em
hex (`#3B82F6` etc.), sem nenhuma relação com a paleta Pulse nem com os dois modos de tema. Como Recharts
recebe cor via prop SVG (`stroke`/`fill`), não via classe Tailwind, essas cores não reagem à troca de tema
mesmo depois da Fase 3.0 — mesma classe de bug do KI-050, só que em componentes de gráfico em vez de texto.

- [ ] **Step 1: Escrever o teste (falhando) de `chart-theme.js`**

Criar `frontend/src/lib/chart-theme.test.js`:

```js
import { describe, it, expect } from "vitest";
import {
  CHART_GRID_STROKE,
  CHART_AXIS_TICK,
  CHART_CURSOR_STROKE,
  CHART_PALETTE,
  chartColor,
} from "./chart-theme";

describe("chart-theme", () => {
  it("expõe 5 cores na paleta categórica (--color-chart-1..5)", () => {
    expect(CHART_PALETTE).toHaveLength(5);
    expect(CHART_PALETTE[0]).toBe("var(--color-chart-1)");
    expect(CHART_PALETTE[4]).toBe("var(--color-chart-5)");
  });

  it("chartColor cicla quando o índice excede o tamanho da paleta", () => {
    expect(chartColor(0)).toBe(CHART_PALETTE[0]);
    expect(chartColor(4)).toBe(CHART_PALETTE[4]);
    expect(chartColor(5)).toBe(CHART_PALETTE[0]);
    expect(chartColor(6)).toBe(CHART_PALETTE[1]);
  });

  it("grid/eixo/cursor usam custom properties CSS -- reagem à troca de tema sem re-render manual", () => {
    expect(CHART_GRID_STROKE).toBe("var(--color-border)");
    expect(CHART_AXIS_TICK).toEqual({ fill: "var(--color-muted-foreground)", fontSize: 12 });
    expect(CHART_CURSOR_STROKE).toBe("var(--color-muted-foreground)");
  });
});
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `npm run test -- src/lib/chart-theme.test.js`
Expected: FAIL — `Failed to resolve import "./chart-theme"`.

- [ ] **Step 3: Implementar `chart-theme.js`**

Criar `frontend/src/lib/chart-theme.js`:

```js
// Tema único para gráficos Recharts (Fase 3.1, Foundation v2) -- ver
// docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md §7 ("Definir tema único...
// consumido por todo gráfico, em vez de estilizado ad-hoc por chart card"). Recharts aceita
// qualquer string CSS em props como `stroke`/`fill`/`color`, incluindo var(--...) -- o navegador
// resolve o valor a cada re-render, então os gráficos já reagem à troca de tema (claro/escuro/
// automático) sem nenhum código extra de sincronização.
export const CHART_GRID_STROKE = "var(--color-border)";
export const CHART_AXIS_TICK = { fill: "var(--color-muted-foreground)", fontSize: 12 };
export const CHART_CURSOR_STROKE = "var(--color-muted-foreground)";

// Paleta categórica (séries/fatias sem status semântico) -- os 5 tokens --color-chart-1..5 já
// existem em index.css desde a Fase 3.0; ciclada via chartColor() quando há mais séries que cores
// (trade-off aceito -- antes desta fase já não havia nenhuma garantia de cor única acima de 8-10
// séries, ver COLORS[] fixo nos cards anteriores a este task).
export const CHART_PALETTE = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
];

export function chartColor(index) {
  return CHART_PALETTE[index % CHART_PALETTE.length];
}
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `npm run test -- src/lib/chart-theme.test.js`
Expected: PASS (3 testes).

- [ ] **Step 5: Ligar o tema em `RevenueChartCard.jsx`**

Em `frontend/src/components/dashboard/RevenueChartCard.jsx`, adicionar o import (junto ao já existente de
`formatCurrency`):

```jsx
import { CHART_GRID_STROKE, CHART_AXIS_TICK, CHART_CURSOR_STROKE, chartColor } from "@/lib/chart-theme";
```

E substituir o bloco `<defs>`...`<Area .../>` (linhas 44-80 atuais) por:

```jsx
          <defs>
            <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={chartColor(0)} stopOpacity={0.3} />
              <stop offset="95%" stopColor={chartColor(0)} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={CHART_GRID_STROKE}
            vertical={false}
            style={{ opacity: 0.5 }}
          />
          <XAxis
            dataKey="data"
            tick={CHART_AXIS_TICK}
            tickLine={false}
            axisLine={false}
            style={{ opacity: 0.7 }}
          />
          <YAxis
            tick={CHART_AXIS_TICK}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
            style={{ opacity: 0.7 }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: CHART_CURSOR_STROKE, strokeOpacity: 0.3 }} />
          <Area
            type="monotone"
            dataKey="total"
            name="Faturamento"
            stroke={chartColor(0)}
            fill="url(#colorRevenue)"
            strokeWidth={2.5}
            isAnimationActive={true}
            animationDuration={800}
          />
```

- [ ] **Step 6: Ligar o tema em `ServicesChartCard.jsx`**

Em `frontend/src/components/dashboard/ServicesChartCard.jsx`, substituir o import e o array `COLORS`
(linhas 1-21 atuais) por:

```jsx
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { chartColor } from "@/lib/chart-theme";
```

(o array `COLORS` local é removido — as duas ocorrências de `COLORS[i % COLORS.length]` mais abaixo, linhas
94 e 111 atuais, viram `chartColor(i)`):

```jsx
              <Pie
                data={dataWithPercentage}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={85}
                paddingAngle={2}
                dataKey="value"
                nameKey="name"
                animationDuration={800}
                animationEasing="ease-out"
              >
                {dataWithPercentage.map((_, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={chartColor(i)}
                    style={{ filter: "drop-shadow(0 1px 3px rgba(0,0,0,0.1))" }}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} cursor={false} />
```

e, na legenda:

```jsx
            {dataWithPercentage.slice(0, 10).map((item, i) => (
              <LegendItem
                key={item.name}
                name={item.name}
                color={chartColor(i)}
                percentage={item.percentage}
              />
            ))}
```

- [ ] **Step 7: Ligar o tema em `TechnicianProfitChartCard.jsx`**

Em `frontend/src/components/dashboard/TechnicianProfitChartCard.jsx`, substituir o import e o array
`COLORS` (linhas 1-22 atuais) por:

```jsx
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "@/lib/constants";
import { CHART_GRID_STROKE, CHART_AXIS_TICK, chartColor } from "@/lib/chart-theme";
```

E substituir o bloco `<CartesianGrid .../>`...`</Bar>` (linhas 59-93 atuais) por:

```jsx
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={CHART_GRID_STROKE}
            vertical={false}
            style={{ opacity: 0.5 }}
          />
          <XAxis
            dataKey="tecnico"
            tick={CHART_AXIS_TICK}
            tickLine={false}
            axisLine={false}
            style={{ opacity: 0.7 }}
          />
          <YAxis
            tick={CHART_AXIS_TICK}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
            style={{ opacity: 0.7 }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--color-muted)" }} />
          <Bar
            dataKey="lucro"
            name="Lucro"
            radius={[6, 6, 0, 0]}
            isAnimationActive={true}
            animationDuration={800}
          >
            {data.map((_, i) => (
              <Cell
                key={`cell-${i}`}
                fill={chartColor(i)}
                style={{ filter: "drop-shadow(0 1px 2px rgba(0,0,0,0.1))" }}
              />
            ))}
          </Bar>
```

- [ ] **Step 8: Rodar a suite completa do frontend**

Run: `npm run test`
Expected: PASS — `Dashboard.test.jsx` (único teste que renderiza esses 3 cards, via `Dashboard.jsx`) não
faz asserção sobre cor/stroke, só sobre presença de dado — confirmado por busca prévia nos arquivos de
teste, nenhum assert em `hsl(`/`#3B82F6`/`COLORS`.

- [ ] **Step 9: Checklist manual — gráficos nos dois modos**

Run: `npm run dev`, logar, abrir o Dashboard.

- [ ] Em Light Mode forçado (DevTools > Rendering > `prefers-color-scheme: light`), confirmar que a grade
  e os rótulos de eixo dos 3 gráficos ficam sutis mas legíveis contra o fundo claro (antes desta task,
  usavam uma cor calibrada só para fundo escuro).
- [ ] Em Dark Mode, confirmar que os 3 gráficos continuam com aparência equivalente à anterior (mesma
  paleta de cor, agora vinda dos tokens `--color-chart-*` em vez de hex fixo).

- [ ] **Step 10: Commit**

```bash
git add frontend/src/lib/chart-theme.js frontend/src/lib/chart-theme.test.js frontend/src/components/dashboard/RevenueChartCard.jsx frontend/src/components/dashboard/ServicesChartCard.jsx frontend/src/components/dashboard/TechnicianProfitChartCard.jsx
git commit -m "feat(design-system): tema único de gráfico (Recharts) reagindo a Light/Dark"
```

---

### Task 4: KI-050 — `KpiCard.jsx` + `Dashboard.jsx` (área do Dashboard)

**Files:**
- Create: `frontend/src/components/dashboard/KpiCard.test.jsx`
- Modify: `frontend/src/components/dashboard/KpiCard.jsx:4-18`
- Modify: `frontend/src/pages/Dashboard.jsx:226-230`

**Why this task exists:** `KpiCard.jsx` (10 ocorrências) e `Dashboard.jsx` (4 ocorrências) são as duas
maiores fontes de classes Tailwind hardcoded do KI-050 — cores calibradas só para o Dark Mode anterior à
Fase 3.0, que caem para contraste ~1,5:1 em fundo claro. A correção troca cada classe pela equivalente já
calibrada para os dois modos (`text-success`/`text-warning`/`text-destructive`/`text-info`, mesmos tokens
que `Badge` já usa desde a Fase 2/3.0) — mesmo resultado visual em Dark Mode (as cores atuais já eram
próximas dos tokens), Light Mode passa a ter contraste correto.

- [ ] **Step 1: Escrever o teste (falhando) do `KpiCard`**

Criar `frontend/src/components/dashboard/KpiCard.test.jsx`:

```jsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CurrencyDollar } from "@phosphor-icons/react";
import KpiCard from "./KpiCard";

describe("KpiCard", () => {
  it("renderiza título e valor formatado", () => {
    render(<KpiCard title="Faturamento" value={1500} icon={CurrencyDollar} />);
    expect(screen.getByText("Faturamento")).toBeInTheDocument();
  });

  it.each([
    ["primary", "text-info"],
    ["blue", "text-info"],
    ["green", "text-success"],
    ["amber", "text-warning"],
    ["red", "text-destructive"],
  ])('color="%s" usa o token de tema %s em vez de classe Tailwind crua -- KI-050', (color, expectedClass) => {
    const { container } = render(<KpiCard title="X" value={1} icon={CurrencyDollar} color={color} />);
    expect(container.firstChild.className).toContain(expectedClass);
  });

  it("cai em 'primary' (text-info) quando a cor não existe no mapa", () => {
    const { container } = render(<KpiCard title="X" value={1} icon={CurrencyDollar} color="inexistente" />);
    expect(container.firstChild.className).toContain("text-info");
  });
});
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `npm run test -- src/components/dashboard/KpiCard.test.jsx`
Expected: FAIL — os testes de cor falham (o componente ainda usa `text-blue-400`/`text-emerald-400`/etc.,
não `text-info`/`text-success`/etc.).

- [ ] **Step 3: Corrigir `KpiCard.jsx`**

Em `frontend/src/components/dashboard/KpiCard.jsx`, substituir `colorMap`/`iconColorMap` (linhas 4-18
atuais) por:

```jsx
// Cores migradas para os tokens de tema (Fase 3.1 -- corrige KI-050: as classes anteriores
// (emerald/amber/red/blue-400) eram calibradas só para o Dark Mode anterior à Fase 3.0 e caíam
// para contraste ~1,5:1 em fundo claro). Mesmo resultado visual em Dark Mode -- os tokens já
// foram calibrados para ficar próximos das cores anteriores (Fase 3.0, ver theme-tokens.js).
const colorMap = {
  primary: "bg-gradient-to-br from-info/20 to-info/10 border-info/20 text-info",
  green:   "bg-gradient-to-br from-success/20 to-success/10 border-success/20 text-success",
  amber:   "bg-gradient-to-br from-warning/20 to-warning/10 border-warning/20 text-warning",
  red:     "bg-gradient-to-br from-destructive/20 to-destructive/10 border-destructive/20 text-destructive",
  blue:    "bg-gradient-to-br from-info/20 to-info/10 border-info/20 text-info",
};

const iconColorMap = {
  primary: "bg-info/15 text-info",
  green:   "bg-success/15 text-success",
  amber:   "bg-warning/15 text-warning",
  red:     "bg-destructive/15 text-destructive",
  blue:    "bg-info/15 text-info",
};
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `npm run test -- src/components/dashboard/KpiCard.test.jsx`
Expected: PASS (5 testes).

- [ ] **Step 5: Corrigir `Dashboard.jsx`**

Em `frontend/src/pages/Dashboard.jsx`, substituir o array de cores do "Resumo Financeiro" (linhas 226-230
atuais) por:

```jsx
                    {[
                      { label: "Custo de Peças", value: data?.custo_consumido_periodo, color: "text-destructive" },
                      { label: "Custos Operacionais", value: data?.custos_operacionais_periodo, color: "text-warning" },
                      { label: "Faturamento", value: data?.faturamento_total, color: "text-success" },
                      { label: "Lucro Bruto", value: data?.lucro_total, color: "text-info" },
                    ].map((item) => (
```

- [ ] **Step 6: Rodar `Dashboard.test.jsx` e a suite completa**

Run: `npm run test -- src/pages/Dashboard.test.jsx && npm run test`
Expected: PASS — `Dashboard.test.jsx` não faz asserção sobre as classes de cor trocadas (confirmado por
busca prévia no arquivo, nenhum assert em `emerald`/`amber`/`red-400`/`blue-400`).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/dashboard/KpiCard.jsx frontend/src/components/dashboard/KpiCard.test.jsx frontend/src/pages/Dashboard.jsx
git commit -m "fix(design-system): KI-050 -- KpiCard e Dashboard usam tokens de tema (Light Mode legível)"
```

---

### Task 5: KI-050 — telas restantes (Reports, OperationalCosts, Garantias, Vendas, Users, VendaDetalhe, TiposGarantia)

**Files:**
- Modify: `frontend/src/pages/Reports.jsx:191,192,229,230,272,295,325`
- Modify: `frontend/src/pages/OperationalCosts.jsx:140,144,182`
- Modify: `frontend/src/pages/Garantias.jsx:10-12`
- Modify: `frontend/src/pages/Vendas.jsx:416-417`
- Modify: `frontend/src/pages/Users.jsx:109,145`
- Modify: `frontend/src/pages/VendaDetalhe.jsx:314`
- Modify: `frontend/src/pages/TiposGarantia.jsx:124`

Nenhum destes 7 arquivos tem teste que assert sobre as classes trocadas (confirmado por busca prévia em
todos os `*.test.jsx`); `Vendas.test.jsx` é o único teste que renderiza uma das telas tocadas — roda de
novo no Step 8 como guarda-corpo.

- [ ] **Step 1: `Reports.jsx` — `text-red-400` → `text-destructive`, `text-emerald-400` → `text-success`**

Substituir, nas 7 linhas (191, 192, 229, 230, 272, 295, 325 atuais):

```jsx
                        <td className="px-4 py-2 text-destructive">{formatCurrency(summary.gastos)}</td>
                        <td className="px-4 py-2 text-success font-medium">{formatCurrency(summary.lucro)}</td>
```
```jsx
                      <td className="px-4 py-3 text-destructive">{formatCurrency(summary.gastos)}</td>
                      <td className="px-4 py-3 text-success font-medium">{formatCurrency(summary.lucro)}</td>
```
```jsx
                        <td className="px-4 py-3 text-destructive font-medium">{formatCurrency(summary.total_valor)}</td>
```
```jsx
                      <span className="text-sm font-medium text-destructive">{formatCurrency(valor)}</span>
```
```jsx
                        <td className="px-4 py-3 text-destructive font-medium whitespace-nowrap">{formatCurrency(item.valor)}</td>
```

- [ ] **Step 2: `OperationalCosts.jsx` — `text-red-400` → `text-destructive`, `text-amber-400` → `text-warning`**

```jsx
          <p className="text-2xl font-bold text-destructive">{formatCurrency(total)}</p>
```
```jsx
          <p className="text-2xl font-bold text-warning">{formatCurrency(thisMonth)}</p>
```
```jsx
                    <td className="px-4 py-3 text-destructive font-medium">{formatCurrency(c.valor)}</td>
```

- [ ] **Step 3: `Garantias.jsx` — mapa de status**

Substituir o `map` (linhas 10-12 atuais):

```jsx
  const map = {
    vencida:   "bg-destructive/20 text-destructive border-destructive/30",
    vencendo:  "bg-warning/20 text-warning border-warning/30",
    ativa:     "bg-success/20 text-success border-success/30",
  };
```

- [ ] **Step 4: `Vendas.jsx` — confirmação de venda concluída**

Substituir (linhas 416-417 atuais):

```jsx
          <div className="mx-auto h-12 w-12 rounded-full bg-success/10 flex items-center justify-center">
            <Check className="h-6 w-6 text-success" />
          </div>
```

- [ ] **Step 5: `Users.jsx` — cor de perfil e badge ativo/inativo**

Substituir `perfilColor` (linha 109 atual) — `financeiro` fica com a classe Tailwind antiga
deliberadamente (ver Global Constraints e Task 6, KI-051 — não existe token semântico de roxo na paleta
Pulse):

```jsx
  // tecnico/vendedor/estoque migrados para tokens de tema (Fase 3.1, KI-050). "financeiro" fica
  // com a classe Tailwind antiga -- não existe token semântico de roxo na paleta Pulse; criar um
  // não está no escopo desta correção de bug. Registrado como KI-051 (não bloqueante).
  const perfilColor = { admin: "text-primary", tecnico: "text-info", vendedor: "text-success", estoque: "text-warning", financeiro: "text-purple-400" };
```

E o badge de status (linha 145 atual):

```jsx
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${u.ativo !== false ? "bg-success/20 text-success border-success/30" : "bg-destructive/20 text-destructive border-destructive/30"}`}>
```

- [ ] **Step 6: `VendaDetalhe.jsx` — borda do painel de cancelamento**

Substituir (linha 314 atual):

```jsx
        <div className="bg-card border border-destructive/30 rounded-xl p-4 space-y-3">
```

- [ ] **Step 7: `TiposGarantia.jsx` — badge ativo**

Substituir (linha 124 atual):

```jsx
                        t.ativo ? "bg-success/10 text-success border-success/30" : "bg-secondary/70 text-muted-foreground border-border",
```

- [ ] **Step 8: Rodar a suite completa do frontend e o lint**

Run: `npm run test && npm run lint`
Expected: PASS — 0 erros (os mesmos 2 warnings pré-existentes de `ShoppingList.jsx`/`Stock.jsx`, fora de
escopo, continuam os únicos).

- [ ] **Step 9: Commit**

```bash
git add frontend/src/pages/Reports.jsx frontend/src/pages/OperationalCosts.jsx frontend/src/pages/Garantias.jsx frontend/src/pages/Vendas.jsx frontend/src/pages/Users.jsx frontend/src/pages/VendaDetalhe.jsx frontend/src/pages/TiposGarantia.jsx
git commit -m "fix(design-system): KI-050 -- Reports/OperationalCosts/Garantias/Vendas/Users/VendaDetalhe/TiposGarantia usam tokens de tema"
```

---

### Task 6: Validação final, documentação e PR

**Files:**
- Modify: `docs/engineering/ENGINEERING_GUIDE.md` (nova seção 3.4)
- Modify: `docs/operations/PROJECT_STATUS.md`
- Modify: `docs/operations/CHANGELOG.md`
- Modify: `docs/operations/KNOWN_ISSUES.md` (KI-050 → Resolvido; novo KI-051)
- Modify: `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md:297` (linha da Fase 3.1 na
  tabela da seção 12)

- [ ] **Step 1: Rodar a suite completa e o lint uma última vez**

Run (a partir de `frontend/`): `npm run test && npm run lint`
Expected: PASS — 0 erros.

- [ ] **Step 2: Checklist manual no browser — Light/Dark nas 9 telas do KI-050**

Run: `npm run dev`, logar.

- [ ] Em Light Mode forçado (DevTools), abrir Dashboard, Relatórios, Custos Operacionais, Garantias,
  Vendas (concluir uma venda de teste), Usuários, uma Venda existente (detalhe), Tipos de Garantia —
  confirmar que os textos/badges antes coloridos com `emerald`/`amber`/`red`/`blue`-400 ficam legíveis
  (não "lavados") contra o fundo claro.
- [ ] Em Dark Mode, confirmar que a aparência permanece equivalente à anterior a este plano (mesmo peso de
  cor, agora vindo dos tokens).
- [ ] Abrir o Dashboard e conferir os 3 gráficos (Task 3) nos dois modos — grade/eixo legíveis em Light,
  aparência preservada em Dark.

- [ ] **Step 3: Adicionar a seção 3.4 em `ENGINEERING_GUIDE.md`**

Em `docs/engineering/ENGINEERING_GUIDE.md`, logo após o fim da seção 3.3 (antes de `## 4. Padrões
Frontend`), adicionar:

```markdown
## 3.4 Fluxoly Design System (Fase 3.1 — Foundation v2)

Formalizado em `docs/engineering/plans/PLAN-design-system-fase3.1-foundation-v2.md`. Evolui a Foundation
da Fase 2 (seção 3.3) para os dois modos de tema (Light+Dark, infra da Fase 3.0) — novos recipientes de
composição, `DataTable` real e tema único de gráfico — **sem redesenhar nenhuma tela** (mesmo princípio da
Fase 2), exceto a correção pontual do KI-050 (troca de classe de cor, não de composição).

### Recipientes de composição (`components/ui/panel.jsx`, `list-block.jsx`, `loose-metric.jsx`)

`Card` deixa de ser o recipiente universal — vira 1 de 4 possíveis, conforme o peso do conteúdo (spec §7):

- **`Panel`** — dominante: borda + sombra, para o único elemento de maior peso de cada tela.
- **`ListBlock`/`ListBlockItem`** — bloco de lista: sem moldura própria, só divisor sutil entre linhas.
- **`LooseMetric`** — métrica solta: número + rótulo, sem moldura nenhuma.
- **`Card`** (já existente) — segue disponível para o caso genérico/elemento flutuante (dropdown/popover
  via Radix), não descontinuado.

Nenhum dos 3 recipientes novos usa o prefixo `dark:` do Tailwind — este projeto não usa esse variant para
tema (ver `index.css`, Fase 3.0); toda diferença visual entre modos vem só de `--color-*`.

### `DataTable` (`components/ui/data-table.jsx`)

Tabela real, substituindo o padrão de HTML cru com bordas manuais repetido por arquivo. `stickyHeader`
(header fixo em listas longas) e `onRowClick` (linha clicável, com suporte a teclado via `Enter`) são
opcionais. Migração de tabelas existentes para `DataTable` é escopo das Fases 3.2+, tela a tela — este
componente só existe a partir da Fase 3.1, ainda não é usado em nenhuma página.

### Tema de gráfico (`lib/chart-theme.js`)

Recharts recebe cor via prop SVG (`stroke`/`fill`), não via classe Tailwind — `chart-theme.js` centraliza
os valores (`var(--color-*)`) para que todo gráfico reaja à troca de tema automaticamente, sem
sincronização manual. `chartColor(index)` cicla a paleta categórica (`--color-chart-1..5`).

### KI-050 — telas hardcoded migradas para tokens de tema

As 9 telas identificadas na revisão final da Fase 3.0 (`KpiCard.jsx`, `Dashboard.jsx`, `Reports.jsx`,
`OperationalCosts.jsx`, `Garantias.jsx`, `Vendas.jsx`, `Users.jsx`, `VendaDetalhe.jsx`,
`TiposGarantia.jsx`) foram migradas de classes Tailwind cruas (`text-emerald-400` etc., calibradas só para
Dark Mode) para os tokens semânticos já existentes (`text-success`/`warning`/`destructive`/`info`).
Exceção registrada: o papel "financeiro" em `Users.jsx` (`text-purple-400`) não tem token semântico
equivalente na paleta Pulse — ver KI-051.
```

- [ ] **Step 4: Atualizar `docs/operations/PROJECT_STATUS.md`**

Adicionar nova seção logo acima de "## ✅ Fase 3.0 do Fluxoly Design System" (mesmo formato das seções
anteriores):

```markdown
## ✅ Fase 3.1 do Fluxoly Design System — Foundation v2 ENCERRADA (PR #<número real> mergeado)

**Ver `docs/engineering/plans/PLAN-design-system-fase3.1-foundation-v2.md` para o registro completo e
`docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (seção 12) para o faseamento
completo da Fase 3.**

<data>. Segunda fatia da Fase 3, sequência imediata à infraestrutura de tema (3.0). Escopo: recipientes de
composição (`Panel`/`ListBlock`/`LooseMetric`, substituindo `Card` como recipiente universal), `DataTable`
real, tema único de gráfico (Recharts) e a correção do KI-050 (9 telas com cor hardcoded, ilegível em
Light Mode). Nenhuma tela redesenhada — migração de composição das telas é Fase 3.2+.

**Entregue** (branch `feat/design-system-fase3.1-foundation-v2`):
- `Panel`/`PanelHeader`/`PanelTitle`/`PanelDescription`/`PanelContent`, `ListBlock`/`ListBlockItem`,
  `LooseMetric` — novos em `components/ui/`, ainda não usados por nenhuma página.
- `DataTable` — tabela real da Foundation (header sticky opcional, linha clicável com suporte a teclado),
  ainda não usada por nenhuma página.
- `lib/chart-theme.js` — tema único (`var(--color-*)`) para os 3 gráficos do Dashboard
  (`RevenueChartCard`/`ServicesChartCard`/`TechnicianProfitChartCard`), que antes usavam cor SVG fixa
  (hex/hsl) sem relação com o tema nem com a marca.
- KI-050 resolvido — `KpiCard.jsx`/`Dashboard.jsx`/`Reports.jsx`/`OperationalCosts.jsx`/`Garantias.jsx`/
  `Vendas.jsx`/`Users.jsx`/`VendaDetalhe.jsx`/`TiposGarantia.jsx` migrados de classe Tailwind crua para os
  tokens de tema (`text-success`/`warning`/`destructive`/`info`). Exceção: papel "financeiro" em
  `Users.jsx` sem token de roxo equivalente — registrado como KI-051.

**Validação:** suíte completa passando, lint 0 erros, checklist manual em navegador real (Light Mode/Dark
Mode) nas 9 telas do KI-050 e nos 3 gráficos.

**Decisão do CTO:** aprovado. Mergeado em `main`.

**Próximo passo:** Fase 3.2 (Vitrine — Dashboard + Login + Shell/Sidebar + harmonização da Landing).
```

(Preencher `<número real>`/`<data>` no momento do merge — não são placeholders de plano, são valores que só
existem depois do PR real.)

- [ ] **Step 5: Atualizar `docs/operations/CHANGELOG.md`**

Adicionar entrada no topo de `## [Não lançado]`:

```markdown
### Adicionado (<data> — Fase 3.1 do Fluxoly Design System, Foundation v2)
- **Recipientes de composição** `Panel`/`ListBlock`/`LooseMetric` em `components/ui/` — evoluem `Card`
  como recipiente universal (dominante/bloco de lista/métrica solta), ainda não usados em nenhuma página.
- **`DataTable`** real da Foundation (header sticky opcional, linha clicável com suporte a teclado).
- **Tema único de gráfico** (`lib/chart-theme.js`) — os 3 gráficos do Dashboard passam a usar
  `var(--color-*)` em vez de cor SVG fixa, reagindo à troca de tema.
- **KI-050 resolvido** — 9 telas migradas de classe Tailwind crua para tokens de tema
  (`text-success`/`warning`/`destructive`/`info`).
- Ver `docs/engineering/plans/PLAN-design-system-fase3.1-foundation-v2.md` para o registro completo.
```

- [ ] **Step 6: Atualizar `docs/operations/KNOWN_ISSUES.md`**

Mover o bloco `## KI-050` para o padrão de resolvido (`## ~~KI-050~~ — RESOLVIDO`), adicionando ao final
do bloco existente:

```markdown
**Resolvido em <data>** (Fase 3.1, `PLAN-design-system-fase3.1-foundation-v2.md`, Tasks 4-5) — as 9 telas
migradas para os tokens de tema (`text-success`/`warning`/`destructive`/`info`). Exceção: o papel
"financeiro" em `Users.jsx` não tem token semântico de roxo equivalente na paleta Pulse — registrado
separadamente como KI-051 (não bloqueante).
```

E adicionar um novo bloco ao final do arquivo:

```markdown
## KI-051

Descrição:
`Users.jsx` (`perfilColor`, papel "financeiro") usa `text-purple-400` (Tailwind cru) para diferenciar o
perfil de usuário "financeiro" na lista de usuários. Ao corrigir o KI-050 (Fase 3.1), os outros 3 papéis
(`tecnico`/`vendedor`/`estoque`) foram migrados para tokens de tema já existentes (`info`/`success`/
`warning`) — "financeiro" não tem equivalente: os 4 tokens semânticos da paleta Pulse (destructive/
success/warning/info) não incluem roxo, e criar um token novo não é escopo de uma correção de bug.

Impacto:
Mesmo impacto de contraste do KI-050 original (calibrado só para Dark Mode, ~baixo contraste em Light
Mode), mas isolado a 1 célula de 1 tela — a lista de usuários já é uma tela administrativa de baixo
tráfego (Tier 4, `PLAN-design-system-fase3-visual-experience.md` §9).

Status:
Aberto — decisão de produto pendente: adicionar um 5º token semântico à paleta (decisão de marca, CTO) ou
remover a diferenciação de cor por papel (mudança de composição, fora de escopo de correção de bug).

Sprint prevista:
Sem sprint — fica para quando a Fase 3.2+ tocar `Users.jsx` diretamente, ou decisão isolada do CTO.

Responsável:
—
```

- [ ] **Step 7: Atualizar a tabela de faseamento do plano de Fase 3**

Em `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md`, seção 12, a linha da Fase 3.1
passa de descrição de escopo para `✅ Concluído -- PR #<número real do PR>, <data do merge>`.

- [ ] **Step 8: Commit da documentação**

```bash
git add docs/engineering/ENGINEERING_GUIDE.md docs/operations/PROJECT_STATUS.md docs/operations/CHANGELOG.md docs/operations/KNOWN_ISSUES.md docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md
git commit -m "docs(design-system): registrar conclusão da Fase 3.1 (Foundation v2, KI-050 resolvido)"
```

- [ ] **Step 9: Push e abrir o PR**

```bash
git push -u origin feat/design-system-fase3.1-foundation-v2
gh pr create --title "feat(design-system): Fase 3.1 — Foundation v2" --body "$(cat <<'EOF'
## Resumo
- Recipientes de composição Panel/ListBlock/LooseMetric (components/ui/) -- ainda não usados em nenhuma página
- DataTable real da Foundation (header sticky, linha clicável) -- ainda não usada em nenhuma página
- Tema único de gráfico (lib/chart-theme.js) -- os 3 gráficos do Dashboard reagem a Light/Dark
- KI-050 resolvido -- 9 telas migradas de cor Tailwind crua para tokens de tema
- KI-051 registrado (não bloqueante) -- papel "financeiro" em Users.jsx sem token de roxo equivalente
- Nenhuma tela redesenhada -- só Foundation + correção de bug (KI-050)

## Plano
docs/engineering/plans/PLAN-design-system-fase3.1-foundation-v2.md

## Test plan
- [x] Suite de testes completa (frontend) passando
- [x] Lint sem erros
- [x] Checklist manual: Light Mode e Dark Mode nas 9 telas do KI-050 e nos 3 gráficos do Dashboard
EOF
)"
```

Aguardar CI verde antes de considerar mergeável (protocolo padrão do repositório — não fazer merge sem
aprovação, ver `CLAUDE.md`).

---

## Self-Review

**Cobertura da spec:** §7 (evolução de componentes: Card→Painel/Bloco/Métrica solta em Task 1, Badge/
EmptyState/ErrorState/LoadingState já dual-mode desde a Fase 3.0 sem mudança necessária, Tabela→DataTable
em Task 2, Gráficos→tema único em Task 3) → todas as linhas da tabela cobertas exceto "Button/Input/Select
mantém API, evolui só skin" (já resolvido estruturalmente pela Fase 3.0 — esses componentes só usam
classes de token, não Tailwind cru, nenhuma ação necessária nesta fase, por isso não tem task própria).
KI-050 → Tasks 4-5 (33 ocorrências nas 9 telas, cobertura 32/33 — a exceção documentada e justificada no
Global Constraints e formalizada como KI-051 na Task 6). §12 linha 3.1 integralmente coberta.

**Placeholders:** nenhum "TBD"/"implementar depois" — todo step tem código completo ou comando exato. Os
únicos valores entre `<>` (número do PR, data do merge) não são placeholders de plano — são preenchidos
depois que o PR real existe, mesmo padrão da Task 6 do plano da Fase 3.0.

**Consistência de tipos/nomes:** `chartColor(index)`/`CHART_PALETTE`/`CHART_GRID_STROKE`/`CHART_AXIS_TICK`/
`CHART_CURSOR_STROKE` (Task 3) usados identicamente nas 3 modificações de chart card da mesma task.
`DataTable({ columns, rows, getRowKey, stickyHeader, onRowClick, className })` (Task 2) — nomes de prop
únicos, sem uso em nenhuma outra task (não migrado a nenhuma página nesta fase). `Panel`/`PanelHeader`/
`PanelTitle`/`PanelDescription`/`PanelContent` (Task 1) seguem exatamente o mesmo padrão de nomes de
`Card`/`CardHeader`/`CardTitle`/`CardDescription`/`CardContent` já existente. Tokens de cor
(`text-success`/`warning`/`destructive`/`info`) idênticos entre Tasks 4 e 5 e a seção nova do
`ENGINEERING_GUIDE.md` (Task 6) — mesmos 4 nomes em todo lugar.
