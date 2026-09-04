import { describe, expect, it } from "vitest";
import { chaveDedup, dedup, imeiReal } from "../lib/dedup.js";
import type { RawInventoryItem } from "../lib/types.js";

const it_ = (o: Partial<RawInventoryItem>): RawInventoryItem =>
  ({ id: 1, imei: null, dataModificacao: null, ...o }) as RawInventoryItem;

describe("imeiReal", () => {
  it("aceita 14-15 dígitos", () => {
    expect(imeiReal("356821833538890")).toBe("356821833538890");
    expect(imeiReal("35682183353889")).toBe("35682183353889");
  });
  it("rejeita 0, vazio, curto, null", () => {
    expect(imeiReal("0")).toBeNull();
    expect(imeiReal("000000000000000")).toBeNull();
    expect(imeiReal("")).toBeNull();
    expect(imeiReal(null)).toBeNull();
    expect(imeiReal("1234")).toBeNull();
  });
});

describe("chaveDedup", () => {
  it("usa IMEI quando existe", () => {
    expect(chaveDedup(it_({ imei: "356821833538890" }))).toBe("imei:356821833538890");
  });
  it("cai para id quando não há IMEI real", () => {
    expect(chaveDedup(it_({ id: 42, imei: "0" }))).toBe("id:42");
  });
});

describe("dedup (BR-072)", () => {
  it("colapsa mesmo IMEI, vence dataModificacao mais recente", () => {
    const antigo = it_({ id: 1, imei: "356821833538890", dataModificacao: "2025-01-01 00:00:00", valorVenda: 1000 });
    const novo = it_({ id: 2, imei: "356821833538890", dataModificacao: "2026-01-01 00:00:00", valorVenda: 2000 });
    const out = dedup([antigo, novo]);
    expect(out).toHaveLength(1);
    expect(out[0]!.id).toBe(2);
  });
  it("mantém unidades sem IMEI separadas por id", () => {
    const a = it_({ id: 10, imei: null });
    const b = it_({ id: 11, imei: null });
    expect(dedup([a, b])).toHaveLength(2);
  });
  it("preserva a ordem das sobreviventes", () => {
    const a = it_({ id: 1, imei: "111111111111111" });
    const b = it_({ id: 2, imei: "222222222222222" });
    const c = it_({ id: 3, imei: "111111111111111", dataModificacao: "2030-01-01 00:00:00" });
    const out = dedup([a, b, c]);
    expect(out.map((x) => x.id)).toEqual([2, 3]);
  });
});
