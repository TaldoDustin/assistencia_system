import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider, useTheme } from "./ThemeContext";

function Probe() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button onClick={() => setTheme("light")}>light</button>
      <button onClick={() => setTheme("dark")}>dark</button>
      <button onClick={() => setTheme("system")}>system</button>
    </div>
  );
}

function renderProbe() {
  return render(
    <ThemeProvider>
      <Probe />
    </ThemeProvider>
  );
}

describe("ThemeContext", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  afterEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("usa 'dark' como padrão quando não há preferência salva (Fase 3.0: nem todas as telas migraram para Light Mode ainda)", () => {
    renderProbe();
    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
  });

  it("resolve para 'light' quando theme='system' e o SO não prefere dark (stub padrão do jsdom)", () => {
    localStorage.setItem("fluxoly-theme", "system");
    renderProbe();
    expect(screen.getByTestId("resolved")).toHaveTextContent("light");
  });

  it("lê uma preferência já salva no localStorage ao montar", () => {
    localStorage.setItem("fluxoly-theme", "dark");
    renderProbe();
    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
    expect(screen.getByTestId("resolved")).toHaveTextContent("dark");
  });

  it("ignora um valor inválido salvo no localStorage e usa 'dark'", () => {
    localStorage.setItem("fluxoly-theme", "roxo");
    renderProbe();
    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
  });

  it("setTheme('dark') persiste no localStorage e aplica data-theme='dark' no <html>", async () => {
    // Semeia 'light' para não colidir com o texto do botão "dark" -- 'dark' já é o padrão sem
    // preferência salva (Fase 3.0, revisão final), então o span "theme" já diria "dark" antes do clique.
    localStorage.setItem("fluxoly-theme", "light");
    renderProbe();
    const user = userEvent.setup();
    await user.click(screen.getByText("dark"));

    expect(screen.getByTestId("theme")).toHaveTextContent("dark");
    expect(screen.getByTestId("resolved")).toHaveTextContent("dark");
    expect(localStorage.getItem("fluxoly-theme")).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("setTheme('system') remove o atributo data-theme do <html>", async () => {
    // Semeia 'light' para não colidir com o texto do botão "dark" -- 'dark' já é o padrão sem
    // preferência salva (Fase 3.0, revisão final), então o span "theme" já diria "dark" antes do clique.
    localStorage.setItem("fluxoly-theme", "light");
    renderProbe();
    const user = userEvent.setup();
    await user.click(screen.getByText("dark"));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");

    await user.click(screen.getByText("system"));
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
    expect(localStorage.getItem("fluxoly-theme")).toBe("system");
  });

  it("reage a uma mudança de preferência do sistema quando theme='system'", () => {
    localStorage.setItem("fluxoly-theme", "system");
    let changeHandler;
    const mql = {
      matches: false,
      media: "(prefers-color-scheme: dark)",
      addEventListener: (_event, handler) => { changeHandler = handler; },
      removeEventListener: () => {},
    };
    const originalMatchMedia = window.matchMedia;
    window.matchMedia = vi.fn().mockReturnValue(mql);

    renderProbe();
    expect(screen.getByTestId("resolved")).toHaveTextContent("light");

    act(() => {
      mql.matches = true;
      changeHandler({ matches: true });
    });

    expect(screen.getByTestId("resolved")).toHaveTextContent("dark");
    window.matchMedia = originalMatchMedia;
  });

  it("useTheme() fora do ThemeProvider lança erro", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Probe />)).toThrow("useTheme deve ser usado dentro de ThemeProvider");
    consoleError.mockRestore();
  });
});
