"use client";

import { useState } from "react";
import { useLocale, useT } from "@/lib/i18n";
import {
  SECTIONS,
  validateDraft,
  type Draft,
  type Field,
  type FieldName,
} from "@/lib/field-spec";
import { PRESETS } from "@/lib/presets";

/**
 * The application, as a worksheet.
 *
 * Fields are underlined rather than boxed, grouped the way an underwriting file
 * is grouped, and every constraint shown comes from the same table the validator
 * reads. Client-side checks are an affordance; the service is the authority, and
 * anything it rejects lands back on the field that caused it (FR-001).
 */

export interface ApplicantFormProps {
  draft: Draft;
  onChange: (draft: Draft) => void;
  onSubmit: (draft: Draft) => void;
  serverErrors: Partial<Record<FieldName, string>>;
  submitting: boolean;
  disabled?: boolean;
  disabledReason?: string;
}

function FieldControl({
  field,
  value,
  error,
  onChange,
}: {
  field: Field;
  value: string;
  error?: string;
  onChange: (value: string) => void;
}) {
  const t = useT();
  const id = `field-${field.name}`;
  const describedBy = error ? `${id}-error` : `${id}-help`;

  return (
    <div>
      <label htmlFor={id} className="label label-ink block">
        {t(field.label)}
        {field.kind === "number" && field.unit ? (
          <span className="ml-1 text-[var(--color-muted)]">({t(field.unit)})</span>
        ) : null}
      </label>

      {field.kind === "enum" ? (
        <select
          id={id}
          className="field-input mt-1"
          value={value}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
        >
          {field.options.map((option) => (
            <option key={option.value} value={option.value}>
              {t(option.label)}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={id}
          className="field-input mt-1"
          type={field.kind === "number" ? "number" : "text"}
          inputMode={field.kind === "number" ? "decimal" : undefined}
          step={field.kind === "number" ? field.step : undefined}
          min={field.kind === "number" ? (field.min ?? field.exclusiveMin) : undefined}
          max={field.kind === "number" ? field.max : undefined}
          value={value}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          onChange={(event) => onChange(event.target.value)}
        />
      )}

      {error ? (
        <p id={`${id}-error`} className="mt-1 text-[11px]" style={{ color: "var(--color-decline-ink)" }}>
          {error}
        </p>
      ) : (
        <p id={`${id}-help`} className="mt-1 text-[11px] text-[var(--color-muted)]">
          {t(field.help)}
        </p>
      )}
    </div>
  );
}

export function ApplicantForm({
  draft,
  onChange,
  onSubmit,
  serverErrors,
  submitting,
  disabled = false,
  disabledReason,
}: ApplicantFormProps) {
  const t = useT();
  const { locale } = useLocale();
  const [clientErrors, setClientErrors] = useState<Partial<Record<FieldName, string>>>({});
  const errors = { ...clientErrors, ...serverErrors };

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const found = validateDraft(draft, locale);
    setClientErrors(found);
    if (Object.keys(found).length === 0) onSubmit(draft);
  }

  function applyPreset(id: string) {
    const preset = PRESETS.find((candidate) => candidate.id === id);
    if (!preset) return;
    setClientErrors({});
    onChange({ ...preset.draft });
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="sheet">
      <div className="sheet-head">
        <span className="label label-ink">{t("form.application")}</span>
        <span className="label">{t("form.heldHere")}</span>
      </div>

      <div className="border-b border-[var(--color-rule)] px-4 py-3">
        <p className="label">{t("form.loadProfile")}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              className="btn btn-quiet"
              onClick={() => applyPreset(preset.id)}
              title={t(preset.expectation)}
            >
              {t(preset.label)}
            </button>
          ))}
        </div>
      </div>

      {SECTIONS.map((section) => (
        <fieldset key={section.title} className="border-b border-[var(--color-rule)] px-4 py-4">
          <legend className="label label-ink mb-3">{t(section.title)}</legend>
          <div className="grid gap-x-6 gap-y-4 sm:grid-cols-2">
            {section.fields.map((field) => (
              <FieldControl
                key={field.name}
                field={field}
                value={draft[field.name] ?? ""}
                error={errors[field.name]}
                onChange={(value) => {
                  setClientErrors((previous) => {
                    const next = { ...previous };
                    delete next[field.name];
                    return next;
                  });
                  onChange({ ...draft, [field.name]: value });
                }}
              />
            ))}
          </div>
        </fieldset>
      ))}

      <div className="flex flex-wrap items-center gap-3 px-4 py-4">
        <button type="submit" className="btn" disabled={submitting || disabled}>
          {submitting ? t("form.submitting") : t("form.submit")}
        </button>
        {disabled && disabledReason ? (
          <span className="text-[12px] text-[var(--color-graphite)]">{disabledReason}</span>
        ) : null}
      </div>
    </form>
  );
}
