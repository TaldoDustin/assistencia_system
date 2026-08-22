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
