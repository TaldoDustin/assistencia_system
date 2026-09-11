import { describe, expect, it } from "vitest";
import { calcularAjustesEstela, VENDEDOR_ESTELA } from "../lib/estela.js";
import type { Reserva } from "../lib/store.js";
import type { EstoqueItem } from "../lib/types.js";

const item = (o: Partial<EstoqueItem>): EstoqueItem =>
  ({
    id: 1, idCurto: "0001", tipoProduto: "IPHONE", modelo: "X", armazenamento: null, cor: null,
    estado: "Seminovo", saudeBateria: null, comDetalhe: false, precoVenda: null, dataEntrada: null,
    custo: null, margem: null, margemPct: null, diasEmEstoque: null, ...o,
  }) as EstoqueItem;

describe("calcularAjustesEstela (BR-082)", () => {
  it("item novo com comDetalhe e sem reserva → reservar", () => {
    const r = calcularAjustesEstela([item({ id: 1, comDetalhe: true })], {});
    expect(r.paraReservar).toEqual([1]);
    expect(r.paraLiberar).toEqual([]);
  });

  it("item com comDetalhe já reservado como Estela → não mexe de novo", () => {
    const reservas: Record<string, Reserva> = { "1": { vendedor: VENDEDOR_ESTELA, reservadoEm: "x" } };
    const r = calcularAjustesEstela([item({ id: 1, comDetalhe: true })], reservas);
    expect(r.paraReservar).toEqual([]);
    expect(r.paraLiberar).toEqual([]);
  });

  it("item deixou de ser comDetalhe e estava reservado como Estela → liberar", () => {
    const reservas: Record<string, Reserva> = { "1": { vendedor: VENDEDOR_ESTELA, reservadoEm: "x" } };
    const r = calcularAjustesEstela([item({ id: 1, comDetalhe: false })], reservas);
    expect(r.paraLiberar).toEqual([1]);
    expect(r.paraReservar).toEqual([]);
  });

  it("item deixou de ser comDetalhe mas a reserva é de um vendedor humano → nunca libera", () => {
    const reservas: Record<string, Reserva> = { "1": { vendedor: "Ana", reservadoEm: "x" } };
    const r = calcularAjustesEstela([item({ id: 1, comDetalhe: false })], reservas);
    expect(r.paraLiberar).toEqual([]);
  });

  it("item comDetalhe mas já reservado por vendedor humano → nunca sobrescreve", () => {
    const reservas: Record<string, Reserva> = { "1": { vendedor: "Ana", reservadoEm: "x" } };
    const r = calcularAjustesEstela([item({ id: 1, comDetalhe: true })], reservas);
    expect(r.paraReservar).toEqual([]);
  });

  it("vários itens: só ajusta quem precisa", () => {
    const reservas: Record<string, Reserva> = {
      "2": { vendedor: VENDEDOR_ESTELA, reservadoEm: "x" },
      "3": { vendedor: "Ana", reservadoEm: "x" },
    };
    const itens = [
      item({ id: 1, comDetalhe: true }), // sem reserva, com detalhe → reservar
      item({ id: 2, comDetalhe: true }), // já Estela → nada
      item({ id: 3, comDetalhe: true }), // reservado por humano → nada
      item({ id: 4, comDetalhe: false }), // sem detalhe, sem reserva → nada
    ];
    const r = calcularAjustesEstela(itens, reservas);
    expect(r.paraReservar).toEqual([1]);
    expect(r.paraLiberar).toEqual([]);
  });
});
