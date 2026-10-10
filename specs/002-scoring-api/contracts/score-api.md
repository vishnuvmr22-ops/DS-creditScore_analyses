# Contract — Scoring API

## POST /score
**Request** (`ScoreRequest`): applicant_id + applicant fields. Invalid → **422** with field detail.

**Response 200** (`ScoreResponse`):
```json
{
  "applicant_id": "pseudo_...", "pd": 0.81, "decision": "decline",
  "thresholds": {"approve_below": 0.15, "decline_at_or_above": 0.45},
  "model_version": "1", "feature_pipeline_version": "1.0.0",
  "drivers": [{"feature": "debt_to_income", "label": "debt-to-income ratio", "shap": 1.03, "direction": "increases_risk"}],
  "reason_code": {"text": "...references drivers...", "grounded_in": ["debt_to_income"], "policy_refs": [], "generator": "template"},
  "audit_id": "uuid"
}
```
**Invariants**: decline ⇒ `drivers` non-empty AND reason references an actual driver; response echoes both versions; identical input ⇒ identical pd/decision/driver order.

## GET /health
```json
{"status": "ok", "model_loaded": true, "model_version": "1", "feature_pipeline_version": "1.0.0"}
```
Degraded (no governed model): `{"status": "degraded", "model_loaded": false}`.

## Side effect
One JSONL audit entry per `/score` call; applicant id pseudonymized; raw id never written.
