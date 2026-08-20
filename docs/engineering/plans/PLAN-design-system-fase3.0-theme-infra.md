# Fase 3.0 — Infraestrutura de Tema (Light Mode + Dark Mode) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao Fluxoly uma infraestrutura real de tema — tokens de cor para Light Mode e Dark Mode em
`index.css`, um `ThemeProvider`/`useTheme()` React, um toggle de 3 estados (automático/claro/escuro) na
Sidebar, e persistência da preferência — sem mudar a composição visual de nenhuma tela.

**Architecture:** Tailwind v4 já expõe os tokens de marca como custom properties CSS via `@theme` em
`frontend/src/index.css`; a estratégia é reescrever esse bloco com os valores de **Light Mode como base**,
e sobrescrever para **Dark Mode** em duas camadas — `@media (prefers-color-scheme: dark)` (segue o SO por
padrão) e `:root[data-theme="dark"]`/`[data-theme="light"]` (override explícito do usuário, que sempre
vence). Um `ThemeContext` React gerencia o estado (`'system' | 'light' | 'dark'`), persiste em
`localStorage` e aplica/remove o atributo `data-theme` em `<html>`. Um pequeno script inline em
`index.html`, executado antes do primeiro paint, aplica um override salvo imediatamente — evita flash da
cor errada ao recarregar a página. Nenhum componente de UI muda de composição; só os tokens de cor por
trás deles.

**Tech Stack:** React 19, Tailwind CSS v4 (`@theme`, tokens `@color-*` viram custom properties CSS puras),
Vite 8, Vitest 4 + Testing Library (jsdom).

**Spec:** `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (seções 0.2 "Direção de
Identidade Escolhida — Pulse", 3 "Light Mode", 4 "Dark Mode", 12 "Plano de implementação", linha da Fase
3.0); `docs/company/BRAND_IDENTITY.md` §10 (paleta decidida). Este plano implementa exatamente a linha
3.0 da tabela de faseamento — nenhuma tela é redesenhada aqui (isso é Fase 3.1+).

## Global Constraints

- Identidade de marca já decidida (não é decisão deste plano): cor de assinatura `#FF3D5A`, 2º acento
  (ciano "fluxo ao vivo") `#29E0C9` dark / `#1BA396` light (variante recalibrada para contraste em fundo
  claro) — `docs/company/BRAND_IDENTITY.md` §10.3.
- Nenhum componente visual muda de composição/layout nesta fase — só tokens de cor e a infraestrutura que
  os liga ao tema. Ver `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` §12, linha
  3.0: "Nenhum componente visual muda ainda — só a infraestrutura, testável isolada."
- Preferência de tema segue o sistema operacional por padrão (`prefers-color-scheme`), com override manual
  salvo — decisão já registrada em `PLAN-design-system-fase3-visual-experience.md` §14, item 1.
  `localStorage` key: `fluxoly-theme`, valores `'system' | 'light' | 'dark'`.
- Cores semânticas de estado (destructive/success/warning/info) usadas como **texto** sobre um fundo tintado
  a 10% de opacidade (`badge.jsx`: `bg-success/10 text-success`), não como preenchimento sólido — logo o
  contraste que precisa passar WCAG AA (≥4.5:1) é *texto-vs-fundo-claro real*, não texto-vs-cor-sólida.
- Zero mudança de lógica de negócio, API, schema ou permissões — escopo 100% frontend/apresentação
  (`frontend/src/`).
- Testes isolados, nenhum toca `database.db` (não aplicável aqui — não há backend envolvido).
- Conventional Commits (`feat:`, `test:`, `fix:`, `docs:`); branch `feat/design-system-fase3.0-theme-infra`.

---

### Task 1: `ThemeContext` — estado de tema, persistência e resolução do preferência do sistema

**Files:**
- Create: `frontend/src/contexts/ThemeContext.jsx`
- Test: `frontend/src/contexts/ThemeContext.test.jsx`

**Interfaces:**
- Produces: `ThemeProvider({ children })` (componente React); `useTheme()` retornando
  `{ theme: 'system'|'light'|'dark', resolvedTheme: 'light'|'dark', setTheme: (next) => void }`.
  `setTheme` só aceita um dos 3 valores válidos (chamada com outro valor é ignorada, sem erro).
  Consumido pelas Tasks 4 e 5.

- [ ] **Step 1: Criar a branch de feature**

```bash
git checkout main
git pull
git checkout -b feat/design-system-fase3.0-theme-infra
```

- [ ] **Step 2: Escrever o teste (falhando) do `ThemeContext`**

Criar `frontend/src/contexts/ThemeContext.test.jsx`:

