/**
 * Identificador curto exibido por unidade — BR-073.
 *
 * Base: últimos 4 dígitos do IMEI. Quando dois (ou mais) identificadores exibidos
 * colidiriam, SÓ os que colidem crescem um dígito por vez (5, 6, …) até ficarem
 * únicos. Unidade sem IMEI real → "#<id>" (não colide com sufixos numéricos).
 *
 * Ver docs/product/research/DISCOVERY_LISTA_PRECOS_PUBLICA.md §3.
 */

const BASE = 4;

export interface UnidadeParaId {
  /** IMEI já normalizado (só dígitos) ou null. */
  imei: string | null;
  /** id interno do MercadoPhone (fallback e desempate estável). */
  id: number;
}

/** Retorna os identificadores curtos na mesma ordem das unidades recebidas. */
export function calcularIdsCurtos(unidades: UnidadeParaId[]): string[] {
  const resultado: string[] = unidades.map((u) => (u.imei ? "" : `#${u.id}`));

  const comImei = unidades
    .map((u, i) => ({ u, i }))
    .filter((x): x is { u: UnidadeParaId & { imei: string }; i: number } => x.u.imei !== null);

  const comprimento = new Map<number, number>();
  for (const { i } of comImei) comprimento.set(i, BASE);

  const sufixo = (imei: string, len: number) => imei.slice(-Math.min(len, imei.length));

  let mudou = true;
  while (mudou) {
    mudou = false;
    const grupos = new Map<string, number[]>();
    for (const { u, i } of comImei) {
      const s = sufixo(u.imei, comprimento.get(i)!);
      const g = grupos.get(s);
      if (g) g.push(i);
      else grupos.set(s, [i]);
    }
    for (const membros of grupos.values()) {
      if (membros.length < 2) continue;
      for (const i of membros) {
        const imei = (unidades[i]!.imei as string);
        const atual = comprimento.get(i)!;
        if (atual < imei.length) {
          comprimento.set(i, atual + 1);
          mudou = true;
        }
      }
    }
  }

  for (const { u, i } of comImei) resultado[i] = sufixo(u.imei, comprimento.get(i)!);
  return resultado;
}
