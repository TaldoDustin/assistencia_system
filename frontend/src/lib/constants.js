export const STATUS_OPTIONS = ["Em andamento", "Aguardando peca", "Finalizado", "Cancelado"];
export const OS_TYPES = ["Assistencia", "Garantia", "Upgrade"];
export const GARANTIA_DIAS = 90;

export function formatCurrency(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
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
