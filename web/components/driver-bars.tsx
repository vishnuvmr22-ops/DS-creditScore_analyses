"use client";

import { formatSigned, isRiskIncreasing } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { Driver } from "@/lib/types";

/**
 * The model's top drivers, made comparable (FR-003).
 *
 * Bars are scaled against the largest driver in the set, so the reader sees
 * relative weight rather than an absolute number they have no reference for.
 * Direction is carried by a word as well as a hue (FR-014b) — "increases risk"
 * is legible in greyscale and to a colour-blind reader.
 */
export function DriverBars({ drivers }: { drivers: Driver[] }) {
  const t = useT();

  const directionLabel = (direction: string) => {
    if (direction === "increases_risk") return t("direction.increases_risk");
    if (direction === "reduces_risk" || direction === "decreases_risk") {
      return t("direction.reduces_risk");
    }
    return direction.replace(/_/g, " ");
  };

  if (drivers.length === 0) {
    return <p className="px-4 py-6 text-sm text-[var(--color-graphite)]">{t("drivers.none")}</p>;
  }

  const widest = Math.max(...drivers.map((driver) => Math.abs(driver.shap)));

  return (
    <ol className="m-0 list-none p-0">
      {drivers.map((driver) => {
        const increasing = isRiskIncreasing(driver.direction);
        const share = widest === 0 ? 0 : (Math.abs(driver.shap) / widest) * 100;
        const hue = increasing ? "var(--color-decline)" : "var(--color-approve)";
        const ink = increasing ? "var(--color-decline-ink)" : "var(--color-approve-ink)";

        return (
          <li
            key={driver.feature}
            className="border-b border-[var(--color-rule)] px-4 py-3 last:border-b-0"
          >
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-[13px]">{driver.label}</span>
              <span className="num text-[13px]" style={{ color: ink }}>
                {formatSigned(driver.shap)}
              </span>
            </div>
            <div className="mt-1.5 flex items-center gap-3">
              <span
                className="h-2 flex-1 bg-[var(--color-sunk)]"
                role="img"
                aria-label={`${driver.label}: ${formatSigned(driver.shap)}, ${directionLabel(driver.direction)}`}
              >
                <span className="block h-full" style={{ width: `${share}%`, background: hue }} />
              </span>
              <span className="label shrink-0" style={{ color: ink }}>
                {directionLabel(driver.direction)}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
