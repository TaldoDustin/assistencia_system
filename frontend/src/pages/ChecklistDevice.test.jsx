import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import ChecklistDevice from "./ChecklistDevice";

const mockGetPublic = vi.fn();
const mockSavePublic = vi.fn();

vi.mock("@/api/client", () => ({
  checklist: {
    getPublic: (...args) => mockGetPublic(...args),
    savePublic: (...args) => mockSavePublic(...args),
  },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

const ordemValida = {
  id: 42,
  cliente: "Maria Souza",
  modelo: "iPhone 14",
  cor: "Preto",
  imei: "123456789012345",
};

function renderChecklist() {
  return render(
    <MemoryRouter initialEntries={["/checklist/token-abc"]}>
      <Routes>
        <Route path="/checklist/:token" element={<ChecklistDevice />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ChecklistDevice — estados", () => {
  beforeEach(() => {
    mockGetPublic.mockReset();
    mockSavePublic.mockReset();
  });

  it("mostra o spinner de carregamento antes da API responder", () => {
    mockGetPublic.mockReturnValue(new Promise(() => {}));
    const { container } = renderChecklist();

    expect(container.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("mostra o ErrorState quando o token não corresponde a uma OS válida", async () => {
    mockGetPublic.mockResolvedValue({ ok: false, erro: "Token inválido" });
    renderChecklist();

    await waitFor(() => expect(screen.getByText("Checklist indisponível")).toBeInTheDocument());
  });

  it("renderiza o checklist completo quando a OS é válida", async () => {
    mockGetPublic.mockResolvedValue({ ok: true, ordem: ordemValida, checklist: {} });
    renderChecklist();

    await waitFor(() => expect(screen.getByText(/Maria Souza/)).toBeInTheDocument());
    expect(screen.getByText("Fluxoly")).toBeInTheDocument();
    expect(screen.getByText("Touch")).toBeInTheDocument();
    expect(screen.getByText("Alto-falante")).toBeInTheDocument();
    expect(screen.getByText("Botões físicos")).toBeInTheDocument();
  });

  it("marcar uma célula da grade de touch atualiza a cobertura", async () => {
    mockGetPublic.mockResolvedValue({ ok: true, ordem: ordemValida, checklist: {} });
    renderChecklist();
    await waitFor(() => expect(screen.getByText("Touch")).toBeInTheDocument());

    expect(screen.getByText(/Cobertura atual: 0%/)).toBeInTheDocument();

    const user = userEvent.setup();
    const [firstCell] = document.querySelectorAll("[data-cell-index]");
    await user.pointer({ keys: "[MouseLeft]", target: firstCell });

    await waitFor(() => expect(screen.getByText(/Cobertura atual: 5%/)).toBeInTheDocument());
  });

  it("salvar checklist chama a API com o payload esperado", async () => {
    mockGetPublic.mockResolvedValue({ ok: true, ordem: ordemValida, checklist: {} });
    mockSavePublic.mockResolvedValue({ ok: true, checklist: {} });
    renderChecklist();
    await waitFor(() => expect(screen.getByText("Touch")).toBeInTheDocument());

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Salvar checklist" }));

    await waitFor(() => expect(mockSavePublic).toHaveBeenCalledWith("token-abc", expect.objectContaining({
      origem: "qr_publico",
    })));
  });
});
