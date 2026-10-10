# Tasks: Real-Time Scoring API

**Feature**: `002-scoring-api` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Tests REQUIRED (Constitution I). Paths repo-relative. Depends on feature 001 (registry + trained model).

## Phase 1: Setup

- [x] T001 Add API deps (fastapi, uvicorn, pydantic v2) in `pyproject.toml`

## Phase 2: Foundational (blocking prerequisites)

- [x] T002 [P] Decision policy `decide()` (pure core) in `src/creditsentinel/decision.py`
- [x] T003 [P] Request/response schemas (`ScoreRequest`, `ScoreResponse`, `Driver`, `ReasonCode`) in `src/creditsentinel/api/schemas.py`
- [x] T004 [P] `RedactorPort` + `HashRedactor` in `src/creditsentinel/api/redact.py`
- [x] T005 [P] `AuditSinkPort` + `JsonlAuditSink` in `src/creditsentinel/api/audit.py`
- [x] T006 [P] `PolicyRetrieverPort` + `NullPolicyRetriever` placeholder in `src/creditsentinel/rag/retriever.py`

## Phase 3: User Story 1 — Real-time decision with explanation (P1, MVP)

**Goal**: One-request PD → decision → drivers → grounded reason → audit.
**Independent test**: high-risk applicant → decline with grounded reason + audit id.

- [x] T007 [P] [US1] SHAP driver extraction (`ShapDriverExtractor`, `Driver`, `risk_increasing`) in `src/creditsentinel/explain/drivers.py`
- [x] T008 [US1] `ReasonCodePort` + template adapter + `assert_grounded` in `src/creditsentinel/explain/reason.py`
- [x] T009 [US1] `ScoringService` composition root (validate→features→PD→decision→drivers→reason→audit) in `src/creditsentinel/api/service.py`
- [x] T010 [US1] FastAPI app `/score` + service wiring in `src/creditsentinel/api/app.py`
- [x] T011 [US1] Tests: reason grounding in `tests/test_reason.py`; end-to-end score + driver-reference in `tests/test_api.py`

## Phase 4: User Story 2 — Reject bad input safely (P2)

**Goal**: Validation errors (422) for malformed/out-of-range input.
**Independent test**: invalid category / missing field → 422.

- [x] T012 [US2] Field constraints + fixed categorical vocabularies in `src/creditsentinel/api/schemas.py`
- [x] T013 [US2] Tests: `test_invalid_payload_returns_422`, `test_missing_field_returns_422` in `tests/test_api.py`

## Phase 5: User Story 3 — PII-safe audit trail (P3)

**Goal**: One PII-safe audit entry per decision.
**Independent test**: audit entry has pseudonymized id; raw id absent.

- [x] T014 [US3] Wire redactor + audit into `ScoringService.score` in `src/creditsentinel/api/service.py`
- [x] T015 [US3] Test: `test_audit_log_is_pii_safe` in `tests/test_api.py`

## Phase 6: Polish & Cross-Cutting

- [x] T016 [P] `GET /health` (liveness + model_loaded) in `src/creditsentinel/api/app.py`
- [x] T017 [US1] Test: `test_determinism` (identical input → identical pd/decision/drivers) in `tests/test_api.py`
- [x] T018 [P] Shared trained-model + service fixtures in `tests/conftest.py`

## Dependencies

- Setup (T001) → Foundational (T002–T006) → US1 (T007–T011) → US2 (T012–T013) → US3 (T014–T015) → Polish (T016–T018).
- US1 depends on feature 001 (registry/model) and Foundational ports.

## Parallel opportunities

- T002 ∥ T003 ∥ T004 ∥ T005 ∥ T006 (independent modules); T007 ∥ T008 within US1; T016 ∥ T018.

## Implementation strategy

MVP = US1 (grounded real-time decision). US2 (validation) and US3 (audit) harden it. Health + determinism test in polish.
