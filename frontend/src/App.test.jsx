import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "./App";

// Cobre a mudança cirúrgica em ProtectedRoute (App.jsx): "/" deslogado renderiza a
// Landing Page pública; "/" autenticado continua o Dashboard dentro do Layout, sem
// regressão; qualquer outra rota protegida (ex. /ordens) continua redirecionando para
// /login normalmente — a mudança é isolada em "/", não em toda rota pública
// (ver docs/engineering/plans/PLAN-landing-page-implementacao.md).

let mockUser = null;
const mockLoading = false;

vi.mock("@/contexts/AuthContext", () => ({
  AuthProvider: ({ children }) => children,
  useAuth: () => ({ user: mockUser, loading: mockLoading, logout: vi.fn() }),
}));

vi.mock("@/api/client", () => ({
  dashboard: { get: vi.fn().mockResolvedValue({ ok: true }) },
  constantes: { get: vi.fn().mockResolvedValue({ ok: true, tecnicos: [] }) },
  alertas: { list: vi.fn().mockResolvedValue({ ok: true, alertas: [] }) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
  Toaster: () => null,
}));

// Recharts não se comporta bem em jsdom (mesmo cuidado do Dashboard.test.jsx).
vi.mock("@/components/dashboard/RevenueChartCard", () => ({ default: () => <div>RevenueChart</div> }));
vi.mock("@/components/dashboard/TechnicianProfitChartCard", () => ({ default: () => <div>TechChart</div> }));
vi.mock("@/components/dashboard/ServicesChartCard", () => ({ default: () => <div>ServicesChart</div> }));

describe("App — roteamento condicional da raiz (/)", () => {
  beforeEach(() => {
    window.history.pushState({}, "", "/");
    mockUser = null;
  });

  it("'/' deslogado renderiza a Landing Page pública", async () => {
    render(<App />);

    expect(
      await screen.findByRole("heading", { name: /o fluxo inteligente da sua loja de celulares/i })
    ).toBeInTheDocument();
    // Sidebar do produto autenticado não deve aparecer para o visitante deslogado.
    expect(screen.queryByText("Ordens de Serviço")).not.toBeInTheDocument();
  });

  it("'/' autenticado continua renderizando o Dashboard dentro do Layout, sem regressão", async () => {
    mockUser = { nome: "Admin", usuario: "admin", perfil: "admin" };
    render(<App />);

    // Item de navegação do Sidebar confirma que o Layout autenticado montou, não a Landing.
    expect(await screen.findByText("Ordens de Serviço")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /o fluxo inteligente da sua loja de celulares/i })).not.toBeInTheDocument();
  });

  it("outra rota protegida (/ordens) deslogada continua redirecionando para /login", async () => {
    window.history.pushState({}, "", "/ordens");
    render(<App />);

    await waitFor(() => expect(window.location.pathname).toBe("/login"));
  });
});
