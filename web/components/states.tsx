"use client";

import type { Failure } from "@/lib/api";
import { useT } from "@/lib/i18n";

/**
 * The three states every view must be able to render, plus the empty one.
 *
 * Failures name what did not happen and what would fix it. They don't apologize
 * and they're never vague — an operator seeing one should know their next move.
 */

export function LoadingState({ label }: { label: string }) {
  const t = useT();
  return (
    <div className="flex items-center gap-3 px-4 py-10" role="status" aria-live="polite">
      <span className="block h-2 w-2 animate-pulse bg-[var(--color-rule-strong)]" aria-hidden />
      <span className="label">{t("states.loading", { label })}</span>
    </div>
  );
}

export function NotProducedState({
  artifact,
  remedy,
}: {
  artifact: string;
  remedy: string;
}) {
  const t = useT();
  return (
    <div className="px-4 py-10">
      <p className="label label-ink">{t("states.notProduced.title")}</p>
      <p className="mt-2 max-w-prose text-sm text-[var(--color-graphite)]">
        {t("states.notProduced.body", { artifact: artifact.replace(/_/g, " ") })}
      </p>
      <p className="mt-4 label">{t("states.notProduced.toProduce")}</p>
      <p className="num mt-1 inline-block bg-[var(--color-sunk)] px-2 py-1 text-[13px]">{remedy}</p>
    </div>
  );
}

export function FailedState({ failure, onRetry }: { failure: Failure; onRetry?: () => void }) {
  const t = useT();
  return (
    <div className="px-4 py-10" role="alert">
      <p className="label" style={{ color: "var(--color-decline-ink)" }}>
        {failure.kind === "unreachable"
          ? t("states.failed.unreachable")
          : t("states.failed.requestFailed")}
      </p>
      <p className="mt-2 max-w-prose text-sm text-[var(--color-graphite)]">{failure.message}</p>
      {onRetry && (
        <button type="button" className="btn btn-quiet mt-4" onClick={onRetry}>
          {t("states.tryAgain")}
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="px-4 py-10">
      <p className="label label-ink">{title}</p>
      <p className="mt-2 max-w-prose text-sm text-[var(--color-graphite)]">{body}</p>
    </div>
  );
}

/** Renders whichever state applies, or nothing once data has arrived. */
export function ViewState({
  loading,
  failure,
  label,
  onRetry,
}: {
  loading: boolean;
  failure: Failure | null;
  label: string;
  onRetry?: () => void;
}) {
  if (loading) return <LoadingState label={label} />;
  if (failure?.kind === "not_produced") {
    return <NotProducedState artifact={failure.artifact} remedy={failure.remedy} />;
  }
  if (failure) return <FailedState failure={failure} onRetry={onRetry} />;
  return null;
}
