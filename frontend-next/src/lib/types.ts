/**
 * Tipos espelhando as respostas reais da API Flask (fluxoly_blueprints_api.py).
 * Protótipo de avaliação — ver frontend-next/README.md e ADR-012.
 */

export interface Usuario {
  id: number;
  nome: string;
  perfil: string;
}

export interface DashboardSerieDia {
  date: string;
  value: number;
}

export interface DashboardNomeValor {
  name: string;
  value: number;
}

export interface DashboardVendedorResumo {
  vendedor: string;
  os_total: number;
  faturamento: number;
  lucro: number;
}

export interface DashboardCustoPorCategoria {
  categoria: string;
  total: number;
}

/** Resposta de GET /api/dashboard (fluxoly_blueprints_api.py:553) */
export interface DashboardData {
  faturamento_total: number;
  lucro_total: number;
  custo_consumido_periodo: number;
  custos_operacionais_periodo: number;
  resultado_liquido: number;
  ticket_medio: number;
  gasto_total_estoque: number;
  ordens_finalizadas: number;
  ordens_abertas: number;
  shopping_pendentes: number;
  shopping_urgentes: number;
  faturamento_por_dia: DashboardSerieDia[];
  lucro_por_tecnico: DashboardNomeValor[];
  servicos_mais_feitos: DashboardNomeValor[];
  resumo_por_vendedor: DashboardVendedorResumo[];
  custos_por_categoria: DashboardCustoPorCategoria[];
}

/** Um item de GET /api/ordens (fluxoly_blueprints_api.py:_os_row_to_dict) */
export interface OrdemServico {
  id: number;
  tipo: string;
  cliente: string;
  aparelho: string;
  tecnico: string;
  status: string;
  reparos: string[];
  reparo_ids: number[];
  reparo: string;
  vendedor: string;
  cor: string;
  imei: string;
  modelo: string;
  valor_cobrado: number;
  valor_descontado: number;
  custo_pecas: number;
  faturamento: number;
  lucro: number;
  data: string;
  observacoes: string;
  origem_integracao: string;
  id_externo_integracao: string;
}

/** Resposta de GET /api/ordens (fluxoly_blueprints_api.py:715) */
export interface OrdensListaResponse {
  ok: boolean;
  ordens: OrdemServico[];
  total: number;
  abertas: number;
  finalizadas: number;
}

export interface OrdemPeca {
  estoque_id: number;
  descricao: string;
  valor: number;
  fornecedor: string;
  quantidade: number;
  modelo: string;
}

/** GET /api/ordens/<id> — campos adicionais ao resumo de OrdemServico */
export interface OrdemServicoDetalhe extends OrdemServico {
  data_finalizado: string;
  pecas_usadas: OrdemPeca[];
}

export interface OrdemDetalheResponse {
  ok: boolean;
  ordem: OrdemServicoDetalhe;
}