```jsx
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider, useTheme } from "./ThemeContext";

function Probe() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button onClick={() => setTheme("light")}>light</button>
      <button onClick={() => setTheme("dark")}>dark</button>
      <button onClick={() => setTheme("system")}>system</button>
    </div>
  );
}

function renderProbe() {
  return render(
    <ThemeProvider>
      <Probe />
    </ThemeProvider>
  );
}

describe("ThemeContext", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("usa 'system' como padrão quando não há preferência salva", () => {
    renderProbe();
    expect(screen.getByTestId("theme")).toHaveTextContent("system");
  });

  it("resolve para 'light' quando o sistema não prefere dark (stub padrão do jsdom)", () => {
    renderProbe();
    expect(screen.getByTestId("resolved")).toHaveTextContent("light");
  });

  it("lê uma preferência já salva no localStorage ao montar", () => {
    localStorage.setItem("fluxoly-theme", "dark");
    renderProbe();
    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
    expect(screen.getByTestId("resolved")).toHaveTextContent("dark");
  });

  it("ignora um valor inválido salvo no localStorage e usa 'system'", () => {
    localStorage.setItem("fluxoly-theme", "roxo");
    renderProbe();
    expect(screen.getByTestId("theme")).toHaveTextContent("system");
  });

  it("setTheme('dark') persiste no localStorage e aplica data-theme='dark' no <html>", async () => {
    renderProbe();
    const user = userEvent.setup();
    await user.click(screen.getByText("dark"));

    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
    expect(screen.getByTestId("resolved")).toHaveTextContent("dark");
    expect(localStorage.getItem("fluxoly-theme")).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("setTheme('system') remove o atributo data-theme do <html>", async () => {
    renderProbe();
    const user = userEvent.setup();
    await user.click(screen.getByText("dark"));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    await user.click(screen.getByText("system"));
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
    expect(localStorage.getItem("fluxoly-theme")).toBe("system");
  });

  it("reage a uma mudança de preferência do sistema quando theme='system'", () => {
    let changeHandler;
    const mql = {
      matches: false,
      media: "(prefers-color-scheme: dark)",
      addEventListener: (_event, handler) => { changeHandler = handler; },
      removeEventListener: () => {},
    };
    const originalMatchMedia = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue(mql);

    renderProbe();
    expect(screen.getByTestId("resolved")).toHaveTextContent("light");

    act(() => {
      mql.matches = true;
      changeHandler({ matches: true });
    });

    expect(screen.getByTestId("resolved")).toHaveTextContent("dark");
    window.matchMedia = originalMatchMedia;
  });

  it("useTheme() fora do ThemeProvider lança erro", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Probe />)).toThrow("useTheme deve ser usado dentro de ThemeProvider");
    consoleError.mockRestore();
  });
});
```

- [ ] **Step 3: Rodar os testes e confirmar que falham** (o módulo ainda não existe)

Run (a partir de `frontend/`): `npm run test -- src/contexts/ThemeContext.test.jsx`
Expected: FAIL — `Failed to resolve import "./ThemeContext"`.

- [ ] **Step 4: Implementar `ThemeContext.jsx`**

Criar `frontend/src/contexts/ThemeContext.jsx`:

```jsx
import { createContext, useCallback, useContext, useEffect, useState } from "react";

const STORAGE_KEY = "fluxoly-theme";
const VALID_THEMES = ["system", "light", "dark"];

const ThemeContext = createContext(null);

function readStoredTheme() {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return VALID_THEMES.includes(stored) ? stored : "system";
  } catch {
    // localStorage indisponível (modo privado, quota, etc.) -- preferência só dura a sessão atual.
    return "system";
  }
}

function getSystemPrefersDark() {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolveTheme(theme, systemPrefersDark) {
  return theme === "system" ? (systemPrefersDark ? "dark" : "light") : theme;
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readStoredTheme);
  const [systemPrefersDark, setSystemPrefersDark] = useState(getSystemPrefersDark);

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return;
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (event) => setSystemPrefersDark(event.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  const resolvedTheme = resolveTheme(theme, systemPrefersDark);

  useEffect(() => {
    if (theme === "system") {
      document.documentElement.removeAttribute("data-theme");
    } else {
      document.documentElement.setAttribute("data-theme", theme);
    }
  }, [theme]);

  const setTheme = useCallback((next) => {
    if (!VALID_THEMES.includes(next)) return;
    setThemeState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // localStorage indisponível -- a mudança ainda se aplica nesta sessão via estado do React.
    }
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme deve ser usado dentro de ThemeProvider");
  return ctx;
}
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `npm run test -- src/contexts/ThemeContext.test.jsx`
Expected: PASS (9 testes).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/contexts/ThemeContext.jsx frontend/src/contexts/ThemeContext.test.jsx
git commit -m "feat(design-system): ThemeContext com persistência e preferência do sistema"
```

---

### Task 2: Utilitário de contraste WCAG + constantes semânticas do Light Mode

**Why this task exists:** as 4 cores semânticas atuais (`destructive`/`success`/`warning`/`info`) foram
calibradas só para fundo escuro. Testadas matematicamente contra um fundo claro (`#FFFFFF`), todas ficam
abaixo do mínimo WCAG AA de 4,5:1 para texto (contraste medido: destructive 3.38:1, success 2.52:1,
warning 1.84:1, info 3.26:1) — exatamente o alerta já registrado em
`PLAN-design-system-fase3-visual-experience.md` §3, linha "estados". Este task recalibra as 4 (mesmo tom/
matiz, luminosidade reduzida) e trava o resultado com um teste automatizado.

