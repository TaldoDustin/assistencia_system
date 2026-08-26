import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Clientes from "./Clientes";

const mockList = vi.fn();
const mockGarantiasList = vi.fn();
const mockClienteHistory = vi.fn().mockResolvedValue({ ok: true, ordens: [] });

vi.mock("@/api/client", () => ({
  clientes: { list: (...args) => mockList(...args) },
  ordens: { clienteHistory: (...args) => mockClienteHistory(...args) },
  garantias: { list: (...args) => mockGarantiasList(...args) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: "admin" } }),
}));

describe("Clientes — estados e status semântico (PR 5)", () => {
  beforeEach(() => {
    mockList.mockReset();
    mockGarantiasList.mockReset();
    mockGarantiasList.mockResolvedValue({ ok: true, garantias: [] });
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = render(<Clientes />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com os clientes quando a API responde", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, nome: "Carla Souza", telefone: "11999990000", email: "carla@example.com" }],
    });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Carla Souza")).toBeInTheDocument());
  });

  it("mostra EmptyState quando não há clientes", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Nenhum cliente cadastrado ainda.")).toBeInTheDocument());
  });

  it("mostra os filtros e KPIs da listagem após carregar", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByPlaceholderText("Buscar por nome, telefone, e-mail, CPF/CNPJ...")).toBeInTheDocument());
    expect(screen.getByText("Com telefone")).toBeInTheDocument();
  });

  it("mostra o Badge de garantia com a variante semântica correta no perfil do cliente", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, nome: "Carla Souza", telefone: "11999990000", email: "carla@example.com" }],
    });
    mockGarantiasList.mockResolvedValue({
      ok: true,
      garantias: [{ id: 1, reparo_id: 1, modelo: "iPhone 13", status_garantia: "vencida", dias_restantes: 0 }],
    });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Carla Souza")).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByText("Carla Souza"));

    await waitFor(() => expect(screen.getByText("Vencida")).toBeInTheDocument());
    expect(screen.getByText("Vencida").className).toContain("bg-destructive/10");
  });

  it("mostra ErrorState com retry quando a API de clientes falha (KI-049)", async () => {
    mockList.mockResolvedValue({ ok: false });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar os clientes.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });

  it("mostra ErrorState quando a promise da API de clientes rejeita (KI-049)", async () => {
    mockList.mockRejectedValue(new Error("network error"));
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar os clientes.")).toBeInTheDocument());
  });

  it("perfil do cliente não fica preso no loading quando a busca de histórico/garantias rejeita (KI-048)", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, nome: "Carla Souza", telefone: "11999990000", email: "carla@example.com" }],
    });
    mockClienteHistory.mockRejectedValue(new Error("network error"));
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Carla Souza")).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByText("Carla Souza"));

    await waitFor(() => expect(screen.getByText("Nenhuma OS encontrada para este cliente.")).toBeInTheDocument());
  });
});
