import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider } from "@/contexts/ThemeContext";
import ThemeToggle from "./ThemeToggle";

function renderToggle() {
  return render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>
  );
}

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("começa no modo automático (segue o sistema)", () => {
    localStorage.setItem("fluxoly-theme", "system");
    renderToggle();
    expect(screen.getByRole("button")).toHaveAccessibleName(/tema: automático/i);
  });

  it("sem preferência salva, começa no modo escuro (não automático) -- telas ainda não migradas para Light Mode", () => {
    renderToggle();
    expect(screen.getByRole("button")).toHaveAccessibleName(/tema: escuro/i);
  });

  it("um clique alterna para claro, o próximo para escuro, o próximo de volta para automático", async () => {
    localStorage.setItem("fluxoly-theme", "system");
    renderToggle();
    const user = userEvent.setup();
    const button = screen.getByRole("button");

    await user.click(button);
    expect(button).toHaveAccessibleName(/tema: claro/i);
    expect(localStorage.getItem("fluxoly-theme")).toBe("light");

    await user.click(button);
    expect(button).toHaveAccessibleName(/tema: escuro/i);
    expect(localStorage.getItem("fluxoly-theme")).toBe("dark");

    await user.click(button);
    expect(button).toHaveAccessibleName(/tema: automático/i);
    expect(localStorage.getItem("fluxoly-theme")).toBe("system");
  });
});
