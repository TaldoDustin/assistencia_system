import { describe, expect, it } from "vitest";
import { compararItens } from "../lib/ordenar.js";
import { buildSnapshots } from "../lib/snapshot.js";
import type { EstoqueItem } from "../lib/types.js";
import { availability, inventarioCru, storageSizes } from "./fixtures.js";

const it_ = (o: Partial<EstoqueItem>): EstoqueItem =>
  ({
    id: 1, idCurto: "0000", tipoProduto: "IPHONE", modelo: "IPHONE 11",
    armazenamento: null, cor: null, estado: "Seminovo", saudeBateria: null,
    comDetalhe: false, precoVenda: 1000, dataEntrada: null,
    custo: null, margem: null, margemPct: null, diasEmEstoque: null, ...o,
  }) as EstoqueItem;

const ordenado = (arr: EstoqueItem[]) => [...arr].sort(compararItens).map((x) => `${x.modelo}/${x.estado}/${x.precoVenda}`);

describe("compararItens", () => {
  it("modelo em ordem natural (11 antes de 12, PRO antes de PRO MAX)", () => {
    const arr = [
      it_({ modelo: "IPHONE 12 PRO MAX" }),
      it_({ modelo: "IPHONE 11" }),
      it_({ modelo: "IPHONE 12" }),
      it_({ modelo: "IPHONE 12 PRO" }),
      it_({ modelo: "IPHONE 9" }),
    ];
    expect(ordenado(arr)).toEqual([
      "IPHONE 9/Seminovo/1000",
      "IPHONE 11/Seminovo/1000",
      "IPHONE 12/Seminovo/1000",
      "IPHONE 12 PRO/Seminovo/1000",
      "IPHONE 12 PRO MAX/Seminovo/1000",
    ]);
  });

  it("mesmo modelo: Lacrado antes de Seminovo antes de 'com detalhe'", () => {
    const arr = [
      it_({ modelo: "IPHONE 17 PRO MAX", estado: "Seminovo (com detalhe)" }),
      it_({ modelo: "IPHONE 17 PRO MAX", estado: "Seminovo" }),
      it_({ modelo: "IPHONE 17 PRO MAX", estado: "Lacrado" }),
    ];
    expect(ordenado(arr).map((s) => s.split("/")[1])).toEqual([
      "Lacrado", "Seminovo", "Seminovo (com detalhe)",
    ]);
  });

  it("tipos: iPhone < iPad < MacBook < Apple Watch", () => {
    const arr = [
      it_({ tipoProduto: "APPLE WATCH", modelo: "APPLE WATCH S11" }),
      it_({ tipoProduto: "MACBOOK", modelo: "MACBOOK AIR M1" }),
      it_({ tipoProduto: "IPAD", modelo: "IPAD 11" }),
      it_({ tipoProduto: "IPHONE", modelo: "IPHONE 17" }),
    ];
    expect([...arr].sort(compararItens).map((x) => x.tipoProduto)).toEqual([
      "IPHONE", "IPAD", "MACBOOK", "APPLE WATCH",
    ]);
  });

  it("mesmo modelo+estado: por preço crescente, sem preço por último", () => {
    const arr = [
      it_({ precoVenda: null }),
      it_({ precoVenda: 3000 }),
      it_({ precoVenda: 1500 }),
    ];
    expect(ordenado(arr).map((s) => s.split("/")[2])).toEqual(["1500", "3000", "null"]);
  });
});

describe("snapshot já sai ordenado", () => {
  it("os grupos (modelo+estado) saem em sequência natural", () => {
    const { geral } = buildSnapshots({ itens: inventarioCru, availability, storageSizes });
    // extrai a sequência de modelos únicos na ordem do snapshot
    const seq: string[] = [];
    for (const i of geral.itens) if (seq[seq.length - 1] !== i.modelo) seq.push(i.modelo);
    const iphones = seq.filter((m) => m.startsWith("IPHONE") && /\d/.test(m));
    const nums = iphones.map((m) => parseInt(m.match(/\d+/)![0], 10));
    // a sequência dos números de geração é não-decrescente
    for (let k = 1; k < nums.length; k++) expect(nums[k]!).toBeGreaterThanOrEqual(nums[k - 1]!);
  });
});