**Files:**
- Create: `frontend/src/lib/contrast.js`
- Create: `frontend/src/lib/contrast.test.js`
- Create: `frontend/src/lib/theme-tokens.js`
- Create: `frontend/src/lib/theme-tokens.test.js`

**Interfaces:**
- Produces: `contrastRatio(hexA, hexB) => number` (razão de contraste WCAG, 1 a 21); `LIGHT_SURFACE`
  (string, `"#FFFFFF"`) e `LIGHT_SEMANTIC` (objeto `{ destructive, success, warning, info }`, valores hex)
  de `theme-tokens.js`. Consumidos pela Task 3 (os hex literais em `index.css` devem ser copiados
  manualmente destas constantes — Tailwind v4 `@theme` não importa constantes JS, então a sincronia é
  documentada, não automática).

- [ ] **Step 1: Escrever o teste (falhando) de `contrastRatio`**

Criar `frontend/src/lib/contrast.test.js`:

```js
import { describe, it, expect } from "vitest";
import { contrastRatio } from "./contrast";

describe("contrastRatio", () => {
  it("preto sobre branco tem contraste 21:1 (referência WCAG)", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 0);
  });

  it("mesma cor tem contraste 1:1", () => {
    expect(contrastRatio("#336699", "#336699")).toBeCloseTo(1, 5);
  });

  it("é simétrico -- ordem dos argumentos não importa", () => {
    const a = contrastRatio("#1F7A50", "#FFFFFF");
    const b = contrastRatio("#FFFFFF", "#1F7A50");
    expect(a).toBeCloseTo(b, 5);
  });
});
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `npm run test -- src/lib/contrast.test.js`
Expected: FAIL — `Failed to resolve import "./contrast"`.

- [ ] **Step 3: Implementar `contrast.js`**

Criar `frontend/src/lib/contrast.js`:

```js
function srgbChannelToLinear(channel255) {
  const c = channel255 / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  const value = normalized.length === 3
    ? normalized.split("").map((ch) => ch + ch).join("")
    : normalized;
  const num = parseInt(value, 16);
  return { r: (num >> 16) & 255, g: (num >> 8) & 255, b: num & 255 };
}

function relativeLuminance(hex) {
  const { r, g, b } = hexToRgb(hex);
  return (
    0.2126 * srgbChannelToLinear(r) +
    0.7152 * srgbChannelToLinear(g) +
    0.0722 * srgbChannelToLinear(b)
  );
}

/** Razão de contraste WCAG 2.x entre duas cores hex (#RGB ou #RRGGBB). Retorna de 1 a 21. */
export function contrastRatio(hexA, hexB) {
  const lumA = relativeLuminance(hexA);
  const lumB = relativeLuminance(hexB);
  const lighter = Math.max(lumA, lumB);
  const darker = Math.min(lumA, lumB);
  return (lighter + 0.05) / (darker + 0.05);
}
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `npm run test -- src/lib/contrast.test.js`
Expected: PASS (3 testes).

- [ ] **Step 5: Escrever o teste (falhando) das constantes semânticas**

Criar `frontend/src/lib/theme-tokens.test.js`:

```js
import { describe, it, expect } from "vitest";
import { contrastRatio } from "./contrast";
import { LIGHT_SURFACE, LIGHT_SEMANTIC } from "./theme-tokens";

const AA_NORMAL_TEXT_MIN = 4.5;

describe("cores semânticas do Light Mode -- WCAG AA", () => {
  it.each(Object.entries(LIGHT_SEMANTIC))(
    "%s (%s) passa AA >= 4.5:1 contra a superfície clara",
    (_name, hex) => {
      expect(contrastRatio(hex, LIGHT_SURFACE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT_MIN);
    }
  );
});
```

- [ ] **Step 6: Rodar e confirmar que falha**

Run: `npm run test -- src/lib/theme-tokens.test.js`
Expected: FAIL — `Failed to resolve import "./theme-tokens"`.

- [ ] **Step 7: Implementar `theme-tokens.js`**

Criar `frontend/src/lib/theme-tokens.js`:

```js
// Cores semânticas do Light Mode, recalibradas para WCAG AA (Fase 3.0 -- ver
// docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md secao 3). Mesmo
// matiz (hue) das versões de Dark Mode já em produção, luminosidade reduzida até passar
// 4.5:1 contra fundo/superfície claros (badge.jsx usa essas cores como texto direto sobre
// um fundo tintado a 10% de opacidade -- o par que precisa passar é texto-vs-branco).
//
// Estas constantes são a fonte de verdade do CÁLCULO de contraste (testado em
// theme-tokens.test.js). Os valores literais equivalentes em frontend/src/index.css
// (bloco @media (prefers-color-scheme: dark) e :root[data-theme="dark"] usam os valores
// ORIGINAIS, inalterados -- só o Light Mode precisava de recalibração) precisam ser
// mantidos manualmente em sincronia com este arquivo -- Tailwind v4 (@theme) não importa
// constantes JS em tempo de build.
export const LIGHT_SURFACE = "#FFFFFF";

export const LIGHT_SEMANTIC = {
  destructive: "#BD290F",
  success: "#1F7A50",
  warning: "#9B6508",
  info: "#0F61B3",
};
```

