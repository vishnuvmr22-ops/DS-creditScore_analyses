"use client";

import { DeterminationScale } from "./determination-scale";
import { DriverBars } from "./driver-bars";
import { decisionClass, formatPd } from "@/lib/format";
import { useFeatureLabel, useT } from "@/lib/i18n";
import type { ScoreResponse } from "@/lib/types";

/**
 * The determination, in full.
 *
 * Every field the service returned appears here (SC-002). That is deliberate:
 * a decisioning console that quietly drops the version pins or the grounding is
 * exactly the console a model-risk reviewer cannot use.
 */

export function DecisionResult({ result }: { result: ScoreResponse }) {
  const t = useT();
  const featureLabel = useFeatureLabel();
  const { thresholds, reason_code: reason } = result;

  const generatorLabel =
    reason.generator === "template" || reason.generator === "anthropic"
      ? t(`result.generator.${reason.generator}`)
      : reason.generator;
  const generatorNote =
    reason.generator === "template"
      ? t("result.generatorNote.template")
      : t("result.generatorNote.anthropic");

  return (
    <div className="space-y-4">
      <section className="sheet">
        <div className="sheet-head">
          <span className="label label-ink">{t("result.determination")}</span>
          <span className="num text-[11px] text-[var(--color-muted)]">{result.applicant_id}</span>
        </div>

        <div className="px-4 py-4">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="label">{t("result.pd")}</p>
              <p className="num mt-0.5 text-[34px] leading-none">{formatPd(result.pd)}</p>
            </div>
            <p className={`${decisionClass(result.decision)} text-[17px]`}>
              {t(`decision.${result.decision}`)}
            </p>
          </div>

          <div className="mt-6">
            <DeterminationScale
              pd={result.pd}
              approveBelow={thresholds.approve_below}
              declineAtOrAbove={thresholds.decline_at_or_above}
              decision={result.decision}
            />
          </div>
        </div>
      </section>

      <section className="sheet">
        <div className="sheet-head">
          <span className="label label-ink">{t("result.topDrivers")}</span>
          <span className="label">{t("result.shapContribution")}</span>
        </div>
        <DriverBars drivers={result.drivers} />
      </section>

      <section className="sheet">
        <div className="sheet-head">
          <span className="label label-ink">{t("result.reason")}</span>
          <span className="label">{generatorLabel}</span>
        </div>

        <div className="px-4 py-4">
          <p className="max-w-prose border-l-2 border-[var(--color-ink)] pl-3 text-[15px] leading-relaxed">
            {reason.text}
          </p>

          <p className="mt-3 text-[12px] text-[var(--color-muted)]">{generatorNote}</p>

          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <div>
              <p className="label">{t("result.groundedIn")}</p>
              <ul className="mt-1.5 list-none space-y-1 p-0">
                {reason.grounded_in.map((feature) => (
                  <li key={feature} className="num text-[12px]">
                    {featureLabel(feature)}
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="label">{t("result.policyRefs")}</p>
              {reason.policy_refs.length === 0 ? (
                <p className="mt-1.5 text-[12px] text-[var(--color-graphite)]">
                  {t("result.policyRefs.none")}
                </p>
              ) : (
                <ul className="mt-1.5 list-none space-y-2 p-0">
                  {reason.policy_refs.map((passage) => (
                    <li
                      key={passage}
                      className="border-l border-[var(--color-rule-strong)] pl-2 text-[12px] text-[var(--color-graphite)]"
                    >
                      {passage}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="sheet">
        <div className="sheet-head">
          <span className="label label-ink">{t("result.provenance")}</span>
        </div>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 px-4 py-4 sm:grid-cols-4">
          {[
            { term: t("result.modelVersion"), value: result.model_version },
            { term: t("result.pipelineVersion"), value: result.feature_pipeline_version },
            { term: t("result.auditId"), value: result.audit_id },
            { term: t("result.applicantRef"), value: result.applicant_id },
          ].map((item) => (
            <div key={item.term}>
              <dt className="label">{item.term}</dt>
              <dd className="num mt-0.5 text-[12px] break-all">{item.value}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
