import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Kanban from "./Kanban";

const mockList = vi.fn();

vi.mock("@/api/client", () => ({
  ordens: { list: (...args) => mockList(...args), patchStatus: vi.fn() },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

function renderKanban() {
  return render(
    <MemoryRouter>
      <Kanban />
    </MemoryRouter>
  );
}

describe("Kanban — estados e semântica de status", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("mostra o spinner de carregamento antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = renderKanban();

    expect(container.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("organiza as ordens nas colunas por status e mostra o Badge semântico no card", async () => {
    mockList.mockResolvedValue({
      ok: true,
      ordens: [{ id: 1, cliente: "João", status: "Finalizado" }],
    });
    renderKanban();

    await waitFor(() => expect(screen.getByText("João")).toBeInTheDocument());
    // O card carrega o mesmo OrderStatusBadge usado em Orders/EditOrder --
    // mesma fonte de verdade de cor (getStatusVariant), sem interpretação própria.
    expect(screen.getByText("Finalizado", { selector: "span" }).className).toContain("bg-success/10");
  });

  it("mostra ErrorState quando a carga inicial falha, com retry", async () => {
    mockList.mockResolvedValue({ ok: false });
    renderKanban();

    await waitFor(() => expect(screen.getByText("Não foi possível carregar as ordens.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });

  it("mostra ErrorState quando a promise da API rejeita, não fica preso no spinner (KI-048)", async () => {
    mockList.mockRejectedValue(new Error("network error"));
    renderKanban();

    await waitFor(() => expect(screen.getByText("Não foi possível carregar as ordens.")).toBeInTheDocument());
  });
});
