import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import OrderStatusBadge from "./OrderStatusBadge";

describe("OrderStatusBadge — semântica de cor unificada (getStatusVariant)", () => {
  it.each([
    ["Em andamento", "bg-info/10"],
    ["Aguardando peca", "bg-warning/10"],
    ["Finalizado", "bg-success/10"],
    ["Cancelado", "bg-destructive/10"],
  ])("mapeia status %s para o tom semântico correto", (status, expectedClass) => {
    render(<OrderStatusBadge status={status} />);
    expect(screen.getByText(status).className).toContain(expectedClass);
  });

  it("usa o tom neutro para status desconhecido", () => {
    render(<OrderStatusBadge status="Algo Novo" />);
    expect(screen.getByText("Algo Novo").className).toContain("bg-muted");
  });

  it("mostra travessão quando status está ausente", () => {
    render(<OrderStatusBadge status={undefined} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
