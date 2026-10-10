"use client";

import { useState } from "react";
import { ApplicantForm } from "@/components/applicant-form";
import { DecisionResult } from "@/components/decision-result";
import { EmptyState, FailedState, LoadingState } from "@/components/states";
import { useHealth } from "@/components/shell";
import { asFailure, type Failure } from "@/lib/api";
import { useApi } from "@/lib/config";
import { useT } from "@/lib/i18n";
import { draftToRequest, type Draft, type FieldName } from "@/lib/field-spec";
import { EMPTY_DRAFT, PRESETS } from "@/lib/presets";
import type { ScoreResponse } from "@/lib/types";

export default function DecisioningPage() {
  const { api } = useApi();
  const t = useT();
  const { health, reachable, loading: healthLoading } = useHealth();

  // The applicant lives here and nowhere else: never stored, never sent
  // anywhere but the scoring request itself (FR-012).
  const [draft, setDraft] = useState<Draft>({ ...PRESETS[2].draft });
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const degraded = reachable && !health?.model_loaded;
  const blocked = !healthLoading && (!reachable || degraded);
  const blockedReason = !reachable
    ? t("decisioning.blocked.unreachable")
    : t("decisioning.blocked.noModel");

  const serverErrors: Partial<Record<FieldName, string>> =
    failure?.kind === "invalid" ? (failure.fields as Partial<Record<FieldName, string>>) : {};

  async function score(current: Draft) {
    setSubmitting(true);
    setFailure(null);
    try {
      setResult(await api.score(draftToRequest(current)));
    } catch (error) {
      setResult(null);
      setFailure(asFailure(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
      <div>
        <header className="mb-4">
          <h1 className="text-[19px] font-semibold tracking-tight">{t("decisioning.title")}</h1>
          <p className="mt-1 max-w-prose text-[13px] text-[var(--color-graphite)]">
            {t("decisioning.intro")}
          </p>
        </header>

        <ApplicantForm
          draft={draft}
          onChange={(next) => {
            setDraft(next);
            if (failure?.kind === "invalid") setFailure(null);
          }}
          onSubmit={score}
          serverErrors={serverErrors}
          submitting={submitting}
          disabled={blocked}
          disabledReason={blocked ? blockedReason : undefined}
        />
      </div>

      <div>
        {submitting && <LoadingState label={t("decisioning.loadingLabel")} />}

        {!submitting && failure && failure.kind !== "invalid" && (
          <div className="sheet">
            <FailedState failure={failure} onRetry={() => score(draft)} />
          </div>
        )}

        {!submitting && failure?.kind === "invalid" && (
          <div className="sheet">
            <EmptyState
              title={t("decisioning.rejected.title")}
              body={t("decisioning.rejected.body")}
            />
          </div>
        )}

        {!submitting && !failure && result && <DecisionResult result={result} />}

        {!submitting && !failure && !result && (
          <div className="sheet">
            <EmptyState
              title={t("decisioning.empty.title")}
              body={t("decisioning.empty.body")}
            />
          </div>
        )}

        {result && (
          <p className="mt-4 flex flex-wrap items-center gap-2">
            <button type="button" className="btn btn-quiet" onClick={() => setResult(null)}>
              {t("decisioning.clearDetermination")}
            </button>
            <button
              type="button"
              className="btn btn-quiet"
              onClick={() => {
                setResult(null);
                setDraft({ ...EMPTY_DRAFT });
              }}
            >
              {t("decisioning.clearApplication")}
            </button>
          </p>
        )}
      </div>
    </div>
  );
}
