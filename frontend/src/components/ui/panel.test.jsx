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
