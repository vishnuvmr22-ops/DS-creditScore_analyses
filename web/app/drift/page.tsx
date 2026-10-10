"use client";

import { PsiBars } from "@/components/psi-bars";
import { ViewState } from "@/components/states";
import { useApi } from "@/lib/config";
import { formatMetric, formatTimestamp } from "@/lib/format";
import { useFeatureLabel, useT } from "@/lib/i18n";
import type { DriftRun } from "@/lib/types";
import { useResource } from "@/lib/use-resource";

export default function DriftPage() {
  const { api } = useApi();
  const t = useT();
  const featureLabel = useFeatureLabel();
  const { data, failure, loading, reload } = useResource<DriftRun>(() => api.drift(), [api]);

  return (
    <div className="max-w-3xl">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-[19px] font-semibold tracking-tight">{t("drift.title")}</h1>
          <p className="mt-1 max-w-prose text-[13px] text-[var(--color-graphite)]">
            {t("drift.intro")}
          </p>
        </div>
        {data && (
          <button type="button" className="btn btn-quiet" onClick={reload}>
            {t("drift.refresh")}
          </button>
        )}
      </header>

      {(loading || failure) && (
        <div className="sheet">
          <ViewState
            loading={loading}
            failure={failure}
            label={t("drift.label.evaluation")}
            onRetry={reload}
          />
        </div>
      )}

      {data && (
        <div className="space-y-4">
          <section className="sheet">
            <div className="sheet-head">
              <span className="label label-ink">{t("drift.verdict")}</span>
              <span className="num text-[11px] text-[var(--color-muted)]">
                {t("drift.run", { id: data.run_id.slice(0, 8) })}
              </span>
            </div>

            <div className="px-4 py-4">
              <p
                className={`verdict text-[17px] ${data.any_breach ? "verdict-decline" : "verdict-approve"}`}
              >
                {data.any_breach ? t("drift.drifted") : t("drift.stable")}
              </p>
              <p className="mt-2 max-w-prose text-[13px] text-[var(--color-graphite)]">
                {data.any_breach
                  ? t(
                      data.breached_features.length === 1
                        ? "drift.breachedSummary.one"
                        : "drift.breachedSummary.other",
                      {
                        count: data.breached_features.length,
                        list: data.breached_features.map(featureLabel).join(", "),
                      },
                    )
                  : t("drift.withinThreshold")}
              </p>

              <dl className="mt-4 grid grid-cols-2 gap-4 border-t border-[var(--color-rule)] pt-4 sm:grid-cols-3">
                <div>
                  <dt className="label">{t("drift.evaluated")}</dt>
                  <dd className="num mt-0.5 text-[12px]">{formatTimestamp(data.ts)}</dd>
                </div>
                <div>
                  <dt className="label">{t("drift.scenario")}</dt>
                  <dd className="num mt-0.5 text-[12px]">{data.scenario}</dd>
                </div>
                <div>
                  <dt className="label">{t("drift.scoreDrift")}</dt>
                  <dd className="num mt-0.5 text-[12px]">
                    {data.score ? formatMetric(data.score.psi, 3) : t("drift.notComputed")}
                  </dd>
                </div>
              </dl>

              {data.scenario === "drift" && (
                <p className="mt-4 border-l-2 border-[var(--color-review)] pl-3 text-[12px] text-[var(--color-graphite)]">
                  {t("drift.injectedNote")}
                </p>
              )}
            </div>
          </section>

          <section className="sheet">
            <div className="sheet-head">
              <span className="label label-ink">{t("drift.perFeature")}</span>
              <span className="label">{t("drift.worstFirst")}</span>
            </div>
            <PsiBars features={data.features} cutoff={data.cutoff} />
          </section>
        </div>
      )}
    </div>
  );
}
