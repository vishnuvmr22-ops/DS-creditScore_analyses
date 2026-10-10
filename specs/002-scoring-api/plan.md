# Implementation Plan: Real-Time Scoring API

**Branch**: `002-scoring-api` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-scoring-api/spec.md`

## Summary

A FastAPI service exposing `POST /score` and `GET /health`. It validates the applicant (Pydantic v2), runs the versioned feature transform, infers PD from the pinned registered model, applies the decision policy, computes SHAP top drivers, produces a grounded reason code, and writes a PII-safe audit entry — in one request. Follows the hexagonal spine: pure core (decision, SHAP, grounding) with FastAPI/redactor/audit as adapters (AD-2 determinism, AD-3 grounded explanation, AD-4 redaction before egress).

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI + Uvicorn, Pydantic v2, SHAP, the registry adapter (MLflow) from feature 001, numpy/pandas
**Storage**: MLflow registry (read-only here); append-only JSONL audit log under `data/`
**Testing**: pytest with FastAPI TestClient; a real trained model fixture (no MLflow overhead)
**Target Platform**: Linux container / local dev
**Project Type**: Web service (single-project layout)
**Performance Goals**: Interactive latency; one model load at startup, SHAP explainer reused
**Constraints**: Deterministic (AD-2); no raw PII in logs (AD-4); no decline without grounded drivers+reason (AD-3)
**Scale/Scope**: One endpoint family; single-operator origination context

## Constitution Check

- **I. Test-first**: PASS — `tests/test_decision.py`, `tests/test_api.py`, plus the driver-reference and PII-safe-audit tests.
- **II. Determinism**: PASS — versions echoed; identical input → identical PD/decision/drivers (FR-008/SC-005).
- **III. Governance-first**: PASS — reads only a governed registered version; never trains (AD-1).
- **IV. Explainability**: PASS — every decision returns drivers; decline returns a grounded reason; `assert_grounded` enforces driver-reference (FR-004/FR-005).
- **V. PII discipline**: PASS — id pseudonymized before audit write; raw id never logged (FR-006/SC-004).

No violations → Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-scoring-api/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/score-api.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/creditsentinel/
├── decision.py               # decision policy (pure core)
├── explain/
│   ├── drivers.py            # SHAP driver extraction (pure core)
│   └── reason.py             # ReasonCodePort + template adapter + assert_grounded
├── rag/retriever.py          # PolicyRetrieverPort + NullPolicyRetriever (placeholder)
└── api/
    ├── schemas.py            # ScoreRequest / ScoreResponse (Pydantic v2)
    ├── redact.py             # RedactorPort + HashRedactor
    ├── audit.py              # AuditSinkPort + JsonlAuditSink
    ├── service.py            # ScoringService composition root
    └── app.py                # FastAPI app: /score, /health

tests/
├── conftest.py               # trained-model + service fixtures
├── test_decision.py · test_reason.py · test_api.py
```

**Structure Decision**: Driving adapter (`api/app.py`) translates HTTP to the pure core via `ScoringService`. Ports (`ReasonCodePort`, `PolicyRetrieverPort`, `RedactorPort`, `AuditSinkPort`) keep the core testable and let later features swap the reason/policy adapters.

## Complexity Tracking

No constitution violations — section intentionally empty.
