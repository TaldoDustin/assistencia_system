import { describe, expect, it } from "vitest";
import { CAMPOS_PII, CAMPOS_PROIBIDOS_GERAL, buildSnapshots } from "../lib/snapshot.js";
import { availability, inventarioCru, storageSizes } from "./fixtures.js";

const AGORA = new Date("2026-09-03T12:00:00Z");

function build() {
  return buildSnapshots({ itens: inventarioCru, availability, storageSizes, agora: AGORA });
}

/** procura recursivamente por qualquer chave proibida em qualquer nível. */
function contémChave(obj: unknown, chaves: readonly string[]): string[] {
  const achados: string[] = [];
  const visitar = (v: unknown) => {
    if (Array.isArray(v)) return v.forEach(visitar);
    if (v && typeof v === "object") {
      for (const [k, val] of Object.entries(v)) {
        if (chaves.includes(k)) achados.push(k);
        visitar(val);
      }
    }
  };
  visitar(obj);
  return [...new Set(achados)];
}

describe("buildSnapshots — allowlist (BR-070/071)", () => {
  const { geral, estoque } = build();

  it("snapshot GERAL não contém nenhum campo proibido (custo, PII, IMEI, fiscal)", () => {
    expect(contémChave(geral, CAMPOS_PROIBIDOS_GERAL)).toEqual([]);
  });

  it("snapshot GERAL, verificado contra o JSON serializado inteiro", () => {
    const txt = JSON.stringify(geral);
    for (const proibido of CAMPOS_PROIBIDOS_GERAL) {
      expect(txt.includes(`"${proibido}"`), `vazou "${proibido}"`).toBe(false);
    }
  });

  it("nenhum IMEI real (14+ dígitos) aparece no JSON do snapshot GERAL", () => {
    expect(JSON.stringify(geral)).not.toMatch(/\d{14,}/);
  });

  it("snapshot ESTOQUE não contém PII, mas contém custo/margem", () => {
    expect(contémChave(estoque, CAMPOS_PII)).toEqual([]);
    expect(estoque.itens.some((i) => i.custo != null)).toBe(true);
    expect(estoque.itens.some((i) => i.margem != null)).toBe(true);
  });

  it("nenhum IMEI real no snapshot ESTOQUE", () => {
    expect(JSON.stringify(estoque)).not.toMatch(/\d{14,}/);
  });
});

describe("buildSnapshots — conteúdo", () => {
  const { geral, estoque, diagnostico } = build();

  it("geral e estoque têm o mesmo número de itens", () => {
    expect(geral.total).toBe(estoque.total);
  });

  it("cada item tem id, idCurto, modelo, estado, preço ou null", () => {
    for (const i of geral.itens) {
      expect(typeof i.id).toBe("number");
      expect(i.idCurto.length).toBeGreaterThan(0);
      expect(i.modelo).toBeTruthy();
      expect(i.estado).toBeTruthy();
      expect(i.precoVenda === null || typeof i.precoVenda === "number").toBe(true);
    }
  });

  it("armazenamento resolvido para iPhones (via gbDescricao)", () => {
    const iph = geral.itens.filter((i) => i.tipoProduto === "IPHONE");
    expect(iph.length).toBeGreaterThan(0);
    expect(iph.every((i) => i.armazenamento && /GB|TB/.test(i.armazenamento))).toBe(true);
  });

  it("Apple Watch pode ficar sem armazenamento", () => {
    const w = geral.itens.filter((i) => i.tipoProduto === "APPLE WATCH");
    if (w.length) expect(w.every((i) => i.armazenamento === null)).toBe(true);
  });

  it("estado 'com detalhe' recebe rótulo", () => {
    const cd = estoque.itens.filter((i) => i.comDetalhe);
    expect(cd.every((i) => /com detalhe/i.test(i.estado))).toBe(true);
  });

  it("diagnóstico bate", () => {
    expect(diagnostico.aposDedup).toBe(geral.total);
    expect(diagnostico.aposFiltro).toBeGreaterThanOrEqual(diagnostico.aposDedup);
  });

  it("idCurto único na lista exibida", () => {
    const ids = geral.itens.map((i) => i.idCurto);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
