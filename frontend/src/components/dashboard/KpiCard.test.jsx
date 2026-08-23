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
  ])('color="%s" usa o token de tema %s em vez de classe Tailwind crua -- KI-050 (colorMap + iconColorMap)', (color, expectedClass) => {
    const { container } = render(<KpiCard title="X" value={1} icon={CurrencyDollar} color={color} />);
    // Verifica colorMap (outer div)
    expect(container.firstChild.className).toContain(expectedClass);
    // Verifica iconColorMap (icon wrapper div)
    const iconWrapper = container.querySelector(".h-12.w-12");
    expect(iconWrapper.className).toContain(expectedClass);
  });

  it("cai em 'primary' (text-info) quando a cor não existe no mapa (colorMap + iconColorMap)", () => {
    const { container } = render(<KpiCard title="X" value={1} icon={CurrencyDollar} color="inexistente" />);
    // Verifica colorMap (outer div)
    expect(container.firstChild.className).toContain("text-info");
    // Verifica iconColorMap (icon wrapper div)
    const iconWrapper = container.querySelector(".h-12.w-12");
    expect(iconWrapper.className).toContain("text-info");
  });
});
