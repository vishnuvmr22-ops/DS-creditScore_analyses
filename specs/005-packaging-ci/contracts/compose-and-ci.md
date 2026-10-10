# Contract — Compose & CI

## docker compose up --build
- Brings up `mlflow`, `chroma`, `api`. `api` waits for healthy deps, trains+registers a governed model if none exists, ingests the policy store, then serves.
- **Endpoints**: API http://localhost:8080 (`/health`, `/score`, `/docs`); MLflow UI http://localhost:5000.
- **No-manual-steps**: a fresh `up` yields a scorable service (FR-001/FR-002).
- **No-key**: without `ANTHROPIC_API_KEY`, `/score` still returns a grounded (template) reason (FR-005).

## GET /health (post-boot)
`{"status":"ok","model_loaded":true,"model_version":"1","feature_pipeline_version":"1.0.0"}`

## CI (.github/workflows/ci.yml) on push/PR
- `ruff check src tests` MUST pass.
- `pytest --cov=creditsentinel --cov-fail-under=80` MUST pass (fails below floor).
