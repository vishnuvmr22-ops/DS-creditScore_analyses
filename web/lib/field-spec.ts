/**
 * One table, two jobs: it lays out the application form and it validates it.
 *
 * The constraints below mirror the service's contract exactly. Keeping them in a
 * single place is the point — a range that drifts from the service would show an
 * operator a green field the service then rejects. The client check is an
 * affordance; the service remains the authority (FR-001).
 */

import { DEFAULT_LOCALE, translate, type Locale } from "./dictionary";
import type { ScoreRequest } from "./types";

export type FieldName = keyof ScoreRequest;

/**
 * `label`, `help`, section `title` and option `label` hold i18n *keys*, not
 * display text — the form resolves them in the active locale. Keeping keys in
 * the spec means the one table still drives both layout and validation while
 * staying language-agnostic.
 */
interface BaseField {
  name: FieldName;
  label: string;
  help: string;
}

export interface NumberField extends BaseField {
  kind: "number";
  min?: number;
  max?: number;
  exclusiveMin?: number;
  step: number;
  unit?: string;
}

export interface EnumField extends BaseField {
  kind: "enum";
  options: { value: string; label: string }[];
}

export interface TextField extends BaseField {
  kind: "text";
}

export type Field = NumberField | EnumField | TextField;

export interface Section {
  title: string;
  fields: Field[];
}

export const SECTIONS: Section[] = [
  {
    title: "section.applicant",
    fields: [
      {
        name: "applicant_id",
        kind: "text",
        label: "field.applicant_id.label",
        help: "field.applicant_id.help",
      },
      {
        name: "age",
        kind: "number",
        label: "field.age.label",
        min: 18,
        max: 120,
        step: 1,
        help: "field.age.help",
      },
      {
        name: "annual_income",
        kind: "number",
        label: "field.annual_income.label",
        min: 0,
        step: 1000,
        unit: "$",
        help: "field.annual_income.help",
      },
      {
        name: "employment_length",
        kind: "number",
        label: "field.employment_length.label",
        min: 0,
        max: 60,
        step: 0.5,
        unit: "unit.yr",
        help: "field.employment_length.help",
      },
      {
        name: "home_ownership",
        kind: "enum",
        label: "field.home_ownership.label",
        help: "field.home_ownership.help",
        options: [
          { value: "RENT", label: "option.home_ownership.RENT" },
          { value: "OWN", label: "option.home_ownership.OWN" },
          { value: "MORTGAGE", label: "option.home_ownership.MORTGAGE" },
        ],
      },
    ],
  },
  {
    title: "section.credit",
    fields: [
      {
        name: "debt_to_income",
        kind: "number",
        label: "field.debt_to_income.label",
        min: 0,
        max: 2,
        step: 0.01,
        help: "field.debt_to_income.help",
      },
      {
        name: "credit_utilization",
        kind: "number",
        label: "field.credit_utilization.label",
        min: 0,
        max: 3,
        step: 0.01,
        help: "field.credit_utilization.help",
      },
      {
        name: "num_delinquencies",
        kind: "number",
        label: "field.num_delinquencies.label",
        min: 0,
        step: 1,
        help: "field.num_delinquencies.help",
      },
      {
        name: "num_open_accounts",
        kind: "number",
        label: "field.num_open_accounts.label",
        min: 0,
        step: 1,
        help: "field.num_open_accounts.help",
      },
    ],
  },
  {
    title: "section.loan",
    fields: [
      {
        name: "loan_amount",
        kind: "number",
        label: "field.loan_amount.label",
        exclusiveMin: 0,
        step: 500,
        unit: "$",
        help: "field.loan_amount.help",
      },
      {
        name: "interest_rate",
        kind: "number",
        label: "field.interest_rate.label",
        min: 0,
        max: 100,
        step: 0.1,
        unit: "%",
        help: "field.interest_rate.help",
      },
      {
        name: "purpose",
        kind: "enum",
        label: "field.purpose.label",
        help: "field.purpose.help",
        options: [
          { value: "debt_consolidation", label: "option.purpose.debt_consolidation" },
          { value: "credit_card", label: "option.purpose.credit_card" },
          { value: "home_improvement", label: "option.purpose.home_improvement" },
          { value: "major_purchase", label: "option.purpose.major_purchase" },
          { value: "other", label: "option.purpose.other" },
        ],
      },
    ],
  },
];

export const ALL_FIELDS: Field[] = SECTIONS.flatMap((section) => section.fields);

export type Draft = Record<FieldName, string>;

export function validateField(
  field: Field,
  raw: string,
  locale: Locale = DEFAULT_LOCALE,
): string | null {
  const value = raw.trim();

  if (field.kind === "text") {
    return value.length === 0 ? translate(locale, "validation.reference") : null;
  }

  if (field.kind === "enum") {
    return field.options.some((option) => option.value === value)
      ? null
      : translate(locale, "validation.chooseOption");
  }

  if (value.length === 0) return translate(locale, "validation.enterValue");
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return translate(locale, "validation.enterNumber");
  if (field.min !== undefined && parsed < field.min) {
    return translate(locale, "validation.min", { min: field.min });
  }
  if (field.max !== undefined && parsed > field.max) {
    return translate(locale, "validation.max", { max: field.max });
  }
  if (field.exclusiveMin !== undefined && parsed <= field.exclusiveMin) {
    return translate(locale, "validation.exclusiveMin", { min: field.exclusiveMin });
  }
  return null;
}

export function validateDraft(
  draft: Draft,
  locale: Locale = DEFAULT_LOCALE,
): Partial<Record<FieldName, string>> {
  const errors: Partial<Record<FieldName, string>> = {};
  for (const field of ALL_FIELDS) {
    const message = validateField(field, draft[field.name] ?? "", locale);
    if (message) errors[field.name] = message;
  }
  return errors;
}

export function draftToRequest(draft: Draft): ScoreRequest {
  const numeric = (name: FieldName) => Number(draft[name]);
  return {
    applicant_id: draft.applicant_id.trim(),
    age: numeric("age"),
    annual_income: numeric("annual_income"),
    employment_length: numeric("employment_length"),
    debt_to_income: numeric("debt_to_income"),
    credit_utilization: numeric("credit_utilization"),
    num_delinquencies: numeric("num_delinquencies"),
    num_open_accounts: numeric("num_open_accounts"),
    loan_amount: numeric("loan_amount"),
    interest_rate: numeric("interest_rate"),
    home_ownership: draft.home_ownership as ScoreRequest["home_ownership"],
    purpose: draft.purpose as ScoreRequest["purpose"],
  };
}
