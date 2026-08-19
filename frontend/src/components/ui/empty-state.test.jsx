import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { EmptyState } from "./empty-state";

describe("EmptyState", () => {
  it("mostra título e descrição", () => {
    render(<EmptyState title="Nenhuma venda encontrada" description="Ajuste os filtros para ver resultados." />);

    expect(screen.getByText("Nenhuma venda encontrada")).toBeInTheDocument();
    expect(screen.getByText("Ajuste os filtros para ver resultados.")).toBeInTheDocument();
  });

  it("renderiza a ação quando informada", async () => {
    const onClick = vi.fn();
    render(
      <EmptyState
        title="Nenhum item"
        action={<button onClick={onClick}>Criar item</button>}
      />
    );

    await userEvent.click(screen.getByText("Criar item"));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("funciona sem descrição nem ação", () => {
    render(<EmptyState title="Vazio" />);
    expect(screen.getByText("Vazio")).toBeInTheDocument();
  });
});