- [ ] **Step 8: Rodar e confirmar que passa**

Run: `npm run test -- src/lib/theme-tokens.test.js`
Expected: PASS (4 testes, um por cor).

- [ ] **Step 9: Commit**

```bash
git add frontend/src/lib/contrast.js frontend/src/lib/contrast.test.js frontend/src/lib/theme-tokens.js frontend/src/lib/theme-tokens.test.js
git commit -m "test(design-system): utilitário de contraste WCAG + recalibração das cores semânticas do Light Mode"
```

---

### Task 3: Restruturar `index.css` — tokens Light (base) + Dark (overrides)

**Files:**
- Modify: `frontend/src/index.css` (linhas 1–139, arquivo inteiro)

**Interfaces:**
- Consumes: `LIGHT_SEMANTIC`/`LIGHT_SURFACE` de `frontend/src/lib/theme-tokens.js` (Task 2) — os hex são
  copiados manualmente para o CSS, não importados (ver nota na Task 2).
- Produces: os mesmos nomes de token que já existem hoje (`--color-background`, `--color-primary`, etc.)
  continuam existindo com os mesmos nomes — nenhuma classe Tailwind (`bg-background`, `text-primary`...)
  muda de nome, só o valor resolvido em cada tema. Consumido implicitamente por todo componente que já usa
  essas classes (nenhuma mudança de código nos componentes nesta fase).

Este task não tem teste automatizado (cascata CSS real + `@media (prefers-color-scheme)` não são
observáveis de forma confiável via `getComputedStyle` em jsdom/Vitest sem carregar CSS externo, e os
componentes React não mudam nesta fase) — a validação é o Step 3 (checklist manual no browser).

- [ ] **Step 1: Substituir o conteúdo de `frontend/src/index.css`**

Conteúdo completo do arquivo (Light Mode como base em `@theme`; Dark Mode nas duas camadas de override —
`@media (prefers-color-scheme: dark)` guardado por `:not([data-theme="light"])`, e `:root[data-theme="dark"]`
explícito, deliberadamente duplicados: são dois gatilhos independentes, não uma duplicação por engano):

