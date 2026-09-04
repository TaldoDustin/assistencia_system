/**
 * Cliente da API nova do MercadoPhone (platform.mercadophone.tech).
 * Só leitura. A `X-API-Key` vem de env var (nunca do repositório, nunca do cliente) — ADR-013.
 */
import type { AvailabilityLookup, RawInventoryItem, StorageSizeLookup } from "./types.js";

const BASE = "https://platform.mercadophone.tech/api/v1";
const PAGE_LIMIT = 300;
const REQUEST_TIMEOUT_MS = 30_000;
const MAX_PAGES = 50; // trava de segurança (~15k itens)

export interface MpClientOptions {
  apiKey: string;
  /** injeção para teste */
  fetchImpl?: typeof fetch;
}

interface PageResponse<T> {
  total: number;
  items: T[];
  page: number;
  limit: number;
}

async function getJson<T>(
  url: string,
  apiKey: string,
  fetchImpl: typeof fetch,
): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetchImpl(url, {
      headers: { "X-API-Key": apiKey, Accept: "application/json" },
      signal: ctrl.signal,
    });
    if (!res.ok) {
      throw new Error(`MercadoPhone ${res.status} em ${url.replace(BASE, "")}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export class MercadoPhoneClient {
  private readonly apiKey: string;
  private readonly fetchImpl: typeof fetch;

  constructor(opts: MpClientOptions) {
    if (!opts.apiKey) throw new Error("MERCADOPHONE_API_KEY ausente");
    this.apiKey = opts.apiKey;
    this.fetchImpl = opts.fetchImpl ?? fetch;
  }

  /** Puxa TODAS as páginas de /inventory. */
  async listarInventarioCompleto(): Promise<RawInventoryItem[]> {
    const out: RawInventoryItem[] = [];
    let total = 0;
    for (let page = 1; page <= MAX_PAGES; page++) {
      const data = await getJson<PageResponse<RawInventoryItem>>(
        `${BASE}/inventory?limit=${PAGE_LIMIT}&page=${page}`,
        this.apiKey,
        this.fetchImpl,
      );
      total = typeof data.total === "number" ? data.total : total;
      out.push(...data.items);
      // Página vazia antes de esgotar o total = glitch da API. Aborta para o
      // sync preservar o snapshot anterior em vez de sobrescrever com dados parciais.
      if (data.items.length === 0 && total > 0 && out.length < total) {
        throw new Error(`inventário incompleto: página ${page} vazia com ${out.length}/${total} itens`);
      }
      if (data.items.length < PAGE_LIMIT) break;
      if (total > 0 && out.length >= total) break;
    }
    return out;
  }

  async listarAvailability(): Promise<AvailabilityLookup[]> {
    const data = await getJson<PageResponse<AvailabilityLookup>>(
      `${BASE}/catalog/availability?limit=100`,
      this.apiKey,
      this.fetchImpl,
    );
    return data.items;
  }

  async listarStorageSizes(): Promise<StorageSizeLookup[]> {
    const data = await getJson<PageResponse<StorageSizeLookup>>(
      `${BASE}/catalog/storage-sizes?limit=100`,
      this.apiKey,
      this.fetchImpl,
    );
    return data.items;
  }
}
