import { describe, it, expect } from "vitest";
import { contrastRatio } from "./contrast";

describe("contrastRatio", () => {
  it("preto sobre branco tem contraste 21:1 (referência WCAG)", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 0);
  });

  it("mesma cor tem contraste 1:1", () => {
    expect(contrastRatio("#336699", "#336699")).toBeCloseTo(1, 5);
  });

  it("é simétrico -- ordem dos argumentos não importa", () => {
    const a = contrastRatio("#1F7A50", "#FFFFFF");
    const b = contrastRatio("#FFFFFF", "#1F7A50");
    expect(a).toBeCloseTo(b, 5);
  });
});
