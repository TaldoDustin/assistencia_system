import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Layout from "./Layout";

const mockNavigate = vi.fn();
const mockLogout = vi.fn().mockResolvedValue(undefined);
let mockUser = { nome: "Admin Teste", usuario: "admin", perfil: "admin" };

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: mockUser, logout: mockLogout }),
}));

vi.mock("@/api/client", () => ({
  alertas: { list: vi.fn().mockResolvedValue({ ok: true, alertas: [] }) },
}));

vi.mock("@/contexts/ThemeContext", () => ({
  useTheme: () => ({ theme: "system", resolvedTheme: "light", setTheme: vi.fn() }),
}));

function renderLayout(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Layout />
    </MemoryRouter>
  );
}

describe("Layout / navegação do Sidebar", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockLogout.mockClear();
  });

  it("mostra itens admin-only para perfil admin", () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    renderLayout();

    expect(screen.getByText("Usuários")).toBeInTheDocument();
    expect(screen.getByText("Backups")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Vendas" })).toBeInTheDocument();
  });

  it("esconde itens admin-only e restritos para perfil tecnico", () => {
    mockUser = { nome: "Tecnico", usuario: "tec1", perfil: "tecnico" };
    renderLayout();

    expect(screen.queryByText("Usuários")).not.toBeInTheDocument();
    expect(screen.queryByText("Backups")).not.toBeInTheDocument();
    expect(screen.queryByText("Vendas")).not.toBeInTheDocument();
    expect(screen.queryByText("Financeiro")).not.toBeInTheDocument();
    expect(screen.getByText("Ordens de Serviço")).toBeInTheDocument();
  });

  it("mostra Vendas para perfil vendedor mas não itens admin-only", () => {
    mockUser = { nome: "Vendedor", usuario: "vend1", perfil: "vendedor" };
    renderLayout();

    expect(screen.getByRole("link", { name: "Vendas" })).toBeInTheDocument();
    expect(screen.queryByText("Usuários")).not.toBeInTheDocument();
    expect(screen.queryByText("Financeiro")).not.toBeInTheDocument();
  });

  it("marca a rota atual como ativa", () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    renderLayout("/clientes");

    const link = screen.getByText("Clientes").closest("a");
    expect(link.className).toContain("bg-sidebar-primary");

    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink.className).not.toContain("bg-sidebar-primary");
  });

  it("logout chama logout() e navega para /login", async () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    renderLayout();
    const user = userEvent.setup();

    await user.click(screen.getByRole("button", { name: "Sair" }));

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
  });

  it("agrupa os itens do Sidebar em seções com rótulo (6 Pilares + Administração)", () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    renderLayout();

    expect(screen.getByText("Vendas", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Operação")).toBeInTheDocument();
    expect(screen.getByText("Financeiro", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByText("Relacionamento")).toBeInTheDocument();
    expect(screen.getByText("Serviços")).toBeInTheDocument();
    expect(screen.getByText("Inteligência")).toBeInTheDocument();
    expect(screen.getByText("Administração")).toBeInTheDocument();
  });

  it("remove a entrada duplicada de /compras -- só 'Lista de Compras' aparece", () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    renderLayout();

    expect(screen.getByText("Lista de Compras")).toBeInTheDocument();
    expect(screen.queryByText("Compras")).not.toBeInTheDocument();
  });
});
