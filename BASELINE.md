# CreditSentinel Baseline Metrics (Step 0)

Date: 2026-10-09
Branch: `step0-baseline`

---

## 1. Test Suite Results

- **Command**: `uv run pytest`
- **Result**: `106 passed, 7 warnings in 27.13s`
- **Pass Rate**: 100% (106 / 106 tests passing)

---

## 2. Model Training & MLflow Governance Metrics

- **Command**: `uv run creditsentinel-train`
- **Model Type**: `XGBClassifier` (n_estimators=300, max_depth=4, lr=0.05)
- **Dataset**: Synthetic applicant dataset (`n=8000`, `seed=42`, `n_train=6000`, `n_test=2000`)
- **Pipeline Version**: `1.0.0`
- **Model Version**: `2` (registered to MLflow experiment `creditsentinel-pd`)

### Governance Metrics Output:
```json
{
  "model_version": "2",
  "feature_pipeline_version": "1.0.0",
  "metrics": {
    "auc_roc": 0.678565611998638,
    "ks": 0.2827898475134968,
    "brier": 0.17384673655033112
  },
  "calibration_ece": 0.14715224576900587,
  "fairness": {
    "approval_rate_by_group": {
      "A": 0.8667225481978206,
      "B": 0.8983890954151177
    },
    "parity_gap": 0.031666547217297114,
    "disparate_impact_ratio": 0.9647518570974362
  },
  "n_train": 6000,
  "n_test": 2000
}
```

---

## 3. Sample `POST /score` Request & Response

### Request Payload:
```json
{
  "applicant_id": "APP-1",
  "age": 24,
  "annual_income": 21000,
  "employment_length": 0.5,
  "debt_to_income": 0.95,
  "credit_utilization": 1.4,
  "num_delinquencies": 6,
  "num_open_accounts": 14,
  "loan_amount": 42000,
  "interest_rate": 28.0,
  "home_ownership": "RENT",
  "purpose": "debt_consolidation"
}
```

### Actual Response:
```json
{
  "applicant_id": "pseudo_dc1d2e5b65a1",
  "pd": 0.756551,
  "decision": "decline",
  "thresholds": {
    "approve_below": 0.15,
    "decline_at_or_above": 0.45
  },
  "model_version": "2",
  "feature_pipeline_version": "1.0.0",
  "drivers": [
    {
      "feature": "debt_to_income",
      "label": "debt-to-income ratio",
      "shap": 1.045329,
      "direction": "increases_risk"
    },
    {
      "feature": "credit_utilization",
      "label": "credit utilization",
      "shap": 0.78313,
      "direction": "increases_risk"
    },
    {
      "feature": "num_delinquencies",
      "label": "recent delinquencies",
      "shap": 0.547212,
      "direction": "increases_risk"
    }
  ],
  "reason_code": {
    "text": "Application declined. The primary factors increasing estimated default risk were: debt-to-income ratio, credit utilization, and recent delinquencies. (Consistent with policy: adverse-action#debt-to-income, model-card#drivers, risk-policy#affordability.)",
    "grounded_in": [
      "debt_to_income",
      "credit_utilization",
      "num_delinquencies"
    ],
    "policy_refs": [
      "adverse-action#debt-to-income",
      "model-card#drivers",
      "risk-policy#affordability"
    ],
    "generator": "template"
  },
  "audit_id": "605c28ef-ad37-4138-843a-5335f1a51281"
}
```
