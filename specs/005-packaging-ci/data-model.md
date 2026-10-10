# Phase 1 Data Model — Packaging, CI & Documentation

This feature is infrastructure; the "entities" are deployment artifacts rather than domain data.

## Container image
One image (uv + Python 3.12 + the app) reused by all services.

## Compose stack
- **mlflow**: `mlflow server` (SQLite backend + artifact store on a volume, `--allowed-hosts "*"`), port 5000.
- **chroma**: `chroma run` (persisted volume), internal port 8000.
- **api**: FastAPI via the entrypoint; host port 8080 → container 8000; depends_on mlflow+chroma healthy.
- **volumes**: `mlflow-data`, `chroma-data`.

## CI pipeline (GitHub Actions)
Steps: checkout → setup-uv (Python 3.12) → `uv sync` → `ruff check` → `pytest --cov-fail-under=80`.

## README
Sections: architecture, provenance banner, <10-min run (compose + local), response shape, ≥5 talking points, business framing, SDD workflow, layout.
