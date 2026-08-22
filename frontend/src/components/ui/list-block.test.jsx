import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ListBlock, ListBlockItem } from "./list-block";

describe("ListBlock", () => {
  it("separa os itens com divisor, sem moldura própria", () => {
    render(<ListBlock data-testid="block" />);
    // Checagem por token exato, não substring: "divide-border" contém "border" como
    // substring e faria um regex /\bborder\b/ (limite de palavra bate no hífen) dar falso
    // positivo mesmo numa implementação correta.
    const classes = screen.getByTestId("block").className.split(" ");
    expect(classes).toContain("divide-y");
    expect(classes).not.toContain("border");
    expect(classes.some((c) => c.startsWith("rounded"))).toBe(false);
    expect(classes).not.toContain("bg-card");
  });

  it("renderiza itens", () => {
    render(
      <ListBlock>
        <ListBlockItem>Item 1</ListBlockItem>
        <ListBlockItem>Item 2</ListBlockItem>
      </ListBlock>
    );
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
  });

  it("ListBlockItem interativo ganha hover/foco de interactiveRowClassName", () => {
    render(<ListBlockItem interactive data-testid="item">Item</ListBlockItem>);
    expect(screen.getByTestId("item").className).toContain("hover:bg-accent/50");
  });

  it("ListBlockItem não interativo não ganha classes de hover", () => {
    render(<ListBlockItem data-testid="item">Item</ListBlockItem>);
    expect(screen.getByTestId("item").className).not.toContain("hover:bg-accent/50");
  });
});
