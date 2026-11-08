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

export interface ScoreBand {
  min: number;
  color: string;
  label: string;
}

/** Score bands shared by the map colouring and the map legend, highest first. */
export const SCORE_BANDS: ScoreBand[] = [
  { min: 75, color: "#0f766e", label: "75–100" },
  { min: 60, color: "#65a30d", label: "60–74" },
  { min: 45, color: "#f59e0b", label: "45–59" },
  { min: 30, color: "#ea580c", label: "30–44" },
  { min: 0, color: "#dc2626", label: "0–29" },
];

export function scoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) {
    return "#94a3b8";
  }
  const band = SCORE_BANDS.find((candidate) => score >= candidate.min);
  return (band ?? SCORE_BANDS[SCORE_BANDS.length - 1]).color;
}
