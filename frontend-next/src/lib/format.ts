export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value ?? 0);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value ?? 0);
}

export function formatDate(value: string): string {
  if (!value) return "—";
  const [datePart] = value.split(" ");
  const [year, month, day] = (datePart || "").split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}
