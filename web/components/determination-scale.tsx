"use client";

import { formatPd } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { Decision } from "@/lib/types";

/**
 * The determination scale — the console's signature instrument.
 *
 * The entire probability range, with the policy's bands drawn as territory and
 * the applicant's PD landing on it as a hard rule. A caliper, not a progress
 * bar: in credit the cutoff *is* the business, so the boundary is the subject
 * and the value is where it fell.
 *
 * The same instrument appears at two scales — full size on a determination, and
 * as a bare tick beside every row of the audit trail.
 */

export interface ScaleProps {
  pd: number;
  approveBelow: number;
  declineAtOrAbove: number;
  decision: Decision | string;
}

function clampToScale(value: number): number {
  return Math.min(100, Math.max(0, value * 100));
}

function bands(approveBelow: number, declineAtOrAbove: number) {
  return [
    { key: "approve", from: 0, to: approveBelow, fill: "var(--color-approve-band)" },
    {
      key: "review",
      from: approveBelow,
      to: declineAtOrAbove,
      fill: "var(--color-review-band)",
    },
    { key: "decline", from: declineAtOrAbove, to: 1, fill: "var(--color-decline-band)" },
  ];
}

export function DeterminationScale({ pd, approveBelow, declineAtOrAbove, decision }: ScaleProps) {
  const t = useT();
  const position = clampToScale(pd);

  return (
    <figure
      className="m-0"
      role="img"
      aria-label={t("scale.aria", {
        pd: formatPd(pd),
        approve: approveBelow,
        decline: declineAtOrAbove,
        outcome: t(`decision.${decision}`),
      })}
    >
      <div className="relative h-11 w-full border border-[var(--color-rule-strong)]" aria-hidden>
        {bands(approveBelow, declineAtOrAbove).map((band) => (
          <div
            key={band.key}
            className="absolute inset-y-0"
            style={{
              left: `${clampToScale(band.from)}%`,
              width: `${clampToScale(band.to) - clampToScale(band.from)}%`,
              background: band.fill,
            }}
          />
        ))}

        {/* Cutoffs are the subject: draw them as rules, not as gradient stops. */}
        {[approveBelow, declineAtOrAbove].map((cutoff) => (
          <div
            key={cutoff}
            className="absolute inset-y-0 w-px bg-[var(--color-rule-strong)]"
            style={{ left: `${clampToScale(cutoff)}%` }}
          />
        ))}

        <div
          className="determination-marker absolute -top-1.5 -bottom-1.5 w-0.5 bg-[var(--color-ink)]"
          style={{ left: `calc(${position}% - 1px)` }}
        />
      </div>

      <div className="relative mt-1 h-8" aria-hidden>
        <span className="num absolute left-0 text-[11px] text-[var(--color-muted)]">0</span>
        <span className="num absolute right-0 text-[11px] text-[var(--color-muted)]">1</span>

        {[
          { value: approveBelow, caption: t("scale.approveBelow") },
          { value: declineAtOrAbove, caption: t("scale.declineAt") },
        ].map((cutoff) => (
          <span
            key={cutoff.caption}
            className="absolute top-0 -translate-x-1/2 text-center"
            style={{ left: `${clampToScale(cutoff.value)}%` }}
          >
            <span className="num block text-[11px] text-[var(--color-graphite)]">
              {cutoff.value}
            </span>
            <span className="label block text-[9px]">{cutoff.caption}</span>
          </span>
        ))}
      </div>
    </figure>
  );
}

/** The same instrument, reduced to a tick — one per audit row. */
export function DeterminationTick({ pd, approveBelow, declineAtOrAbove }: Omit<ScaleProps, "decision">) {
  const t = useT();
  return (
    <span
      className="relative inline-block h-3.5 w-16 border border-[var(--color-rule)] align-middle"
      role="img"
      aria-label={t("scale.tick.aria", { pd: formatPd(pd) })}
    >
      {bands(approveBelow, declineAtOrAbove).map((band) => (
        <span
          key={band.key}
          className="absolute inset-y-0"
          style={{
            left: `${clampToScale(band.from)}%`,
            width: `${clampToScale(band.to) - clampToScale(band.from)}%`,
            background: band.fill,
          }}
        />
      ))}
      <span
        className="absolute inset-y-0 w-px bg-[var(--color-ink)]"
        style={{ left: `calc(${clampToScale(pd)}% - 0.5px)` }}
      />
    </span>
  );
}
