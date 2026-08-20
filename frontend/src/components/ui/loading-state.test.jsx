import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { ListSkeleton, CardGridSkeleton } from "./loading-state";

describe("ListSkeleton", () => {
  it("renderiza a quantidade padrão de linhas", () => {
    const { container } = render(<ListSkeleton />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(6);
  });

  it("respeita a quantidade de linhas informada", () => {
    const { container } = render(<ListSkeleton rows={3} />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(3);
  });
});

describe("CardGridSkeleton", () => {
  it("renderiza a quantidade padrão de cards", () => {
    const { container } = render(<CardGridSkeleton />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(4);
  });

  it("respeita a quantidade de cards informada", () => {
    const { container } = render(<CardGridSkeleton count={8} />);
    expect(container.querySelectorAll(".animate-pulse")).toHaveLength(8);
  });
});
