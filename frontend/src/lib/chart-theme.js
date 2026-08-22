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
