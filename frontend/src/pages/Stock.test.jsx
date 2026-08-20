import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import Stock from "./Stock";

const mockList = vi.fn();
const mockReposicao = vi.fn().mockResolvedValue({ ok: true, itens: [] });

vi.mock("@/api/client", () => ({
  estoque: { list: (...args) => mockList(...args), reposicaoSugestao: (...args) => mockReposicao(...args) },
  constantes: { get: vi.fn().mockResolvedValue({ ok: true }) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: "admin" } }),
}));

describe("Stock — estados e status semântico", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = render(<Stock />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com o Badge de status semântico quando a API retorna itens", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, descricao: "Tela iPhone 14", status_estoque: "disponivel", quantidade: 5 }],
    });
    render(<Stock />);

    await waitFor(() => expect(screen.getByText("Tela iPhone 14")).toBeInTheDocument());
    expect(screen.getByText("Disponível").className).toContain("bg-success/10");
  });

  it("mostra EmptyState quando não há itens", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<Stock />);

    await waitFor(() => expect(screen.getByText(/Nenhum item/)).toBeInTheDocument());
  });

  it("mostra ErrorState com retry quando a API falha", async () => {
    mockList.mockResolvedValue({ ok: false });
    render(<Stock />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar o estoque.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });
});
