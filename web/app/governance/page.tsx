"use client";

import { CalibrationPlot } from "@/components/calibration-plot";
import { FairnessPanel } from "@/components/fairness-panel";
import { ModelCardView } from "@/components/model-card";
import { ViewState } from "@/components/states";
import { useApi } from "@/lib/config";
import { formatMetric } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { Governance, ModelCard } from "@/lib/types";
import { useResource } from "@/lib/use-resource";

/** Named in full: an acronym a reviewer has to decode is a reviewer you lost. */
const METRICS = [
  { key: "auc_roc" as const, name: "governance.metric.auc.name", gloss: "governance.metric.auc.gloss" },
  { key: "ks" as const, name: "governance.metric.ks.name", gloss: "governance.metric.ks.gloss" },
  { key: "brier" as const, name: "governance.metric.brier.name", gloss: "governance.metric.brier.gloss" },
];

export default function GovernancePage() {
  const { api } = useApi();
  const t = useT();
  const governance = useResource<Governance>(() => api.governance(), [api]);
  const card = useResource<ModelCard>(() => api.modelCard(), [api]);

  return (
    <div className="max-w-5xl">
      <header className="mb-4">
        <h1 className="text-[19px] font-semibold tracking-tight">{t("governance.title")}</h1>
        <p className="mt-1 max-w-prose text-[13px] text-[var(--color-graphite)]">
          {t("governance.intro")}
        </p>
      </header>

      {(governance.loading || governance.failure) && (
        <div className="sheet">
          <ViewState
            loading={governance.loading}
            failure={governance.failure}
            label={t("governance.label.record")}
            onRetry={governance.reload}
          />
        </div>
      )}

      {governance.data && (
        <div className="space-y-4">
          <section className="sheet">
            <div className="sheet-head">
              <span className="label label-ink">{t("governance.serving")}</span>
              <span className="num text-[11px] text-[var(--color-muted)]">
                {t("governance.servingMeta", {
                  model: governance.data.model_version,
                  pipeline: governance.data.feature_pipeline_version,
                })}
              </span>
            </div>
            <dl className="grid gap-x-6 gap-y-4 px-4 py-4 sm:grid-cols-3">
              {METRICS.map((metric) => (
                <div key={metric.key}>
                  <dt className="label label-ink">{t(metric.name)}</dt>
                  <dd className="num mt-0.5 text-[26px] leading-none">
                    {formatMetric(governance.data!.metrics[metric.key])}
                  </dd>
                  <p className="mt-1.5 text-[11px] text-[var(--color-muted)]">{t(metric.gloss)}</p>
                </div>
              ))}
            </dl>
          </section>

          <div className="grid gap-4 lg:grid-cols-2">
            <section className="sheet">
              <div className="sheet-head">
                <span className="label label-ink">{t("governance.calibration")}</span>
                <span className="label">
                  {t("governance.bins", { n: governance.data.metrics.calibration.bins.length })}
                </span>
              </div>
              <CalibrationPlot
                bins={governance.data.metrics.calibration.bins}
                expectedCalibrationError={
                  governance.data.metrics.calibration.expected_calibration_error
                }
              />
            </section>

            <section className="sheet">
              <div className="sheet-head">
                <span className="label label-ink">{t("governance.fairness")}</span>
                <span className="label">{t("governance.approvalParity")}</span>
              </div>
              <FairnessPanel fairness={governance.data.fairness} />
            </section>
          </div>
        </div>
      )}

      <section className="sheet mt-4">
        <div className="sheet-head">
          <span className="label label-ink">{t("governance.modelCard")}</span>
          {card.data && (
            <span className="num text-[11px] text-[var(--color-muted)]">
              {t("governance.version", { v: card.data.model_version })}
            </span>
          )}
        </div>
        <ViewState
          loading={card.loading}
          failure={card.failure}
          label={t("governance.label.modelCard")}
          onRetry={card.reload}
        />
        {card.data && <ModelCardView content={card.data.content} />}
      </section>
    </div>
  );
}
