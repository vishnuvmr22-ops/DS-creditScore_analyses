# Quickstart — Real-Time Scoring API

## Prerequisites
- `uv sync --extra dev`; a governed model registered (`uv run creditsentinel-train`).

## Run
```bash
uv run uvicorn creditsentinel.api.app:app --reload   # :8000
curl http://localhost:8000/health
curl -X POST http://localhost:8000/score -H "Content-Type: application/json" -d '{"applicant_id":"APP-1","age":24,"annual_income":21000,"employment_length":0.5,"debt_to_income":0.95,"credit_utilization":1.4,"num_delinquencies":6,"num_open_accounts":14,"loan_amount":42000,"interest_rate":28.0,"home_ownership":"RENT","purpose":"debt_consolidation"}'
```
Expected: 200 with a decline, drivers, a grounded reason, pseudonymized id, audit id.

## Validate
```bash
uv run pytest tests/test_decision.py tests/test_reason.py tests/test_api.py -q
```
Expected: pass, including `test_high_risk_declines_with_grounded_reason`, `test_invalid_payload_returns_422`, `test_audit_log_is_pii_safe`, `test_determinism`.

## Success signals
- Complete response in one call (SC-001); decline is grounded (SC-002); invalid → 422 (SC-003); no raw id in audit (SC-004); determinism (SC-005).
