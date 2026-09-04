/**
 * Abstração de armazenamento (ADR-013 Q4 — Vercel KV).
 *
 * `KvStore` usa @vercel/kv em produção. `MemoryStore` serve testes e o modo
 * degradado local. As duas implementam a mesma interface mínima.
 */
import type { DetalheNota, EstoqueItem, GeralItem, Snapshot } from "./types.js";

export interface Reserva {
  vendedor: string;
  reservadoEm: string;
}

export interface SyncStatus {
  em: string;
  ok: boolean;
  erro?: string;
  diagnostico?: unknown;
}

export interface Store {
  getSnapshotGeral(): Promise<Snapshot<GeralItem> | null>;
  getSnapshotEstoque(): Promise<Snapshot<EstoqueItem> | null>;
  setSnapshots(geral: Snapshot<GeralItem>, estoque: Snapshot<EstoqueItem>): Promise<void>;
  getReservas(): Promise<Record<string, Reserva>>;
  reservar(id: number, reserva: Reserva): Promise<"ok" | "ja-reservado">;
  desreservar(id: number): Promise<void>;
  getDetalhes(): Promise<Record<string, DetalheNota>>;
  /** texto vazio limpa a nota. */
  setDetalhe(id: number, texto: string): Promise<void>;
  getSyncStatus(): Promise<SyncStatus | null>;
  setSyncStatus(s: SyncStatus): Promise<void>;
  /** Contador simples de rate-limit por chave; retorna o total após incrementar. */
  bumpRate(chave: string, janelaSegundos: number): Promise<number>;
}

interface RedisLike {
  get(key: string): Promise<unknown>;
  set(key: string, value: unknown): Promise<unknown>;
  hgetall(key: string): Promise<Record<string, unknown> | null>;
  hset(key: string, obj: Record<string, unknown>): Promise<unknown>;
  hsetnx(key: string, field: string, value: unknown): Promise<number>;
  hdel(key: string, field: string): Promise<unknown>;
  incr(key: string): Promise<number>;
  expire(key: string, seconds: number): Promise<unknown>;
}

const K = {
  geral: "snapshot:geral",
  estoque: "snapshot:estoque",
  reservas: "reservas",
  detalhes: "detalhes",
  sync: "sync:last",
  rate: (c: string) => `rate:${c}`,
};

const DETALHE_MAX = 280;


export class MemoryStore implements Store {
  private data = new Map<string, unknown>();
  private hashes = new Map<string, Map<string, unknown>>();

  async getSnapshotGeral() {
    return (this.data.get(K.geral) as Snapshot<GeralItem>) ?? null;
  }
  async getSnapshotEstoque() {
    return (this.data.get(K.estoque) as Snapshot<EstoqueItem>) ?? null;
  }
  async setSnapshots(geral: Snapshot<GeralItem>, estoque: Snapshot<EstoqueItem>) {
    this.data.set(K.geral, geral);
    this.data.set(K.estoque, estoque);
  }
  async getReservas() {
    const h = this.hashes.get(K.reservas);
    return h ? (Object.fromEntries(h) as Record<string, Reserva>) : {};
  }
  async reservar(id: number, reserva: Reserva) {
    const h = this.hashes.get(K.reservas) ?? new Map();
    if (h.has(String(id))) return "ja-reservado" as const;
    h.set(String(id), reserva);
    this.hashes.set(K.reservas, h);
    return "ok" as const;
  }
  async desreservar(id: number) {
    this.hashes.get(K.reservas)?.delete(String(id));
  }
  async getDetalhes() {
    const h = this.hashes.get(K.detalhes);
    return h ? (Object.fromEntries(h) as Record<string, DetalheNota>) : {};
  }
  async setDetalhe(id: number, texto: string) {
    const h = this.hashes.get(K.detalhes) ?? new Map();
    const t = texto.trim().slice(0, DETALHE_MAX);
    if (t) h.set(String(id), { texto: t, editadoEm: new Date().toISOString() } satisfies DetalheNota);
    else h.delete(String(id));
    this.hashes.set(K.detalhes, h);
  }
  async getSyncStatus() {
    return (this.data.get(K.sync) as SyncStatus) ?? null;
  }
  async setSyncStatus(s: SyncStatus) {
    this.data.set(K.sync, s);
  }
  async bumpRate(chave: string, _janelaSegundos: number) {
    const k = K.rate(chave);
    const n = ((this.data.get(k) as number) ?? 0) + 1;
    this.data.set(k, n);
    return n;
  }
}

/**
 * Implementação Redis gerenciado — carregada só quando há credencial (produção).
 * O "Vercel KV" foi descontinuado e migrado para Upstash Redis (Vercel Marketplace);
 * a API Redis usada aqui (get/set/hget…/incr/expire) é a mesma nos dois.
 */
export class KvStore implements Store {
  // cliente @upstash/redis (ou compatível)
  constructor(private kv: RedisLike) {}

  async getSnapshotGeral() {
    return (await this.kv.get(K.geral)) as Snapshot<GeralItem> | null;
  }
  async getSnapshotEstoque() {
    return (await this.kv.get(K.estoque)) as Snapshot<EstoqueItem> | null;
  }
  async setSnapshots(geral: Snapshot<GeralItem>, estoque: Snapshot<EstoqueItem>) {
    await Promise.all([this.kv.set(K.geral, geral), this.kv.set(K.estoque, estoque)]);
  }
  async getReservas() {
    return ((await this.kv.hgetall(K.reservas)) as Record<string, Reserva>) ?? {};
  }
  async reservar(id: number, reserva: Reserva) {
    const criado = await this.kv.hsetnx(K.reservas, String(id), reserva);
    return criado ? ("ok" as const) : ("ja-reservado" as const);
  }
  async desreservar(id: number) {
    await this.kv.hdel(K.reservas, String(id));
  }
  async getDetalhes() {
    return ((await this.kv.hgetall(K.detalhes)) as Record<string, DetalheNota>) ?? {};
  }
  async setDetalhe(id: number, texto: string) {
    const t = texto.trim().slice(0, DETALHE_MAX);
    if (t) {
      await this.kv.hset(K.detalhes, {
        [String(id)]: { texto: t, editadoEm: new Date().toISOString() } satisfies DetalheNota,
      });
    } else {
      await this.kv.hdel(K.detalhes, String(id));
    }
  }
  async getSyncStatus() {
    return (await this.kv.get(K.sync)) as SyncStatus | null;
  }
  async setSyncStatus(s: SyncStatus) {
    await this.kv.set(K.sync, s);
  }
  async bumpRate(chave: string, janelaSegundos: number) {
    const k = K.rate(chave);
    const n = (await this.kv.incr(k)) as number;
    if (n === 1) await this.kv.expire(k, janelaSegundos);
    return n;
  }
}

let cached: Store | null = null;

function redisEnv(): { url: string; token: string } | null {
  const url = process.env.KV_REST_API_URL ?? process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.KV_REST_API_TOKEN ?? process.env.UPSTASH_REDIS_REST_TOKEN;
  return url && token ? { url, token } : null;
}

/** Store de produção (Upstash Redis) se houver credencial; senão MemoryStore. */
export async function getStore(): Promise<Store> {
  if (cached) return cached;
  const env = redisEnv();
  if (env) {
    const { Redis } = await import("@upstash/redis");
    cached = new KvStore(new Redis(env) as unknown as RedisLike);
  } else {
    cached = new MemoryStore();
  }
  return cached;
}

/** Só para testes. */
export function _setStoreParaTeste(s: Store | null): void {
  cached = s;
}
