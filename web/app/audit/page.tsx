"use client";

import { useState } from "react";
import { AuditTable } from "@/components/audit-table";
import { EmptyState, ViewState } from "@/components/states";
import { useApi } from "@/lib/config";
import { useT } from "@/lib/i18n";
import type { AuditPage, Decision, DecisionPolicy } from "@/lib/types";
import { useResource } from "@/lib/use-resource";

const FILTERS: { value: Decision | null; key: string }[] = [
  { value: null, key: "audit.filter.all" },
  { value: "approve", key: "audit.filter.approve" },
  { value: "review", key: "audit.filter.review" },
  { value: "decline", key: "audit.filter.decline" },
];

const LIMIT = 50;

export default function AuditPageView() {
  const { api } = useApi();
  const t = useT();
  const [filter, setFilter] = useState<Decision | null>(null);

  const page = useResource<AuditPage>(
    () => api.audit({ limit: LIMIT, decision: filter }),
    [api, filter],
  );
  const policy = useResource<DecisionPolicy>(() => api.decisionPolicy(), [api]);

  return (
    <div>
      <header className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[19px] font-semibold tracking-tight">{t("audit.title")}</h1>
          <p className="mt-1 max-w-prose text-[13px] text-[var(--color-graphite)]">
            {t("audit.intro", { n: LIMIT })}
          </p>
        </div>
        <button type="button" className="btn btn-quiet" onClick={page.reload}>
          {t("audit.refresh")}
        </button>
      </header>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="label">{t("audit.outcome")}</span>
        {FILTERS.map((option) => (
          <button
            key={option.key}
            type="button"
            className="btn btn-quiet"
            aria-pressed={filter === option.value}
            onClick={() => setFilter(option.value)}
          >
            {t(option.key)}
          </button>
        ))}
      </div>

      <div className="sheet">
        <div className="sheet-head">
          <span className="label label-ink">{t("audit.recorded")}</span>
          {page.data && (
            <span className="num text-[11px]">{t("audit.shown", { count: page.data.count })}</span>
          )}
        </div>

        <ViewState
          loading={page.loading}
          failure={page.failure}
          label={t("audit.label.trail")}
          onRetry={page.reload}
        />

        {page.data &&
          (page.data.count === 0 ? (
            <EmptyState
              title={t("audit.empty.title")}
              body={filter ? t("audit.empty.filtered") : t("audit.empty.none")}
            />
          ) : (
            <AuditTable entries={page.data.entries} policy={policy.data} />
          ))}
      </div>
    </div>
  );
}
