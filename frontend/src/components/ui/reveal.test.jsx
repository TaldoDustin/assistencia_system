import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Reveal } from "./reveal";

describe("Reveal", () => {
  it("renderiza os filhos", () => {
    render(
      <Reveal>
        <p>conteúdo revelado</p>
      </Reveal>
    );
    expect(screen.getByText("conteúdo revelado")).toBeInTheDocument();
  });

  it("repassa className para o wrapper", () => {
    const { container } = render(
      <Reveal className="custom-reveal">
        <span>x</span>
      </Reveal>
    );
    expect(container.firstChild.className).toContain("custom-reveal");
  });
});
