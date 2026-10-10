# Phase 1 Data Model — Training & Governance Pipeline

## Applicant record (dataset row)
Numeric: `age`, `annual_income`, `employment_length`, `debt_to_income`, `credit_utilization`, `num_delinquencies`, `num_open_accounts`, `loan_amount`, `interest_rate`.
Categorical (fixed vocabularies): `home_ownership` ∈ {RENT, OWN, MORTGAGE}; `purpose` ∈ {debt_consolidation, credit_card, home_improvement, major_purchase, other}.
Label: `default` ∈ {0,1}. Governance-only: `group` ∈ {A,B} (**never a feature**).
- **Validation**: generated from a pinned seed; ranges are bounded by the generator; label drawn from a transparent latent risk function + noise.

## Feature matrix (transform output)
Ordered columns = numeric fields + engineered (`income_to_loan`, `delinquency_flag`) + one-hot expansions of the categoricals. Carries `FEATURE_PIPELINE_VERSION` (currently `1.0.0`).
- **Invariant (AD-2)**: same input + same version ⇒ identical matrix (byte-for-byte); protected attribute absent.

## Model version
A registered PD model with an integer/string version and a `feature_pipeline_version` tag.
- **Relationships**: one model version → one governance package; the latest version is the one served.

## Governance package (required for registration)
- **Metrics**: `auc_roc`, `ks`, `brier`, `calibration` (per-bin mean-pred vs observed + expected calibration error).
- **Fairness**: `approval_rate_by_group`, `parity_gap`, `disparate_impact_ratio` (measured at the decline threshold).
- **Model card**: intended use, provenance (labeled synthetic), metrics, fairness, limitations.
- **Rule (FR-006)**: `assert_governed` raises `GovernanceError` if any of metrics/calibration/fairness/model-card is missing → registration refused.

## Drift baseline
Per-feature reference `{edges, props}` (deciles) + a score reference distribution + `n_bins`. Persisted to `data/baseline_stats.json`.
- **Consumed by**: the drift-monitoring feature (separate slice).
