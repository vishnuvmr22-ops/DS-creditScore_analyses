import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import type { Api } from "@/lib/api";
import { ApiContext } from "@/lib/config";
import type {
  AuditPage,
  DecisionPolicy,
  DriftRun,
  Governance,
  Health,
  ModelCard,
  ScoreResponse,
} from "@/lib/types";

export const HEALTHY: Health = {
  status: "ok",
  model_loaded: true,
  model_version: "1",
  feature_pipeline_version: "1.0.0",
};

export const POLICY: DecisionPolicy = {
  approve_below: 0.15,
  decline_at_or_above: 0.45,
  top_n_drivers: 3,
  psi_cutoff: 0.2,
};

export const SCORE: ScoreResponse = {
  applicant_id: "pseudo_abc123",
  pd: 0.7622,
  decision: "decline",
  thresholds: { approve_below: 0.15, decline_at_or_above: 0.45 },
  model_version: "1",
  feature_pipeline_version: "1.0.0",
  drivers: [
    { feature: "debt_to_income", label: "debt-to-income ratio", shap: 1.19, direction: "increases_risk" },
    { feature: "num_delinquencies", label: "recent delinquencies", shap: 0.7, direction: "increases_risk" },
    { feature: "credit_utilization", label: "credit utilization", shap: 0.6, direction: "increases_risk" },
  ],
  reason_code: {
    text: "This application was declined. The debt-to-income ratio and recent delinquencies weighed heavily against approval.",
    grounded_in: ["debt_to_income", "num_delinquencies"],
    policy_refs: ["Applicants with debt-to-income above 0.5 are declined."],
    generator: "template",
  },
  audit_id: "audit-xyz",
};

export const GOVERNANCE: Governance = {
  model_version: "1",
  feature_pipeline_version: "1.0.0",
  metrics: {
    auc_roc: 0.683,
    ks: 0.284,
    brier: 0.173,
    calibration: {
      expected_calibration_error: 0.114,
      bins: [
        { bin: 0, n: 317, mean_pred: 0.07, observed: 0.088 },
        { bin: 1, n: 638, mean_pred: 0.148, observed: 0.166 },
      ],
    },
  },
  fairness: {
    approval_rate_by_group: { A: 0.879, B: 0.897 },
    parity_gap: 0.0179,
    disparate_impact_ratio: 0.98,
  },
};

export const MODEL_CARD: ModelCard = {
  model_version: "1",
  content: "# Model Card\n\n## Data provenance\nGenerated from a pinned seed with no real PII.\n\n| Metric | Value |\n| --- | --- |\n| AUC-ROC | 0.6832 |",
};

export const DRIFT_STABLE: DriftRun = {
  run_id: "run-stable-01",
  ts: "2026-07-21T10:12:03+00:00",
  scenario: "stable",
  cutoff: 0.2,
  features: {
    debt_to_income: { psi: 0.02, breach: false },
    age: { psi: 0.01, breach: false },
  },
  score: { psi: 0.03, breach: false },
  breached_features: [],
  any_breach: false,
};

export const DRIFT_BREACHING: DriftRun = {
  run_id: "run-drift-01",
  ts: "2026-07-21T12:00:00+00:00",
  scenario: "drift",
  cutoff: 0.2,
  features: {
    debt_to_income: { psi: 0.31, breach: true },
    age: { psi: 0.01, breach: false },
  },
  score: { psi: 0.25, breach: true },
  breached_features: ["debt_to_income"],
  any_breach: true,
};

export const AUDIT_PAGE: AuditPage = {
  count: 1,
  entries: [
    {
      audit_id: "audit-1",
      ts: "2026-07-21T09:00:00+00:00",
      applicant_id: "pseudo_e6cae956dbeb",
      pd: 0.762,
      decision: "decline",
      model_version: "1",
      feature_pipeline_version: "1.0.0",
      drivers: [
        { feature: "debt_to_income", label: "debt-to-income ratio", shap: 1.19, direction: "increases_risk" },
      ],
      reason_generator: "template",
    },
  ],
};

/** A stub Api whose every method rejects unless overridden. */
export function makeApi(overrides: Partial<Api> = {}): Api {
  const reject = () => Promise.reject(new Error("not stubbed"));
  return {
    health: () => Promise.resolve(HEALTHY),
    decisionPolicy: () => Promise.resolve(POLICY),
    governance: reject,
    modelCard: reject,
    drift: reject,
    audit: reject,
    score: reject,
    ...overrides,
  } as Api;
}

/** Render a view with the given stub client injected directly. */
export function renderWithApi(ui: ReactElement, api: Api) {
  return render(
    <ApiContext.Provider value={{ api, baseUrl: "http://svc:8080" }}>{ui}</ApiContext.Provider>,
  );
}
