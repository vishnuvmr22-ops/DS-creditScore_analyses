import type { Decision } from "./types";

/** Probabilities are shown at the precision the service reports them. */
export function formatPd(value: number): string {
  return value.toFixed(4);
}

export function formatPercent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatMetric(value: number, digits = 4): string {
  return value.toFixed(digits);
}

export function formatSigned(value: number, digits = 3): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${Math.abs(value).toFixed(digits)}`;
}

export function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toISOString().replace("T", " ").replace(/\.\d+/, "").replace("Z", " UTC");
}

export function decisionClass(decision: Decision | string): string {
  return `verdict verdict-${decision}`;
}

export function isRiskIncreasing(direction: string): boolean {
  return direction === "increases_risk";
}
