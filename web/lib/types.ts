/**
 * The service contract, mirrored.
 *
 * These types are the console's half of `specs/006-web-console/contracts/`.
 * Nothing here is invented: every field is something the service returns.
 */

export type Decision = "approve" | "review" | "decline";

export type HomeOwnership = "RENT" | "OWN" | "MORTGAGE";

export type Purpose =
  | "debt_consolidation"
  | "credit_card"
  | "home_improvement"
  | "major_purchase"
  | "other";

export interface Health {
  status: string;
  model_loaded: boolean;
  model_version: string | null;
  feature_pipeline_version: string | null;
}

export interface DecisionPolicy {
  approve_below: number;
  decline_at_or_above: number;
  top_n_drivers: number;
  psi_cutoff: number;
}

export interface Driver {
  feature: string;
  label: string;
  shap: number;
  direction: string;
}

export interface ReasonCode {
  text: string;
  grounded_in: string[];
  policy_refs: string[];
  generator: string;
}

export interface ScoreRequest {
  applicant_id: string;
  age: number;
  annual_income: number;
  employment_length: number;
  debt_to_income: number;
  credit_utilization: number;
  num_delinquencies: number;
  num_open_accounts: number;
  loan_amount: number;
  interest_rate: number;
  home_ownership: HomeOwnership;
  purpose: Purpose;
}

export interface ScoreResponse {
  applicant_id: string;
  pd: number;
  decision: Decision;
  thresholds: { approve_below: number; decline_at_or_above: number };
  model_version: string;
  feature_pipeline_version: string;
  drivers: Driver[];
  reason_code: ReasonCode;
  audit_id: string;
}

export interface CalibrationBin {
  bin: number;
  n: number;
  mean_pred: number;
  observed: number;
}

export interface Governance {
  model_version: string;
  feature_pipeline_version: string;
  metrics: {
    auc_roc: number;
    ks: number;
    brier: number;
    calibration: {
      expected_calibration_error: number;
      bins: CalibrationBin[];
    };
  };
  fairness: {
    approval_rate_by_group: Record<string, number>;
    parity_gap: number;
    disparate_impact_ratio: number;
  };
}

export interface ModelCard {
  model_version: string;
  content: string;
}

export interface DriftFeature {
  psi: number;
  breach: boolean;
}

export interface DriftRun {
  run_id: string;
  ts: string;
  scenario: string;
  cutoff: number;
  features: Record<string, DriftFeature>;
  score: DriftFeature | null;
  breached_features: string[];
  any_breach: boolean;
}

export interface AuditEntry {
  audit_id: string;
  ts: string;
  applicant_id: string;
  pd: number;
  decision: Decision;
  model_version: string;
  feature_pipeline_version: string;
  drivers: Driver[];
  reason_generator: string;
}

export interface AuditPage {
  count: number;
  entries: AuditEntry[];
}
