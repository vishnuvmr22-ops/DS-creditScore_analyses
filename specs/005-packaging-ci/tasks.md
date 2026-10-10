# Tasks: Packaging, CI & Documentation

**Feature**: `005-packaging-ci` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Depends on features 001–004. Paths repo-relative.

## Phase 1: Setup

- [x] T001 [P] `.dockerignore` (exclude venv, mlflow, chroma, data artifacts, _bmad-output) in `.dockerignore`
- [x] T002 [P] `.gitattributes` (LF normalization) in `.gitattributes`

## Phase 2: Foundational

- [x] T003 Single-image `Dockerfile` (uv, Python 3.12, install deps then project) in `Dockerfile`
- [x] T004 Self-sufficient API entrypoint (wait MLflow → train-if-needed → ingest → uvicorn) in `docker/entrypoint.sh`

## Phase 3: User Story 1 — One-command local bring-up (P1, MVP)

**Goal**: `docker compose up` starts API + Chroma + MLflow, scorable with no manual steps.
**Independent test**: fresh `up` → `/health` model_loaded true; `/score` returns a decision.

- [x] T005 [US1] `docker-compose.yml`: mlflow (SQLite + serve-artifacts + allowed-hosts), chroma (`chroma run`), api (entrypoint, port 8080, depends_on healthy) in `docker-compose.yml`
- [x] T006 [US1] Config: `chroma_host/port` + MLflow server URIs consumed via env in `src/creditsentinel/config.py`
- [x] T007 [US1] Verify end-to-end: `docker compose up` → `/score` HTTP 200 (live)

## Phase 4: User Story 2 — Automated quality gate (P2)

**Goal**: CI runs ruff + pytest with ≥80% coverage floor on push.
**Independent test**: pipeline runs lint + tests; fails below floor.

- [x] T008 [US2] GitHub Actions workflow (setup-uv, ruff, pytest --cov-fail-under=80) in `.github/workflows/ci.yml`

## Phase 5: User Story 3 — Credible, honest documentation (P3)

**Goal**: README lets a stranger run it <10 min; ≥5 talking points; honest provenance.
**Independent test**: follow README to run; count ≥5 talking points; find synthetic-data label.

- [x] T009 [US3] Flagship `README.md` (architecture, run steps, response shape, 7 talking points, provenance, SDD workflow) in `README.md`

## Phase 6: Polish & Cross-Cutting

- [x] T010 [P] Ensure runs with no `ANTHROPIC_API_KEY` (template fallback) — verified via health/score
- [x] T011 [P] Full suite green + ruff clean at repo scope (verify)

## Dependencies

- Setup (T001–T002) → Foundational (T003–T004) → US1 (T005–T007) → US2 (T008) → US3 (T009) → Polish (T010–T011).
- US1 requires features 001–004 present (train/ingest/serve/drift all packaged).

## Parallel opportunities

- T001 ∥ T002; T008 ∥ T009; T010 ∥ T011.

## Implementation strategy

MVP = US1 (one-command bring-up, verified live). US2 adds the CI gate; US3 the documentation. Polish verifies keyless operation and the full gate.
