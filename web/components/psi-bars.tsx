"use client";

import { formatMetric } from "@/lib/format";
import { useFeatureLabel, useT } from "@/lib/i18n";
import type { DriftFeature } from "@/lib/types";

/**
 * Population stability per feature, worst first.
 *
 * The threshold is drawn as a rule across every bar rather than stated once, so
 * "how close is this to alerting" is answerable at a glance. Breaches carry the
 * word as well as the hue (FR-014b).
 */

export interface PsiRow {
  feature: string;
  psi: number;
  breach: boolean;
}

export function sortWorstFirst(features: Record<string, DriftFeature>): PsiRow[] {
  return Object.entries(features)
    .map(([feature, value]) => ({ feature, psi: value.psi, breach: value.breach }))
    .sort((a, b) => b.psi - a.psi);
}

/** Scale headroom so the threshold rule always sits inside the track. */
export function scaleMax(rows: PsiRow[], cutoff: number): number {
  return Math.max(cutoff * 1.5, ...rows.map((row) => row.psi)) || 1;
}

export function PsiBars({
  features,
  cutoff,
}: {
  features: Record<string, DriftFeature>;
  cutoff: number;
}) {
  const t = useT();
  const featureLabel = useFeatureLabel();
  const rows = sortWorstFirst(features);
  if (rows.length === 0) {
    return <p className="px-4 py-6 text-sm text-[var(--color-graphite)]">{t("psi.none")}</p>;
  }

  const max = scaleMax(rows, cutoff);
  const thresholdAt = (cutoff / max) * 100;

  return (
    <div>
      <p className="border-b border-[var(--color-rule)] px-4 py-2">
        <span className="label">{t("psi.alertThreshold")}</span>{" "}
        <span className="num text-[12px]">PSI ≥ {cutoff}</span>
      </p>

      <ol className="m-0 list-none p-0">
        {rows.map((row) => (
          <li
            key={row.feature}
            className="border-b border-[var(--color-rule)] px-4 py-3 last:border-b-0"
          >
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-[13px]">{featureLabel(row.feature)}</span>
              <span
                className="num text-[13px]"
                style={{ color: row.breach ? "var(--color-decline-ink)" : undefined }}
              >
                {formatMetric(row.psi, 3)}
              </span>
            </div>

            <div className="mt-1.5 flex items-center gap-3">
              <span
                className="relative h-2.5 flex-1 bg-[var(--color-sunk)]"
                role="img"
                aria-label={t(row.breach ? "psi.aria.breach" : "psi.aria.within", {
                  feature: featureLabel(row.feature),
                  psi: formatMetric(row.psi, 3),
                })}
              >
                <span
                  className="block h-full"
                  style={{
                    width: `${Math.min(100, (row.psi / max) * 100)}%`,
                    background: row.breach ? "var(--color-decline)" : "var(--color-form)",
                  }}
                />
                <span
                  className="absolute inset-y-[-3px] w-px bg-[var(--color-ink)]"
                  style={{ left: `${thresholdAt}%` }}
                />
              </span>
              <span
                className="label w-16 shrink-0 text-right"
                style={{ color: row.breach ? "var(--color-decline-ink)" : "var(--color-muted)" }}
              >
                {row.breach ? t("psi.breach") : t("psi.stable")}
              </span>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
