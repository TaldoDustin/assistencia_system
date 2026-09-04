import { describe, expect, it } from "vitest";
import {
  filtrarAparelhosDisponiveis,
  idsVisiveisNaVitrine,
  isAparelho,
  isDisponivel,
} from "../lib/filter.js";
import type { RawInventoryItem } from "../lib/types.js";
import { availability, inventarioCru } from "./fixtures.js";

const raw = (o: Partial<RawInventoryItem>): RawInventoryItem =>
  ({ id: 1, imei: null, imei2: null, serialNumber: null, aparelhoDescricao: "X", quantidade: 1,
     snAcessorio: 0, snPeca: 0, snServico: 0, tipoProdutoId: "3719", tipoProdutoDescricao: "IPHONE",
     produtoDisponibilidadeId: 1, disponibilidade: null, estadoProdutoId: null, estadoProdutoDescricao: null,
     gbId: null, gbDescricao: null, corDescricao: null, saudeBateria: null, valorVenda: 1000, valorCusto: 500,
     dataEntrada: null, dataModificacao: null, ...o }) as RawInventoryItem;

describe("isAparelho (BR-074)", () => {
  it("inclui iPhone/iPad/MacBook/Apple Watch", () => {
    for (const t of ["3719", "4959", "4960", "4961"]) {
      expect(isAparelho(raw({ tipoProdutoId: t }))).toBe(true);
    }
  });
  it("exclui acessório mesmo com tipo de aparelho", () => {
    expect(isAparelho(raw({ snAcessorio: 1 }))).toBe(false);
  });
  it("exclui AirPods/Pencil/serviço/brinde (tipos fora da lista)", () => {
    for (const t of ["7911", "7303", "23803", "50704", "100419"]) {
      expect(isAparelho(raw({ tipoProdutoId: t }))).toBe(false);
    }
  });
  it("exclui peça e serviço", () => {
    expect(isAparelho(raw({ snPeca: 1 }))).toBe(false);
    expect(isAparelho(raw({ snServico: 1 }))).toBe(false);
  });
});

describe("isDisponivel (BR-075)", () => {
  const ids = idsVisiveisNaVitrine(availability);
  it("aceita só situações com snExibirPdv === 1", () => {
    expect([...ids].sort()).toEqual([1, 62177]);
  });
  it("rejeita Laboratório e ANALISE", () => {
    expect(isDisponivel(raw({ produtoDisponibilidadeId: 2 }), ids)).toBe(false);
    expect(isDisponivel(raw({ produtoDisponibilidadeId: 61058 }), ids)).toBe(false);
  });
  it("aceita 'com detalhe'", () => {
    expect(isDisponivel(raw({ produtoDisponibilidadeId: 62177 }), ids)).toBe(true);
  });
});

describe("filtrarAparelhosDisponiveis sobre a fixture real", () => {
  const out = filtrarAparelhosDisponiveis(inventarioCru, availability);
  it("não devolve nenhum acessório", () => {
    expect(out.every((i) => i.snAcessorio === 0)).toBe(true);
  });
  it("só devolve tipos de aparelho", () => {
    expect(out.every((i) => ["3719", "4959", "4960", "4961"].includes(String(i.tipoProdutoId)))).toBe(true);
  });
  it("só devolve unidades disponíveis para venda", () => {
    expect(out.every((i) => [1, 62177].includes(i.produtoDisponibilidadeId as number))).toBe(true);
  });
  it("devolve pelo menos alguns aparelhos", () => {
    expect(out.length).toBeGreaterThan(5);
  });
});
