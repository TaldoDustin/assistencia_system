import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import Produtos from "./Produtos";

const mockList = vi.fn();

vi.mock("@/api/client", () => ({
  produtos: { list: (...args) => mockList(...args) },
  constantes: { get: vi.fn().mockResolvedValue({ ok: true }) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: "admin" } }),
}));

describe("Produtos — estados e status semântico", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = render(<Produtos />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com Badge de disponibilidade e de condição", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, descricao: "iPhone 15 Pro", categoria: "iPhone", condicao: "Novo", ativo: true, quantidade: 3, preco_venda: 5000 }],
    });
    render(<Produtos />);

    await waitFor(() => expect(screen.getByText("iPhone 15 Pro")).toBeInTheDocument());
    expect(screen.getByText("Disponível").className).toContain("bg-success/10");
    expect(screen.getByText("Novo").className).toContain("bg-success/10");
  });

  it("mostra EmptyState quando não há produtos", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<Produtos />);

    await waitFor(() => expect(screen.getByText("Nenhum produto cadastrado ainda.")).toBeInTheDocument());
  });

  it("mostra ErrorState com retry quando a API falha", async () => {
    mockList.mockResolvedValue({ ok: false });
    render(<Produtos />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar os produtos.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });
});
