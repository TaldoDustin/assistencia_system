import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "./badge";

describe("Badge — variantes semânticas (Fase 2)", () => {
  it("aplica a classe de tom correta para cada variante semântica", () => {
    const variants = ["success", "warning", "error", "info", "neutral"];
    variants.forEach((variant) => {
      render(<Badge variant={variant}>{variant}</Badge>);
    });

    expect(screen.getByText("success").className).toContain("bg-success/10");
    expect(screen.getByText("warning").className).toContain("bg-warning/10");
    expect(screen.getByText("error").className).toContain("bg-destructive/10");
    expect(screen.getByText("info").className).toContain("bg-info/10");
    expect(screen.getByText("neutral").className).toContain("bg-muted");
  });

  it("preserva o comportamento das variantes existentes", () => {
    render(<Badge variant="outline" className="custom">Padrão</Badge>);
    const badge = screen.getByText("Padrão");
    expect(badge.className).toContain("text-foreground");
    expect(badge.className).toContain("custom");
  });

  it("aplica a classe neutra da variante taxonômica tag, distinta das variantes de severidade", () => {
    render(<Badge variant="tag">Categoria</Badge>);
    const badge = screen.getByText("Categoria");
    expect(badge.className).toContain("bg-secondary/60");
    expect(badge.className).toContain("text-secondary-foreground");
    expect(badge.className).toContain("border-border");
  });

  it("usa a variante default quando nenhuma é informada", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default").className).toContain("bg-primary");
  });
});
