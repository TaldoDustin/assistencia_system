import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Landing from "./Landing";

function renderLanding() {
  return render(
    <MemoryRouter>
      <Landing />
    </MemoryRouter>
  );
}

describe("Landing — smoke test das 14 seções", () => {
  it("renderiza o título de cada seção da spec", () => {
    renderLanding();

    expect(screen.getByRole("heading", { name: /o fluxo inteligente da sua loja de celulares/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /sua loja roda no improviso\?/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /um único fluxo para toda a operação/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /o que muda na prática/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /um sistema, todas as frentes da loja/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /do improviso ao controle, em 3 passos/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /veja o fluxoly de verdade/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /por que usar o fluxoly\?/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /quem usa, recomenda/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /um plano para cada estágio da sua loja/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /perguntas frequentes/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /pronto para organizar sua operação\?/i })).toBeInTheDocument();
  });

  it("CTA primário do Hero aponta para /login", () => {
    renderLanding();

    const cta = screen.getAllByRole("link", { name: /começar agora/i })[0];
    expect(cta).toHaveAttribute("href", "/login");
  });

  it("itens [DEFINIR] (Prova Social, Planos) aparecem como placeholder, nunca texto inventado", () => {
    renderLanding();

    expect(screen.getByText(/\[DEFINIR — aguardando primeiro cliente\/piloto citável\]/)).toBeInTheDocument();
    expect(screen.getByText(/\[DEFINIR — faixas e valores dependem da decisão de monetização/)).toBeInTheDocument();
  });

  it("FAQ abre e fecha via Accordion", async () => {
    const user = userEvent.setup();
    renderLanding();

    const question = screen.getByText("O que é o Fluxoly?");
    expect(screen.queryByText(/plataforma de gestão para lojas especializadas/i)).not.toBeInTheDocument();

    await user.click(question);
    expect(screen.getByText(/plataforma de gestão para lojas especializadas/i)).toBeInTheDocument();

    await user.click(question);
    expect(screen.queryByText(/plataforma de gestão para lojas especializadas/i)).not.toBeInTheDocument();
  });
});