```css
@import "tailwindcss";

/* Fluxoly brand palette -- direção "Pulse" (docs/company/BRAND_IDENTITY.md #10, decidida
   2026-08-20). Light Mode é a base deste bloco @theme; Dark Mode sobrescreve mais abaixo.
   Valores em hex (não hsl como antes desta fase) para rastreabilidade direta com os
   artboards de identidade decididos -- ver canvas "Fluxoly Identity Directions" e
   docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md secoes 0.2/3/4. */
@theme {
  --color-background: #F5F6FA;
  --color-foreground: #10121A;

  --color-card: #FFFFFF;
  --color-card-foreground: #10121A;

  --color-popover: #FFFFFF;
  --color-popover-foreground: #10121A;

  /* Fluxoly Pulse -- vermelho-sinal (substitui #FF0125 da identidade anterior) */
  --color-primary: #FF3D5A;
  --color-primary-foreground: #FFFFFF;

  --color-secondary: #ECEEF3;
  --color-secondary-foreground: #10121A;

  --color-muted: #ECEEF3;
  --color-muted-foreground: #5B6178;

  --color-accent: #ECEEF3;
  --color-accent-foreground: #10121A;

  /* Recalibrado para WCAG AA (>= 4.5:1) contra fundo claro -- ver
     frontend/src/lib/theme-tokens.js (fonte de verdade do cálculo, testada) e
     PLAN-design-system-fase3.0-theme-infra.md Task 2. Mesmo matiz das versões de Dark
     Mode abaixo, luminosidade reduzida. */
  --color-destructive: #BD290F;
  --color-destructive-foreground: #FFFFFF;

  --color-success: #1F7A50;
  --color-success-foreground: #FFFFFF;

  --color-warning: #9B6508;
  --color-warning-foreground: #FFFFFF;

  --color-info: #0F61B3;
  --color-info-foreground: #FFFFFF;

  --color-border: #E4E7EF;
  --color-input: #ECEEF3;
  --color-ring: #FF3D5A;

  /* Sidebar é intencionalmente invariante entre temas (sempre escura) -- decisão de escopo
     desta fase (3.0 é só infraestrutura), não um princípio permanente: a composição do
     Shell/Sidebar é Fase 3.2 (Vitrine), que pode revisitar isso. */
  --color-sidebar: #0A0A0A;
  --color-sidebar-foreground: #EBEBEB;
  --color-sidebar-primary: #FF3D5A;
  --color-sidebar-primary-foreground: #FFFFFF;
  --color-sidebar-accent: #1A1A1A;
  --color-sidebar-accent-foreground: #F5F5F5;
  --color-sidebar-border: #242424;
  --color-sidebar-ring: #FF3D5A;

  /* Gráficos também invariantes por enquanto -- tema único de gráfico (Recharts) é Fase
     3.1 (Foundation v2), não infraestrutura de tema. chart-1 e chart-5 atualizados só para
     sincronizar com a identidade Pulse já decidida; chart-2/3/4 sem mudança. */
  --color-chart-1: #FF3D5A;
  --color-chart-2: hsl(160 60% 45%);
  --color-chart-3: hsl(38 92% 50%);
  --color-chart-4: hsl(280 65% 60%);
  --color-chart-5: #29E0C9;

  --animate-accordion-down: accordion-down 200ms ease-out;
  --animate-accordion-up: accordion-up 200ms ease-out;
}

@keyframes accordion-down {
  from { height: 0; }
  to { height: var(--radix-accordion-content-height); }
}

@keyframes accordion-up {
  from { height: var(--radix-accordion-content-height); }
  to { height: 0; }
}

/* Dark Mode -- segue a preferência do sistema por padrão; [data-theme="dark"] força
   independente do SO; [data-theme="light"] força claro mesmo com SO escuro (por isso o
   :not() abaixo). Ver PLAN-design-system-fase3-visual-experience.md secao 0.2/4. As duas
   camadas repetem as mesmas declarações de propósito -- gatilhos independentes (preferência
   do sistema vs. override explícito), não um copy-paste para "DRY-ficar". */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --color-background: #0B0D12;
    --color-foreground: #EDEFF5;
    --color-card: #14171F;
    --color-card-foreground: #EDEFF5;
    --color-popover: #1C202B;
    --color-popover-foreground: #EDEFF5;
    --color-secondary: #1C202B;
    --color-secondary-foreground: #EDEFF5;
    --color-muted: #1C202B;
    --color-muted-foreground: #8B90A3;
    --color-accent: #1C202B;
    --color-accent-foreground: #EDEFF5;
    --color-destructive: #F9502C;
    --color-success: #33B884;
    --color-warning: #F7B312;
    --color-warning-foreground: hsl(30 15% 10%);
    --color-info: #3D8FF5;
    --color-border: #232733;
    --color-input: #1C202B;
  }
}

:root[data-theme="dark"] {
  --color-background: #0B0D12;
  --color-foreground: #EDEFF5;
  --color-card: #14171F;
  --color-card-foreground: #EDEFF5;
  --color-popover: #1C202B;
  --color-popover-foreground: #EDEFF5;
  --color-secondary: #1C202B;
  --color-secondary-foreground: #EDEFF5;
  --color-muted: #1C202B;
  --color-muted-foreground: #8B90A3;
  --color-accent: #1C202B;
  --color-accent-foreground: #EDEFF5;
  --color-destructive: #F9502C;
  --color-success: #33B884;
  --color-warning: #F7B312;
  --color-warning-foreground: hsl(30 15% 10%);
  --color-info: #3D8FF5;
  --color-border: #232733;
  --color-input: #1C202B;
}

@layer base {
  *,
  ::before,
  ::after {
    /* Antes desta fase: hsl(222 47% 19%) hardcoded -- um azul-marinho que não correspondia
       a nenhum token da marca (nem ao --color-border antigo, hsl(0 0% 20%)). Corrigido para
       reagir ao tema junto com o resto -- já estava errado antes desta fase, exposto ao
       tornar todo o resto deste bloco theme-aware. */
    border-color: var(--color-border);
    box-sizing: border-box;
  }

  html {
    height: 100%;
  }

  body {
    background-color: var(--color-background);
    color: var(--color-foreground);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    margin: 0;
    min-height: 100%;
  }

  #root {
    width: 100%;
    min-height: 100vh;
    text-align: left;
  }

  h1, h2, h3, h4, h5, h6 {
    margin: 0;
  }

  p {
    margin: 0;
  }

  input, textarea, select {
    outline: none;
  }
}

.font-wordmark {
  font-family: "Onest", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-weight: 700;
}

/* UX-001 -- Preservação de Contexto da Navegação: destaque temporário do
   registro restaurado ao voltar de uma edição/detalhe (ver useListContext.js).
   Cor sincronizada com --color-primary (Pulse, #FF3D5A) -- antes desta fase usava o
   vermelho antigo (#FF0125) hardcoded. */
@keyframes nav-context-pulse {
  from { background-color: rgb(255 61 90 / 18%); }
  to { background-color: transparent; }
}

.nav-context-highlight {
  animation: nav-context-pulse 2s ease-out;
}
```

- [ ] **Step 2: Rodar a suite completa do frontend para garantir que nada quebrou**

Run: `npm run test`
Expected: PASS -- todos os testes existentes continuam passando (nenhum deles depende do valor exato de
uma cor; os que verificam classes Tailwind como `bg-sidebar-primary`, ex. `Layout.test.jsx`, continuam
passando porque o NOME da classe não mudou, só o valor resolvido).

