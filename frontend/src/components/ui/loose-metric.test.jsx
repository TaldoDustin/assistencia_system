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
