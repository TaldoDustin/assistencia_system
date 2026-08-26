import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toast } from "sonner";
import Financeiro from "./Financeiro";

const mockCaixaList = vi.fn();
const mockContasPagarList = vi.fn();
const mockContasReceberList = vi.fn();
const mockSaldo = vi.fn().mockResolvedValue({ ok: true, saldo: 1000 });

vi.mock("@/api/client", () => ({
  caixa: { list: (...args) => mockCaixaList(...args), saldo: (...args) => mockSaldo(...args) },
  contasPagar: { list: (...args) => mockContasPagarList(...args) },
  contasReceber: { list: (...args) => mockContasReceberList(...args) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: "admin" } }),
}));

async function abrirAba(nome) {
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: nome }));
}

describe("Financeiro — Movimentações: estados e status semântico (PR 5)", () => {
  beforeEach(() => {
    mockCaixaList.mockReset();
    mockContasPagarList.mockReset();
    mockContasReceberList.mockReset();
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockCaixaList.mockReturnValue(new Promise(() => {}));
    const { container } = render(<Financeiro />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com o Badge de tipo semântico (entrada=success, saída=error)", async () => {
    mockCaixaList.mockResolvedValue({
      ok: true,
      total: 2,
      items: [
        { id: 1, tipo: "entrada", valor: 500, origem: "manual", criado_em: "2026-08-20 10:00:00" },
        { id: 2, tipo: "saida", valor: 100, origem: "manual", criado_em: "2026-08-20 11:00:00" },
      ],
    });
    render(<Financeiro />);

    await waitFor(() => expect(screen.getByText("Entrada")).toBeInTheDocument());
    expect(screen.getByText("Entrada").className).toContain("bg-success/10");
    expect(screen.getByText("Saída").className).toContain("bg-destructive/10");
  });

  it("mostra EmptyState quando não há movimentações", async () => {
    mockCaixaList.mockResolvedValue({ ok: true, total: 0, items: [] });
    render(<Financeiro />);

    await waitFor(() => expect(screen.getByText("Nenhuma movimentação encontrada.")).toBeInTheDocument());
  });

  it("mostra ErrorState com retry quando a API de movimentações falha", async () => {
    mockCaixaList.mockResolvedValue({ ok: false });
    render(<Financeiro />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar as movimentações.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });

  it("mostra Badge de status semântico na aba Contas a Pagar (pendente=warning, pago=success)", async () => {
    mockCaixaList.mockResolvedValue({ ok: true, total: 0, items: [] });
    mockContasPagarList.mockResolvedValue({
      ok: true,
      total: 2,
      items: [
        { id: 1, descricao: "Aluguel", valor: 2000, status: "pendente", data_vencimento: "2026-09-01" },
        { id: 2, descricao: "Internet", valor: 150, status: "pago", data_vencimento: "2026-08-01" },
      ],
    });
    render(<Financeiro />);
    await abrirAba("Contas a Pagar");

    await waitFor(() => expect(screen.getByText("Aluguel")).toBeInTheDocument());
    expect(screen.getByText("Pendente").className).toContain("bg-warning/10");
    expect(screen.getByText("Pago").className).toContain("bg-success/10");
  });

  it("mostra EmptyState específico na aba Contas a Receber quando vazia", async () => {
    mockCaixaList.mockResolvedValue({ ok: true, total: 0, items: [] });
    mockContasReceberList.mockResolvedValue({ ok: true, total: 0, items: [] });
    render(<Financeiro />);
    await abrirAba("Contas a Receber");

    await waitFor(() => expect(screen.getByText("Nenhuma conta a receber cadastrada.")).toBeInTheDocument());
  });

  it("mostra os filtros da listagem de movimentações após carregar", async () => {
    mockCaixaList.mockResolvedValue({ ok: true, total: 0, items: [] });
    render(<Financeiro />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Lançar" })).toBeInTheDocument());
  });
});

describe("Financeiro — Saldo em caixa: rejeição de promise não fica silenciosa (KI-048)", () => {
  beforeEach(() => {
    mockCaixaList.mockReset();
    mockSaldo.mockReset();
  });

  it("mostra toast de erro e sai do estado de loading quando a busca de saldo rejeita", async () => {
    mockCaixaList.mockResolvedValue({ ok: true, total: 0, items: [] });
    mockSaldo.mockRejectedValue(new Error("network error"));
    render(<Financeiro />);

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Erro ao carregar saldo em caixa"));
  });
});