- [ ] **Step 3: Checklist manual no browser (Light Mode não existe hoje -- primeira vez que fica visível)**

Run: `npm run dev`, abrir `http://localhost:5173` no navegador.

- [ ] Com o SO em modo claro (ou forçando via DevTools > Rendering > "prefers-color-scheme: light"),
  confirmar que o Dashboard renderiza com fundo `#F5F6FA`, cards brancos, texto escuro legível.
- [ ] Forçar DevTools para "prefers-color-scheme: dark" e confirmar que o app permanece com a aparência
  atual (fundo quase-preto, cards `#14171F`) -- Dark Mode não deve ter mudado visualmente de forma
  perceptível além das cores primary/chart-1/chart-5 (agora `#FF3D5A`/`#29E0C9` em vez do vermelho antigo).
- [ ] Abrir uma tela com badges de status (ex. `/ordens`) em modo claro forçado e confirmar que os textos
  coloridos (sucesso/aviso/erro/info) continuam legíveis, não "lavados" contra o fundo branco.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat(design-system): tokens de Light Mode e Dark Mode em index.css (identidade Pulse)"
```

---

### Task 4: Ligar `ThemeProvider` no `App.jsx` + script anti-FOUC em `index.html`

**Files:**
- Modify: `frontend/src/App.jsx:101-110` (função `App`)
- Modify: `frontend/index.html:1-8` (dentro de `<head>`)

**Interfaces:**
- Consumes: `ThemeProvider` de `frontend/src/contexts/ThemeContext.jsx` (Task 1).

- [ ] **Step 1: Adicionar o script anti-FOUC em `index.html`**

Em `frontend/index.html`, inserir como o **primeiro filho** de `<head>` (antes do `<meta charset>` já
existente, ou logo depois -- precisa rodar antes do CSS terminar de carregar):

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <script>
      (function () {
        try {
          var stored = localStorage.getItem("fluxoly-theme");
          if (stored === "light" || stored === "dark") {
            document.documentElement.setAttribute("data-theme", stored);
          }
        } catch (e) {
          // localStorage indisponível -- sem override para aplicar antes do paint;
          // o ThemeProvider (React) ainda resolve o tema normalmente depois de montar.
        }
      })();
    </script>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Onest:wght@700&display=swap"
      rel="stylesheet"
    />
    <meta
      name="description"
      content="O fluxo inteligente da sua loja de celulares. Vendas, estoque, ordens de serviço e financeiro em um único sistema."
    />
    <title>Fluxoly — Gestão para lojas de dispositivos móveis premium</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

(Só a tag `<script>` no topo do `<head>` é nova; o resto do arquivo é idêntico ao atual.)

- [ ] **Step 2: Ligar `ThemeProvider` em `App.jsx`**

Em `frontend/src/App.jsx`, adicionar o import (junto aos outros, topo do arquivo):

```jsx
import { ThemeProvider } from "@/contexts/ThemeContext";
```

E envolver o retorno de `App()` (linhas 101-110 atuais):

```jsx
export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Toaster position="top-right" richColors />
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
```

- [ ] **Step 3: Rodar a suite completa e confirmar que `App.test.jsx` continua passando**

Run: `npm run test -- src/App.test.jsx`
Expected: PASS -- `ThemeProvider` não depende de `AuthContext`/`api/client` (já mockados nesse arquivo) e
usa só `localStorage`/`matchMedia`, ambos disponíveis em jsdom (o segundo já stubado globalmente em
`frontend/src/test/setup.js` para o `useIsMobile()` existente).

- [ ] **Step 4: Rodar a suite completa do frontend**

Run: `npm run test`
Expected: PASS -- nenhum teste existente é afetado.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.jsx frontend/index.html
git commit -m "feat(design-system): liga ThemeProvider ao App e evita flash de tema errado no load"
```

---

### Task 5: `ThemeToggle` na Sidebar

**Files:**
- Create: `frontend/src/components/ThemeToggle.jsx`
- Create: `frontend/src/components/ThemeToggle.test.jsx`
- Modify: `frontend/src/components/Layout.jsx:73-104` (função `SidebarUserFooter`)
- Modify: `frontend/src/components/Layout.test.jsx:1-22` (mocks do topo do arquivo)

**Interfaces:**
- Consumes: `useTheme()` de `frontend/src/contexts/ThemeContext.jsx` (Task 1); `Button` de
  `@/components/ui/button` (já existente, variant="ghost" size="icon", mesmo padrão do botão "Sair" em
  `Layout.jsx`); ícones `Sun`/`Moon`/`Monitor` de `@phosphor-icons/react` (já uma dependência do projeto,
  mesma lib usada pelo resto de `Layout.jsx` -- não usar `lucide-react` aqui para não misturar as duas
  libs de ícone na mesma tela).
- Produces: `<ThemeToggle />` (componente, sem props). Consumido por `Layout.jsx`.

- [ ] **Step 1: Escrever o teste (falhando) do `ThemeToggle`**

Criar `frontend/src/components/ThemeToggle.test.jsx`:

