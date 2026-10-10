"use client";

import { formatMetric } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { CalibrationBin } from "@/lib/types";

/**
 * Predicted against observed default rate, per bin.
 *
 * The diagonal is the claim being tested — a perfectly calibrated model would
 * sit on it. Distance from that line, not position on it, is the finding. Bins
 * are sized by how many records they hold, because a bin of four says much less
 * than a bin of six hundred and the eye should know that before it judges.
 */

const W = 320;
const H = 264;
const PAD = { left: 40, right: 12, top: 12, bottom: 40 };
const TICKS = [0, 0.25, 0.5, 0.75, 1];

export function CalibrationPlot({
  bins,
  expectedCalibrationError,
}: {
  bins: CalibrationBin[];
  expectedCalibrationError: number;
}) {
  const t = useT();
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const x = (value: number) => PAD.left + value * plotW;
  const y = (value: number) => PAD.top + (1 - value) * plotH;

  const largest = Math.max(1, ...bins.map((bin) => bin.n));
  const radius = (n: number) => 2.5 + Math.sqrt(n / largest) * 5;

  const path = bins.map((bin) => `${x(bin.mean_pred)},${y(bin.observed)}`).join(" ");

  return (
    <div className="px-4 py-4">
      <div className="scroll-x">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full min-w-[280px]"
          role="img"
          aria-label={t("calibration.aria", {
            n: bins.length,
            ece: formatMetric(expectedCalibrationError),
          })}
        >
          {TICKS.map((tick) => (
            <g key={tick}>
              <line
                x1={x(tick)}
                y1={PAD.top}
                x2={x(tick)}
                y2={PAD.top + plotH}
                stroke="var(--color-rule)"
                strokeWidth="1"
              />
              <line
                x1={PAD.left}
                y1={y(tick)}
                x2={PAD.left + plotW}
                y2={y(tick)}
                stroke="var(--color-rule)"
                strokeWidth="1"
              />
              <text
                x={x(tick)}
                y={PAD.top + plotH + 14}
                textAnchor="middle"
                fontSize="9"
                fill="var(--color-muted)"
                fontFamily="var(--font-mono)"
              >
                {tick}
              </text>
              <text
                x={PAD.left - 6}
                y={y(tick) + 3}
                textAnchor="end"
                fontSize="9"
                fill="var(--color-muted)"
                fontFamily="var(--font-mono)"
              >
                {tick}
              </text>
            </g>
          ))}

          {/* Perfect calibration. */}
          <line
            x1={x(0)}
            y1={y(0)}
            x2={x(1)}
            y2={y(1)}
            stroke="var(--color-rule-strong)"
            strokeWidth="1"
            strokeDasharray="3 3"
          />

          <polyline points={path} fill="none" stroke="var(--color-form)" strokeWidth="1.5" />

          {bins.map((bin) => (
            <circle
              key={bin.bin}
              cx={x(bin.mean_pred)}
              cy={y(bin.observed)}
              r={radius(bin.n)}
              fill="var(--color-form)"
              fillOpacity="0.85"
            />
          ))}

          <text
            x={PAD.left + plotW / 2}
            y={H - 6}
            textAnchor="middle"
            fontSize="9"
            fill="var(--color-muted)"
          >
            {t("calibration.xAxis")}
          </text>
          <text
            x={10}
            y={PAD.top + plotH / 2}
            textAnchor="middle"
            fontSize="9"
            fill="var(--color-muted)"
            transform={`rotate(-90 10 ${PAD.top + plotH / 2})`}
          >
            {t("calibration.yAxis")}
          </text>
        </svg>
      </div>

      <div className="mt-3 flex flex-wrap items-baseline gap-x-6 gap-y-1 border-t border-[var(--color-rule)] pt-3">
        <span className="label">{t("calibration.ece")}</span>
        <span className="num text-[15px]">{formatMetric(expectedCalibrationError)}</span>
        <span className="text-[12px] text-[var(--color-graphite)]">
          {t("calibration.eceNote", { n: bins.length })}
        </span>
      </div>
    </div>
  );
}
