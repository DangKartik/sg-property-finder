export function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }
  return new Intl.NumberFormat("en-SG", {
    style: "currency",
    currency: "SGD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) {
    return "—";
  }
  return new Intl.NumberFormat("en-SG", {
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "—";
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("en-SG");
}

export function scoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) {
    return "#94a3b8";
  }
  if (score >= 75) return "#0f766e";
  if (score >= 60) return "#65a30d";
  if (score >= 45) return "#f59e0b";
  if (score >= 30) return "#ea580c";
  return "#dc2626";
}
