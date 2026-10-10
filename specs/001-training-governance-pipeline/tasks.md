# Tasks: Training & Governance Pipeline

**Feature**: `001-training-governance-pipeline` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Tests are REQUIRED (Constitution I: test-first). Paths are repo-relative.

## Phase 1: Setup

- [x] T001 Add project dependencies (scikit-learn, xgboost, mlflow, pandas, numpy) and dev tools (pytest, pytest-cov, ruff) in `pyproject.toml`
- [x] T002 [P] Configure ruff + pytest (pythonpath=src, coverage) in `pyproject.toml`
- [x] T003 Add `creditsentinel-train` console entrypoint in `pyproject.toml`

## Phase 2: Foundational (blocking prerequisites)

- [x] T004 Central `Settings` (seed, decision thresholds, model name, MLflow URIs, data paths) in `src/creditsentinel/config.py`
- [x] T005 [P] Canonical applicant schema + `PROTECTED_ATTRIBUTE` (governance-only) in `src/creditsentinel/features/schema.py`

## Phase 3: User Story 2 — Reproducible, honest data foundation (P2, foundational for US1)

**Goal**: Reproducible synthetic data + deterministic versioned features.
**Independent test**: regenerate with same seed → identical rows; transform twice → identical matrix.

- [x] T006 [P] [US2] Deterministic `transform()` + `FEATURE_PIPELINE_VERSION` + `feature_names()` in `src/creditsentinel/features/pipeline.py`
- [x] T007 [P] [US2] Synthetic dataset generator + `PROVENANCE` note in `src/creditsentinel/dataset.py`
- [x] T008 [US2] Tests: determinism, reproducibility, protected-attr exclusion in `tests/test_features.py`

## Phase 4: User Story 1 — Governed, registered PD model (P1, MVP)

**Goal**: Train → govern → gate → register a PD model.
**Independent test**: run pipeline → one governed version registered + reloadable; ungoverned register refused.

- [x] T009 [P] [US1] Core metrics (AUC-ROC, KS, Brier) + calibration in `src/creditsentinel/governance/metrics.py`
- [x] T010 [P] [US1] Model card generation in `src/creditsentinel/governance/model_card.py`
- [x] T011 [US1] `GovernedModel` + `assert_governed` hard gate in `src/creditsentinel/governance/gate.py`
- [x] T012 [US1] `ModelRegistryPort` + MLflow adapter (gate before write, register + load) in `src/creditsentinel/models/registry.py`
- [x] T013 [US1] Training orchestration CLI (`train_and_register`) in `src/creditsentinel/models/train.py`
- [x] T014 [US1] Tests: metrics/gate refusal in `tests/test_governance.py`; register+load roundtrip + registry gate in `tests/test_registry.py`

## Phase 5: User Story 3 — Fairness reading (P3)

**Goal**: Approval-rate parity across the protected attribute at the decline threshold.
**Independent test**: registered version has per-group approval rates + parity gap; protected attr not a feature.

- [x] T015 [P] [US3] `approval_rate_parity()` in `src/creditsentinel/governance/fairness.py`
- [x] T016 [US3] Wire fairness into `train_and_register` + model card; test parity shape in `tests/test_governance.py`

## Phase 6: Polish & Cross-Cutting

- [x] T017 [P] PSI baseline writer (feature/score reference distributions) in `src/creditsentinel/monitoring/baseline.py`
- [x] T018 Write baseline from training run to `data/baseline_stats.json` in `src/creditsentinel/models/train.py`
- [x] T019 [P] Ruff clean + coverage ≥80% on core logic (verify)

## Dependencies

- Setup (T001–T003) → Foundational (T004–T005) → US2 (T006–T008) → US1 (T009–T014) → US3 (T015–T016) → Polish (T017–T019).
- US1 depends on US2 (features) and Foundational (config/schema). US3 depends on US1 (trained model + threshold).

## Parallel opportunities

- T006 ∥ T007 (features vs dataset); T009 ∥ T010 (metrics vs model card); T015 ∥ (US1 metrics) within governance; T017 ∥ T019.

## Implementation strategy

MVP = US1 (governed registered model) built on US2's data/features foundation. US3 and the drift baseline layer on top. Deliver and test each story independently before the next.
