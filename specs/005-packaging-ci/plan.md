# Implementation Plan: Packaging, CI & Documentation

**Branch**: `005-packaging-ci` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-packaging-ci/spec.md`

## Summary

Packages the whole system for one-command bring-up and continuous verification. A single Docker image runs three compose services (API, Chroma, MLflow) with matching component versions; the API entrypoint auto-trains a governed model and builds the policy store on first boot, then serves. GitHub Actions runs ruff + pytest with a ≥80% coverage floor on every push. A flagship README carries architecture, <10-minute run steps, interview talking points, and honest synthetic-data provenance.

## Technical Context

**Language/Version**: Python 3.12 (image `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`)
**Primary Dependencies**: Docker + Docker Compose; the full app stack; GitHub Actions (setup-uv)
**Storage**: named volumes for the MLflow SQLite store/artifacts and the Chroma persistence
**Testing**: pytest + coverage gate in CI; end-to-end verified via a live `docker compose up`
**Target Platform**: Linux containers
**Project Type**: Deployment/packaging over the single-project app
**Performance Goals**: First boot completes training + ingest in ~30s before serving
**Constraints**: No manual steps (FR-001/FR-002); runs with no external key (FR-005)
**Scale/Scope**: 3 services, 1 image, 1 CI workflow, 1 README

## Constitution Check

- **I. Test-first**: PASS — CI runs the full suite with a coverage floor; end-to-end `/score` verified live.
- **II. Determinism**: PASS — one shared image pins matching mlflow/chromadb versions across services.
- **III. Governance-first**: PASS — first boot registers a governed model before serving (FR-002).
- **IV. Explainability**: PASS — end-to-end check returns a grounded reason.
- **V. PII discipline & honest provenance**: PASS — README labels data synthetic; no secrets required to run.

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-packaging-ci/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/compose-and-ci.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
Dockerfile
docker/entrypoint.sh          # train-if-needed + ingest + uvicorn
docker-compose.yml            # api + chroma + mlflow (one shared image)
.dockerignore
.github/workflows/ci.yml      # ruff + pytest --cov-fail-under=80
README.md                     # architecture, run steps, talking points, provenance
```

**Structure Decision**: One image is built and reused by all three compose services so mlflow/chromadb client and server versions match exactly. The entrypoint makes first boot self-sufficient (train + ingest) to satisfy "no manual steps". MLflow runs with `--allowed-hosts "*"` for the private compose network; the API host port avoids the common 8000 conflict.

## Complexity Tracking

No constitution violations — section intentionally empty.
