import { describe, it, expect } from "vitest";
import {
  CHART_GRID_STROKE,
  CHART_AXIS_TICK,
  CHART_CURSOR_STROKE,
  CHART_CURSOR_FILL,
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
    expect(CHART_CURSOR_FILL).toBe("var(--color-muted)");
  });
});
