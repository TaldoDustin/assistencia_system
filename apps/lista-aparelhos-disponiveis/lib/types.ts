/**
 * Tipos do MercadoPhone (API nova, platform.mercadophone.tech) e do snapshot interno.
 * Ver docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md.
 */

/** Item cru de GET /api/v1/inventory (só os campos que consumimos; a API devolve muitos outros). */
export interface RawInventoryItem {
  id: number;
  imei: string | null;
  imei2: string | null;
  serialNumber: string | null;
  aparelhoDescricao: string | null;
  quantidade: number | null;
  snAcessorio: 0 | 1 | null;
  snPeca: 0 | 1 | null;
  snServico: 0 | 1 | null;
  tipoProdutoId: string | number | null;
  tipoProdutoDescricao: string | null;
  produtoDisponibilidadeId: number | null;
  disponibilidade: string | null;
  estadoProdutoId: number | null;
  estadoProdutoDescricao: string | null;
  gbId: number | null;
  gbDescricao: string | null;
  corDescricao: string | null;
  saudeBateria: number | null;
  valorVenda: number | null;
  valorCusto: number | null;
  dataEntrada: string | null;
  dataModificacao: string | null;
  // Campos sensíveis — nunca copiados para o snapshot (ver allowlist em snapshot.ts).
  fornecedorNome?: string | null;
  fornecedorId?: number | null;
  clienteNome?: string | null;
  clienteId?: number | null;
  obs?: string | null;
  observacaoCatalogo?: string | null;
  [k: string]: unknown;
}

/** Situação de estoque (GET /api/v1/catalog/availability). */
export interface AvailabilityLookup {
  id: number;
  name: string;
  snExibirPdv: number | null;
}

/** Tamanho de armazenamento (GET /api/v1/catalog/storage-sizes) — usado como fallback do gbDescricao. */
export interface StorageSizeLookup {
  id: number;
  size: string;
}

/** Linha exibida na área Geral (vendedor). NUNCA contém custo, PII, IMEI completo. */
export interface GeralItem {
  /** id interno do MercadoPhone — estável, não sensível. Chave da reserva (BR-078). */
  id: number;
  /** Identificador curto exibido — sufixo do IMEI (BR-073) ou "#<id>". */
  idCurto: string;
  tipoProduto: string;
  modelo: string;
  armazenamento: string | null;
  cor: string | null;
  estado: string;
  saudeBateria: number | null;
  comDetalhe: boolean;
  /** null quando a fonte não tem preço → a UI mostra "sob consulta". */
  precoVenda: number | null;
  dataEntrada: string | null;
}

/** Linha da área Estoque (organizador). Geral + custo/margem/dias. */
export interface EstoqueItem extends GeralItem {
  custo: number | null;
  margem: number | null;
  margemPct: number | null;
  diasEmEstoque: number | null;
  reservado?: { vendedor: string; reservadoEm: string };
}

export interface Snapshot<T> {
  geradoEm: string;
  total: number;
  itens: T[];
}

export type Papel = "geral" | "estoque";
