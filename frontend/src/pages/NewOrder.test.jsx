import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toast } from "sonner";
import NewOrder from "./NewOrder";

const mockConstGet = vi.fn();
const mockReparosList = vi.fn();
const mockEstoqueList = vi.fn();

vi.mock("@/api/client", () => ({
  constantes: { get: (...args) => mockConstGet(...args) },
  reparos: { list: (...args) => mockReparosList(...args) },
  estoque: { list: (...args) => mockEstoqueList(...args) },
  ordens: { create: vi.fn() },
  precos: { sugerir: vi.fn() },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

function renderNewOrder() {
  return render(
    <MemoryRouter>
      <NewOrder />
    </MemoryRouter>
  );
}

describe("NewOrder — carga inicial", () => {
  beforeEach(() => {
    mockConstGet.mockReset();
    mockReparosList.mockReset();
    mockEstoqueList.mockReset();
    toast.error.mockReset();
  });

  it("mostra o formulário (Panel de Cliente) quando a API responde", async () => {
    mockConstGet.mockResolvedValue({ ok: true, os_tipos: [], iphone_models: [] });
    mockReparosList.mockResolvedValue({ ok: true, reparos: [] });
    mockEstoqueList.mockResolvedValue({ ok: true, items: [] });
    renderNewOrder();

    await waitFor(() => expect(screen.getByText("Nova Ordem de Serviço")).toBeInTheDocument());
    expect(screen.getByText("Cliente")).toBeInTheDocument();
  });

  it("mostra toast.error e sai do spinner quando a promise da carga inicial rejeita (KI-048)", async () => {
    mockConstGet.mockResolvedValue({ ok: true, os_tipos: [], iphone_models: [] });
    mockReparosList.mockResolvedValue({ ok: true, reparos: [] });
    mockEstoqueList.mockRejectedValue(new Error("network error"));
    const { container } = renderNewOrder();

    expect(container.querySelector(".animate-spin")).toBeInTheDocument();

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Erro ao carregar dados da nova ordem"));
    await waitFor(() => expect(container.querySelector(".animate-spin")).not.toBeInTheDocument());
    expect(screen.getByText("Nova Ordem de Serviço")).toBeInTheDocument();
  });
});