```jsx
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider } from "@/contexts/ThemeContext";
import ThemeToggle from "./ThemeToggle";

function renderToggle() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>
  );
}

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("começa no modo automático (segue o sistema)", () => {
    renderToggle();
    expect(screen.getByRole("button")).toHaveAccessibleName(/tema: automático/i);
  });

  it("um clique alterna para claro, o próximo para escuro, o próximo de volta para automático", async () => {
    renderToggle();
    const user = userEvent.setup();
    const button = screen.getByRole("button");

    await user.click(button);
    expect(button).toHaveAccessibleName(/tema: claro/i);
    expect(localStorage.getItem("fluxoly-theme")).toBe("light");

    await user.click(button);
    expect(button).toHaveAccessibleName(/tema: escuro/i);
    expect(localStorage.getItem("fluxoly-theme")).toBe("dark");

    await user.click(button);
    expect(button).toHaveAccessibleName(/tema: automático/i);
    expect(localStorage.getItem("fluxoly-theme")).toBe("system");
  });
});
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `npm run test -- src/components/ThemeToggle.test.jsx`
Expected: FAIL — `Failed to resolve import "./ThemeToggle"`.

- [ ] **Step 3: Implementar `ThemeToggle.jsx`**

Criar `frontend/src/components/ThemeToggle.jsx`:

```jsx
import { Sun, Moon, Monitor } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/contexts/ThemeContext";

const NEXT_THEME = { system: "light", light: "dark", dark: "system" };
const ICON_BY_THEME = { system: Monitor, light: Sun, dark: Moon };
const LABEL_BY_THEME = {
  system: "Tema: automático (segue o sistema)",
  light: "Tema: claro",
  dark: "Tema: escuro",
};

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const Icon = ICON_BY_THEME[theme];

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(NEXT_THEME[theme])}
      aria-label={`${LABEL_BY_THEME[theme]} — clique para alternar`}
      className="h-8 w-8 text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `npm run test -- src/components/ThemeToggle.test.jsx`
Expected: PASS (2 testes).

- [ ] **Step 5: Integrar em `Layout.jsx`**

Em `frontend/src/components/Layout.jsx`, adicionar o import (junto aos outros componentes locais):

```jsx
import ThemeToggle from "./ThemeToggle";
```

E em `SidebarUserFooter` (linhas 87-101 atuais), adicionar `<ThemeToggle />` entre `<GlobalAlerts />` e o
botão "Sair":

```jsx
      <div className="flex items-center justify-between px-1">
        <span className="text-xs text-sidebar-foreground/60">v1.0.0</span>
        <div className="flex items-center gap-1">
          <GlobalAlerts />
          <ThemeToggle />
          <Button
            variant="ghost"
            size="icon"
            onClick={onLogout}
            aria-label="Sair"
            className="h-8 w-8 text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
          >
            <SignOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
```

- [ ] **Step 6: Ajustar o mock em `Layout.test.jsx`**

`Layout.jsx` agora importa `ThemeToggle`, que chama `useTheme()` -- sem um `ThemeProvider` real envolvendo
o teste, isso lançaria o erro implementado na Task 1. `Layout.test.jsx` já mocka `AuthContext`/`api/client`
no mesmo estilo; seguir o padrão em vez de envolver com um `ThemeProvider` real (mantém o teste de Layout
focado em navegação, não em comportamento de tema -- isso já está coberto em `ThemeToggle.test.jsx`).

Em `frontend/src/components/Layout.test.jsx`, adicionar mais um `vi.mock` junto aos já existentes (topo do
arquivo, depois do mock de `@/api/client`):

```jsx
vi.mock("@/contexts/ThemeContext", () => ({
  useTheme: () => ({ theme: "system", resolvedTheme: "light", setTheme: vi.fn() }),
}));
```

- [ ] **Step 7: Rodar a suite completa de `Layout.test.jsx` e confirmar que passa**

Run: `npm run test -- src/components/Layout.test.jsx`
Expected: PASS (5 testes já existentes, sem nenhuma mudança de asserção -- `getByRole("button", { name:
"Sair" })` continua encontrando só o botão de logout porque a busca é por nome acessível exato, e o novo
botão do `ThemeToggle` tem um nome diferente).

- [ ] **Step 8: Rodar a suite completa do frontend**

Run: `npm run test`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/components/ThemeToggle.jsx frontend/src/components/ThemeToggle.test.jsx frontend/src/components/Layout.jsx frontend/src/components/Layout.test.jsx
git commit -m "feat(design-system): toggle de tema (automático/claro/escuro) na Sidebar"
```

---

### Task 6: Validação final, documentação e PR

**Files:**
- Modify: `docs/operations/PROJECT_STATUS.md`
- Modify: `docs/operations/CHANGELOG.md`
- Modify: `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md:242` (linha da Fase 3.0 na
  tabela da seção 12)

- [ ] **Step 1: Rodar a suite completa e o lint uma última vez**

Run (a partir de `frontend/`): `npm run test && npm run lint`
Expected: PASS -- 0 erros. Se o lint apontar algo nos arquivos novos/modificados, corrigir antes de seguir.

- [ ] **Step 2: Repetir o checklist manual da Task 3, agora com o toggle**

Run: `npm run dev`, abrir `http://localhost:5173`, logar.

