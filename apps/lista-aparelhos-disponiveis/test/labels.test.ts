import { describe, expect, it } from "vitest";
import { calcularMargem, diasEmEstoque, rotuloEstado } from "../lib/labels.js";

describe("rotuloEstado", () => {
  it("mapeia os estados conhecidos", () => {
    expect(rotuloEstado("SEMINOVO", false)).toBe("Seminovo");
    expect(rotuloEstado("LACRADO", false)).toBe("Lacrado");
    expect(rotuloEstado("CPO", false)).toBe("CPO");
    expect(rotuloEstado("OPEN BOX", false)).toBe("Open box");
  });
  it("acrescenta '(com detalhe)'", () => {
    expect(rotuloEstado("SEMINOVO", true)).toBe("Seminovo (com detalhe)");
    expect(rotuloEstado("LACRADO", true)).toBe("Lacrado (com detalhe)");
  });
  it("estado nulo → 'Não informado'", () => {
    expect(rotuloEstado(null, false)).toBe("Não informado");
  });
});

describe("calcularMargem", () => {
  it("calcula absoluto e percentual", () => {
    expect(calcularMargem(3000, 2000)).toEqual({ margem: 1000, margemPct: 50 });
  });
  it("custo 0/null ou venda null → indefinido", () => {
    expect(calcularMargem(3000, 0)).toEqual({ margem: null, margemPct: null });
    expect(calcularMargem(null, 2000)).toEqual({ margem: null, margemPct: null });
    expect(calcularMargem(3000, null)).toEqual({ margem: null, margemPct: null });
  });
});

describe("diasEmEstoque", () => {
  it("conta os dias", () => {
    expect(diasEmEstoque("2026-09-01", new Date("2026-09-11T00:00:00Z"))).toBe(10);
  });
  it("data futura → 0, data inválida/null → null", () => {
    expect(diasEmEstoque("2027-01-01", new Date("2026-09-11T00:00:00Z"))).toBe(0);
    expect(diasEmEstoque(null)).toBeNull();
    expect(diasEmEstoque("xx")).toBeNull();
  });
});
