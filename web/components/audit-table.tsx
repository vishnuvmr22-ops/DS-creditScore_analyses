"use client";

import { DeterminationTick } from "./determination-scale";
import { decisionClass, formatPd, formatTimestamp } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { AuditEntry, DecisionPolicy } from "@/lib/types";

const COLUMN_KEYS = [
  "auditTable.recorded",
  "auditTable.reference",
  "auditTable.pd",
  "auditTable.position",
  "auditTable.outcome",
  "auditTable.drivers",
  "auditTable.versions",
  "auditTable.reasonBy",
];

/**
 * The decision trail, as a ledger.
 *
 * Every row carries the same determination scale that headlines a fresh
 * decision, shrunk to a tick — so a reviewer scanning history reads position
 * against the cutoff, not just a number. References are pseudonymized at write
 * time; no applicant attribute value was ever recorded (FR-019).
 */
export function AuditTable({
  entries,
  policy,
}: {
  entries: AuditEntry[];
  policy: DecisionPolicy | null;
}) {
  const t = useT();
  return (
    <div className="scroll-x">
      <table className="ledger">
        <thead>
          <tr>
            {COLUMN_KEYS.map((key) => (
              <th key={key} className="label label-ink">
                {t(key)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.audit_id}>
              <td className="num whitespace-nowrap text-[12px]">{formatTimestamp(entry.ts)}</td>
              <td className="num text-[12px]">{entry.applicant_id}</td>
              <td className="num text-[12px]">{formatPd(entry.pd)}</td>
              <td>
                {policy ? (
                  <DeterminationTick
                    pd={entry.pd}
                    approveBelow={policy.approve_below}
                    declineAtOrAbove={policy.decline_at_or_above}
                  />
                ) : (
                  <span className="label">—</span>
                )}
              </td>
              <td>
                <span className={`${decisionClass(entry.decision)} text-[11px]`}>
                  {t(`decision.${entry.decision}`)}
                </span>
              </td>
              <td className="text-[12px]">
                <ul className="m-0 list-none space-y-0.5 p-0">
                  {entry.drivers.map((driver) => (
                    <li key={driver.feature} className="whitespace-nowrap">
                      {driver.label}
                    </li>
                  ))}
                </ul>
              </td>
              <td className="num whitespace-nowrap text-[12px] text-[var(--color-graphite)]">
                {entry.model_version} · {entry.feature_pipeline_version}
              </td>
              <td className="label">{entry.reason_generator}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
