# Quickstart — Packaging, CI & Documentation

## One-command bring-up
```bash
docker compose up --build
# wait for "Uvicorn running", then:
curl http://localhost:8080/health
curl -X POST http://localhost:8080/score -H "Content-Type: application/json" -d '{"applicant_id":"APP-1","age":24,"annual_income":21000,"employment_length":0.5,"debt_to_income":0.95,"credit_utilization":1.4,"num_delinquencies":6,"num_open_accounts":14,"loan_amount":42000,"interest_rate":28.0,"home_ownership":"RENT","purpose":"debt_consolidation"}'
```
Expected: health shows a loaded model; score returns a complete decision with a grounded reason (SC-001/SC-002).

## CI locally (mirror the gate)
```bash
uv run ruff check src tests
uv run pytest --cov=creditsentinel --cov-fail-under=80
```
Expected: lint clean; tests pass at ≥80% coverage (SC-003).

## Docs
- Open `README.md`: architecture, <10-min run, ≥5 talking points, synthetic-data label (SC-004/SC-005).
