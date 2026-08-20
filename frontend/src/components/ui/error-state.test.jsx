import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ErrorState, ErrorBanner } from "./error-state";

describe("ErrorState", () => {
  it("mostra mensagem padrão e chama onRetry", async () => {
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);

    expect(screen.getByText("Não foi possível carregar os dados.")).toBeInTheDocument();
    await userEvent.click(screen.getByText("Tentar novamente"));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("aceita título/descrição customizados", () => {
    render(<ErrorState title="Erro ao carregar vendas" description="Tente de novo em instantes." />);
    expect(screen.getByText("Erro ao carregar vendas")).toBeInTheDocument();
    expect(screen.getByText("Tente de novo em instantes.")).toBeInTheDocument();
  });

  it("não mostra botão de retry quando onRetry não é informado", () => {
    render(<ErrorState />);
    expect(screen.queryByText("Tentar novamente")).not.toBeInTheDocument();
  });
});

describe("ErrorBanner", () => {
  it("mostra a mensagem e aciona onRetry", async () => {
    const onRetry = vi.fn();
    render(<ErrorBanner message="Falha ao atualizar" onRetry={onRetry} />);

    expect(screen.getByText("Falha ao atualizar")).toBeInTheDocument();
    await userEvent.click(screen.getByText("Tentar novamente"));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
