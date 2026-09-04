import { describe, expect, it } from "vitest";
import { calcularIdsCurtos } from "../lib/short-id.js";

describe("calcularIdsCurtos (BR-073)", () => {
  it("usa 4 dígitos quando não há colisão", () => {
    const ids = calcularIdsCurtos([
      { imei: "111111111111234", id: 1 },
      { imei: "222222222225678", id: 2 },
    ]);
    expect(ids).toEqual(["1234", "5678"]);
  });

  it("estende SÓ os que colidem", () => {
    const ids = calcularIdsCurtos([
      { imei: "356821833538890", id: 1 }, // ...8890
      { imei: "358206136828890", id: 2 }, // ...8890
      { imei: "999999999990000", id: 3 }, // ...0000 (único)
    ]);
    expect(ids[2]).toBe("0000");
    expect(ids[0]).toBe("38890");
    expect(ids[1]).toBe("28890");
    expect(new Set(ids).size).toBe(3);
  });

  it("cresce mais de um dígito se preciso (colisão tripla)", () => {
    const ids = calcularIdsCurtos([
      { imei: "111111111148890", id: 1 }, // ...48890
      { imei: "222222222148890", id: 2 }, // ...48890  -> colide em 5
      { imei: "333333333333890", id: 3 }, // ...33890  -> só colide em 4
    ]);
    // todos únicos
    expect(new Set(ids).size).toBe(3);
    // #1 e #2 precisaram passar de 5 dígitos
    expect(ids[0]!.length).toBeGreaterThanOrEqual(6);
    expect(ids[1]!.length).toBeGreaterThanOrEqual(6);
  });

  it("unidade sem IMEI vira #id", () => {
    const ids = calcularIdsCurtos([
      { imei: null, id: 99 },
      { imei: "111111111111234", id: 1 },
    ]);
    expect(ids[0]).toBe("#99");
    expect(ids[1]).toBe("1234");
  });

  it("é estável para o mesmo conjunto de entrada", () => {
    const entrada = [
      { imei: "356821833538890", id: 1 },
      { imei: "358206136828890", id: 2 },
      { imei: "351080694568890", id: 3 },
    ];
    expect(calcularIdsCurtos(entrada)).toEqual(calcularIdsCurtos(entrada));
  });
});
