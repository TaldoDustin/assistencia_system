import { describe, expect, it } from "vitest";
import { compararItens, compararItensEstoque } from "../lib/ordenar.js";
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

const ordenado = (arr: EstoqueItem[]) =>
  [...arr].sort(compararItens).map((x) => `${x.modelo}/${x.estado}/${x.armazenamento}/${x.cor}/${x.saudeBateria}`);

describe("compararItens", () => {
  it("modelo em ordem natural (11 antes de 12, PRO antes de PRO MAX)", () => {
    const arr = [
      it_({ modelo: "IPHONE 12 PRO MAX" }),
      it_({ modelo: "IPHONE 11" }),
      it_({ modelo: "IPHONE 12" }),
      it_({ modelo: "IPHONE 12 PRO" }),
      it_({ modelo: "IPHONE 9" }),
    ];
    expect(ordenado(arr).map((s) => s.split("/")[0])).toEqual([
      "IPHONE 9", "IPHONE 11", "IPHONE 12", "IPHONE 12 PRO", "IPHONE 12 PRO MAX",
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

  it("mesmo modelo+estado: por GB crescente, sem GB reconhecível por último", () => {
    const arr = [
      it_({ armazenamento: null }),
      it_({ armazenamento: "256GB" }),
      it_({ armazenamento: "64GB" }),
      it_({ armazenamento: "128GB" }),
    ];
    expect(ordenado(arr).map((s) => s.split("/")[2])).toEqual(["64GB", "128GB", "256GB", "null"]);
  });

  it("mesmo GB: por cor em ordem alfabética (pt-BR)", () => {
    const arr = [
      it_({ armazenamento: "128GB", cor: "Rosa" }),
      it_({ armazenamento: "128GB", cor: "Azul" }),
      it_({ armazenamento: "128GB", cor: "Preto" }),
    ];
    expect(ordenado(arr).map((s) => s.split("/")[3])).toEqual(["Azul", "Preto", "Rosa"]);
  });

  it("mesmo GB+cor: por saúde de bateria decrescente (maior % primeiro)", () => {
    const arr = [
      it_({ armazenamento: "128GB", cor: "Azul", saudeBateria: 82 }),
      it_({ armazenamento: "128GB", cor: "Azul", saudeBateria: 100 }),
      it_({ armazenamento: "128GB", cor: "Azul", saudeBateria: null }),
      it_({ armazenamento: "128GB", cor: "Azul", saudeBateria: 91 }),
    ];
    expect(ordenado(arr).map((s) => s.split("/")[4])).toEqual(["100", "91", "82", "null"]);
  });
});

describe("compararItensEstoque — critério extra de dias parado", () => {
  const ordenadoEstoque = (arr: EstoqueItem[]) =>
    [...arr].sort(compararItensEstoque).map((x) => x.diasEmEstoque);

  it("mesmo GB+cor+bateria: mais dias parado primeiro", () => {
    const base = { armazenamento: "128GB", cor: "Azul", saudeBateria: 90 } as const;
    const arr = [
      it_({ ...base, diasEmEstoque: 10 }),
      it_({ ...base, diasEmEstoque: 90 }),
      it_({ ...base, diasEmEstoque: null }),
      it_({ ...base, diasEmEstoque: 45 }),
    ];
    expect(ordenadoEstoque(arr)).toEqual([90, 45, 10, null]);
  });

  it("dias parado só desempata DEPOIS de GB/cor/bateria", () => {
    const arr = [
      it_({ armazenamento: "256GB", diasEmEstoque: 5 }),
      it_({ armazenamento: "64GB", diasEmEstoque: 200 }),
    ];
    // 64GB vem antes de 256GB mesmo tendo bem menos dias parado que o de 256GB
    expect([...arr].sort(compararItensEstoque).map((x) => x.armazenamento)).toEqual(["64GB", "256GB"]);
  });

  it("a área Geral NÃO usa dias parado — mesmo conjunto, ordem diferente da Estoque quando só dias parado muda", () => {
    const base = { armazenamento: "128GB", cor: "Azul", saudeBateria: 90 } as const;
    const a = it_({ ...base, id: 1, diasEmEstoque: 5 });
    const b = it_({ ...base, id: 2, diasEmEstoque: 200 });
    // Geral: empata em tudo que ela conhece, desempata por id (nunca por dias parado)
    expect(compararItens(a, b)).toBeLessThan(0);
    // Estoque: b tem muito mais dias parado, vem primeiro mesmo com id maior
    expect(compararItensEstoque(a, b)).toBeGreaterThan(0);
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

  it("dentro do mesmo modelo+estado, a área Estoque vem ordenada por dias parado decrescente", () => {
    const { estoque } = buildSnapshots({ itens: inventarioCru, availability, storageSizes });
    const porGrupo = new Map<string, number[]>();
    for (const it of estoque.itens) {
      const k = `${it.modelo}·${it.estado}·${it.armazenamento}·${it.cor}·${it.saudeBateria}`;
      const arr = porGrupo.get(k) ?? [];
      arr.push(it.diasEmEstoque ?? -1);
      porGrupo.set(k, arr);
    }
    for (const dias of porGrupo.values()) {
      for (let k = 1; k < dias.length; k++) expect(dias[k]!).toBeLessThanOrEqual(dias[k - 1]!);
    }
  });
});