- [ ] Clicar o botão de tema na Sidebar (perto de "Sair") e confirmar que ele cicla
  automático → claro → escuro → automático, e que a interface muda de cor a cada clique.
- [ ] Recarregar a página com o tema em "claro" ou "escuro" (não "automático") e confirmar que **não há
  flash** da cor errada antes do app aparecer (o script anti-FOUC da Task 4 deve evitar isso).
- [ ] Testar em uma tela mobile (DevTools > toggle device toolbar) -- o botão deve continuar acessível no
  menu da Sidebar.

- [ ] **Step 3: Atualizar `docs/operations/PROJECT_STATUS.md`**

Adicionar à seção de estado atual (formato consistente com entradas anteriores do Design System): Fase 3.0
concluída -- infraestrutura de tema (Light Mode + Dark Mode, `ThemeProvider`, toggle de 3 estados,
persistência) implementada; identidade Pulse (`#FF3D5A`/`#29E0C9`) aplicada aos tokens de `index.css`;
nenhum componente redesenhado ainda (Fase 3.1 é o próximo passo).

- [ ] **Step 4: Atualizar `docs/operations/CHANGELOG.md`**

Adicionar entrada com a data do merge: "feat(design-system): infraestrutura de tema (Fase 3.0) -- Light
Mode e Dark Mode, toggle automático/claro/escuro, persistência de preferência."

- [ ] **Step 5: Atualizar a tabela de faseamento do plano de Fase 3**

Em `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md`, seção 12, a linha da Fase 3.0
passa de descrição de escopo para `✅ Concluído -- PR #<número real do PR>, <data do merge>`.

- [ ] **Step 6: Commit da documentação**

```bash
git add docs/operations/PROJECT_STATUS.md docs/operations/CHANGELOG.md docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md
git commit -m "docs(design-system): registrar conclusão da Fase 3.0 (infraestrutura de tema)"
```

- [ ] **Step 7: Push e abrir o PR**

```bash
git push -u origin feat/design-system-fase3.0-theme-infra
gh pr create --title "feat(design-system): Fase 3.0 — Infraestrutura de Tema (Light + Dark)" --body "$(cat <<'EOF'
## Resumo
- Tokens de Light Mode (base) e Dark Mode (override via prefers-color-scheme + data-theme) em index.css
- Identidade Pulse aplicada aos tokens de cor (#FF3D5A vermelho-sinal, #29E0C9 ciano de fluxo)
- Cores semânticas de estado recalibradas para WCAG AA em fundo claro (contraste calculado e testado)
- ThemeProvider/useTheme() com persistência em localStorage e sincronia com a preferência do sistema
- Toggle de 3 estados (automático/claro/escuro) na Sidebar
- Nenhum componente redesenhado -- só infraestrutura (Fase 3.1+ trata composição)

## Plano
docs/engineering/plans/PLAN-design-system-fase3.0-theme-infra.md

## Test plan
- [x] Suite de testes completa (frontend) passando
- [x] Lint sem erros
- [x] Checklist manual: Light Mode, Dark Mode, toggle, sem flash no reload, mobile
EOF
)"
```

Aguardar CI verde antes de considerar mergeável (protocolo padrão do repositório -- não fazer merge sem
aprovação, ver `CLAUDE.md`).

---

## Self-Review

**Cobertura da spec:** diagnóstico (§0.1 liberdade criativa, §0.2 identidade Pulse) → tokens de cor
aplicados na Task 3; §3 Light Mode → tokens base da Task 3; §4 Dark Mode → overrides da Task 3; §14 item 1
(seguir o SO por padrão) → `ThemeContext` (Task 1) + CSS de duas camadas (Task 3); toggle acessível → Task
5; persistência → `localStorage` na Task 1; "nenhum componente muda" → nenhuma task altera composição, só
cor/infra. §12 linha 3.0 integralmente coberta.

**Placeholders:** nenhum "TBD"/"implementar depois" — todo step tem código completo ou comando exato. A
única coisa deliberadamente adiada para depois do merge real (número do PR na Task 6) não é um placeholder
de plano, é uma ação que só existe depois que o PR é criado.

**Consistência de tipos/nomes:** `useTheme()` retorna `{ theme, resolvedTheme, setTheme }` -- usado
identicamente nas Tasks 1, 4 (indiretamente, via Provider) e 5. `fluxoly-theme` é a mesma chave de
`localStorage` em `ThemeContext.jsx` (Task 1) e no script de `index.html` (Task 4). `LIGHT_SEMANTIC`/
`LIGHT_SURFACE` (Task 2) e os hex equivalentes em `index.css` (Task 3) usam exatamente os mesmos valores
(`#BD290F`, `#1F7A50`, `#9B6508`, `#0F61B3`, `#FFFFFF`) -- conferido manualmente linha a linha.
