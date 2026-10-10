import type { Draft } from "./field-spec";

/**
 * Profiles that reach each outcome without manual data entry (FR-004).
 *
 * These are synthetic applicants, chosen from the same distribution the model
 * was trained on so each lands in its band reliably. They exist to make the
 * decision boundary demonstrable in one click, not to flatter the model.
 *
 * `label` and `expectation` hold i18n keys; the form resolves them in the
 * active locale.
 */
export interface Preset {
  id: string;
  label: string;
  expectation: string;
  draft: Draft;
}

export const PRESETS: Preset[] = [
  {
    id: "strong",
    label: "preset.strong.label",
    expectation: "preset.strong.expectation",
    draft: {
      applicant_id: "APP-STRONG-01",
      age: "48",
      annual_income: "140000",
      employment_length: "20",
      debt_to_income: "0.08",
      credit_utilization: "0.05",
      num_delinquencies: "0",
      num_open_accounts: "6",
      loan_amount: "8000",
      interest_rate: "6.0",
      home_ownership: "OWN",
      purpose: "home_improvement",
    },
  },
  {
    id: "borderline",
    label: "preset.borderline.label",
    expectation: "preset.borderline.expectation",
    draft: {
      applicant_id: "APP-BORDER-01",
      age: "34",
      annual_income: "58000",
      employment_length: "4",
      debt_to_income: "0.42",
      credit_utilization: "0.55",
      num_delinquencies: "1",
      num_open_accounts: "9",
      loan_amount: "18000",
      interest_rate: "15.5",
      home_ownership: "RENT",
      purpose: "credit_card",
    },
  },
  {
    id: "impaired",
    label: "preset.impaired.label",
    expectation: "preset.impaired.expectation",
    draft: {
      applicant_id: "APP-IMPAIR-01",
      age: "24",
      annual_income: "21000",
      employment_length: "0.5",
      debt_to_income: "0.95",
      credit_utilization: "1.4",
      num_delinquencies: "6",
      num_open_accounts: "14",
      loan_amount: "42000",
      interest_rate: "28.0",
      home_ownership: "RENT",
      purpose: "debt_consolidation",
    },
  },
];

export const EMPTY_DRAFT: Draft = {
  applicant_id: "",
  age: "",
  annual_income: "",
  employment_length: "",
  debt_to_income: "",
  credit_utilization: "",
  num_delinquencies: "",
  num_open_accounts: "",
  loan_amount: "",
  interest_rate: "",
  home_ownership: "RENT",
  purpose: "other",
};
