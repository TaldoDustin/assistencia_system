// Fallback caso /api/constantes não retorne as listas (rede/erro) — espelha
// STATUS_OS_OPCOES/OS_TIPOS_OPCOES (fluxoly_core.py). Fonte de verdade real é
// a API — mesmo padrão de Produtos.jsx/Stock.jsx.
export const STATUS_OPTIONS_FALLBACK = ["Em andamento", "Aguardando peca", "Finalizado", "Cancelado"];
export const OS_TYPES_FALLBACK = ["Assistencia", "Garantia", "Upgrade"];

export function formatCurrency(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
}

// Compartilhado entre VendaDetalhe.jsx e Vendas.jsx (Historico) -- badge de
// status de venda, mesmo padrão visual dos badges de origem/status já usados
// em UnidadesSerializadas.jsx.
export const VENDA_STATUS_BADGE = {
  concluida: { label: "Concluída", className: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  cancelada: { label: "Cancelada", className: "bg-red-500/10 text-red-300 border-red-500/30" },
};

export function vendaStatusBadge(status) {
  return VENDA_STATUS_BADGE[status] || { label: status || "—", className: "bg-secondary/70 text-muted-foreground border-border" };
}

export function getOrderDisplayNumber(order) {
  if (!order) {
    return "";
  }

  // OS importada do MercadoPhone: usar o número real da integração, não o id
  // interno do Fluxoly — permite localizar a OS pelo número que o cliente/
  // MercadoPhone já usa, sincronizar atualizações e evitar duplicidade.
  if (order.origem_integracao === "mercado_phone" && order.id_externo_integracao) {
    return String(order.id_externo_integracao);
  }

  // OS nativa do Fluxoly: id interno, sem truncar (truncar via .slice(-5) foi
  // o bug real corrigido em 2026-06-09, não a preferência pelo número externo).
  if (order.id !== undefined && order.id !== null) {
    return String(order.id);
  }

  return String(order.id_externo_integracao || "");
}

export function getStatusColor(status) {
  switch (status) {
    case "Em andamento":   return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    case "Aguardando peca": return "bg-amber-500/20 text-amber-400 border-amber-500/30";
    case "Finalizado":     return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    case "Cancelado":      return "bg-red-500/20 text-red-400 border-red-500/30";
    default:               return "bg-muted text-muted-foreground border-border";
  }
}

export function isStatusOpen(status) {
  return status !== "Finalizado" && status !== "Cancelado";
}

export function calcularFaturamento(valor_cobrado, valor_descontado) {
  return (valor_cobrado || 0) > 0 ? (valor_cobrado || 0) : (valor_descontado || 0);
}

export function normalizeImei(imei) {
  const digits = (imei || "").replace(/\D/g, "");
  return digits.length >= 14 && digits.length <= 16 ? digits : "";
}
