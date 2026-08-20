import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import Vendas from "./Vendas";

const mockList = vi.fn();

vi.mock("@/api/client", () => ({
  clientes: { list: vi.fn().mockResolvedValue({ ok: true, items: [] }) },
  unidadesSerializadas: { list: vi.fn().mockResolvedValue({ ok: true, items: [] }) },
  vendas: { list: (...args) => mockList(...args) },
  tiposGarantia: { list: vi.fn().mockResolvedValue({ ok: true, items: [] }) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn(), info: vi.fn() },
}));

function renderVendas() {
  return render(
    <MemoryRouter>
      <Vendas />
    </MemoryRouter>
  );
}

async function abrirHistorico() {
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Histórico" }));
}

describe("Vendas — Histórico: estados e status semântico (PR 5)", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("mostra o skeleton de lista antes da API responder", async () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = renderVendas();
    await abrirHistorico();

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com o Badge de status semântico quando a API retorna vendas", async () => {
    mockList.mockResolvedValue({
      ok: true,
      total: 1,
      items: [{ id: 1, cliente_nome: "Ana Silva", status: "concluida", forma_pagamento: "pix", valor_total: 1200 }],
    });
    renderVendas();
    await abrirHistorico();

    await waitFor(() => expect(screen.getByText("Ana Silva")).toBeInTheDocument());
    expect(screen.getByText("Concluída").className).toContain("bg-success/10");
  });

  it("mostra a variante de erro (destructive) para venda cancelada", async () => {
    mockList.mockResolvedValue({
      ok: true,
      total: 1,
      items: [{ id: 2, cliente_nome: "Bruno Costa", status: "cancelada", forma_pagamento: "cartao", valor_total: 800 }],
    });
    renderVendas();
    await abrirHistorico();

    await waitFor(() => expect(screen.getByText("Cancelada")).toBeInTheDocument());
    expect(screen.getByText("Cancelada").className).toContain("bg-destructive/10");
  });

  it("mostra EmptyState quando não há vendas", async () => {
    mockList.mockResolvedValue({ ok: true, total: 0, items: [] });
    renderVendas();
    await abrirHistorico();

    await waitFor(() => expect(screen.getByText("Nenhuma venda registrada ainda.")).toBeInTheDocument());
  });

  it("mostra ErrorState com retry quando a API falha", async () => {
    mockList.mockResolvedValue({ ok: false });
    renderVendas();
    await abrirHistorico();

    await waitFor(() => expect(screen.getByText("Não foi possível carregar o histórico de vendas.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });

  it("mostra os filtros da listagem após carregar", async () => {
    mockList.mockResolvedValue({ ok: true, total: 0, items: [] });
    renderVendas();
    await abrirHistorico();

    await waitFor(() => expect(screen.getByPlaceholderText("Buscar por cliente, IMEI ou produto...")).toBeInTheDocument());
  });
});
