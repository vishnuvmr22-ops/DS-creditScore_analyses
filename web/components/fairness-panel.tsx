"use client";

import { formatMetric, formatPercent } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { Governance } from "@/lib/types";

/**
 * Approval-rate parity across the protected attribute.
 *
 * The disparity here was put into the synthetic data on purpose, so the check
 * has something to find. Saying so beside the number is the point — a fairness
 * panel that lets a reader mistake a fixture for a finding is worse than none.
 */
export function FairnessPanel({ fairness }: { fairness: Governance["fairness"] }) {
  const t = useT();
  const groups = Object.entries(fairness.approval_rate_by_group);
  const highest = Math.max(...groups.map(([, rate]) => rate), 0.0001);

  return (
    <div className="px-4 py-4">
      <ul className="m-0 list-none space-y-3 p-0">
        {groups.map(([group, rate]) => (
          <li key={group}>
            <div className="flex items-baseline justify-between gap-4">
              <span className="label label-ink">{t("fairness.group", { group })}</span>
              <span className="num text-[13px]">{formatPercent(rate, 2)}</span>
            </div>
            <span className="mt-1 block h-2.5 bg-[var(--color-sunk)]">
              <span
                className="block h-full"
                style={{ width: `${(rate / highest) * 100}%`, background: "var(--color-form)" }}
              />
            </span>
          </li>
        ))}
      </ul>

      <dl className="mt-5 grid grid-cols-2 gap-4 border-t border-[var(--color-rule)] pt-4">
        <div>
          <dt className="label">{t("fairness.parityGap")}</dt>
          <dd className="num mt-0.5 text-[18px]">{formatMetric(fairness.parity_gap)}</dd>
        </div>
        <div>
          <dt className="label">{t("fairness.disparateImpact")}</dt>
          <dd className="num mt-0.5 text-[18px]">
            {formatMetric(fairness.disparate_impact_ratio)}
          </dd>
        </div>
      </dl>

      <p className="mt-4 border-l-2 border-[var(--color-review)] pl-3 text-[12px] text-[var(--color-graphite)]">
        {t("fairness.note")}
      </p>
    </div>
  );
}
