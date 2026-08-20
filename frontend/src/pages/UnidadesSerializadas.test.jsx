import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import UnidadesSerializadas from "./UnidadesSerializadas";

const mockList = vi.fn();

vi.mock("@/api/client", () => ({
  unidadesSerializadas: { list: (...args) => mockList(...args), get: vi.fn(), historico: vi.fn() },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: "admin" } }),
}));

describe("UnidadesSerializadas — estados e status semântico", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = render(<UnidadesSerializadas />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com o Badge de status semântico quando a API retorna unidades", async () => {
    mockList.mockResolvedValue({
      ok: true,
      total: 1,
      items: [{ id: 1, imei: "123456789012345", status: "disponivel", origem_tipo: "estoque" }],
    });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("123456789012345")).toBeInTheDocument());
    expect(screen.getByText("Disponível").className).toContain("bg-success/10");
    // ORIGEM_BADGE migrado para o Badge taxonômico variant="tag" no PR 5
    // (PLAN-design-system-fase2.md) -- cor neutra única, sem tom por valor.
    expect(screen.getByText("Estoque").className).toContain("bg-secondary/60");
  });

  it("mostra EmptyState quando não há unidades", async () => {
    mockList.mockResolvedValue({ ok: true, total: 0, items: [] });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("Nenhuma unidade serializada cadastrada ainda.")).toBeInTheDocument());
  });

  it("mostra ErrorState com retry quando a API falha", async () => {
    mockList.mockResolvedValue({ ok: false });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar as unidades.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });
});
