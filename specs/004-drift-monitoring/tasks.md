# Tasks: Drift Monitoring

**Feature**: `004-drift-monitoring` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Tests REQUIRED (Constitution I). Depends on feature 001 (baseline). Paths repo-relative.

## Phase 1: Setup

- [x] T001 Add `creditsentinel-drift` console entrypoint in `pyproject.toml`

## Phase 2: Foundational

- [x] T002 [P] PSI baseline builder (reference distributions) in `src/creditsentinel/monitoring/baseline.py`

## Phase 3: User Story 1 — Detect distribution drift (P1, MVP)

**Goal**: Per-feature (+ score) PSI vs baseline; flag breaches; signal result.
**Independent test**: shifted batch → flagged + breach signal; stable → none.

- [x] T003 [US1] `psi()`, `_actual_props`, `feature_psi()`, `run_drift()` report in `src/creditsentinel/monitoring/drift.py`
- [x] T004 [US1] `load_baseline`, batch builder (stable|drift), optional score PSI, CLI + exit code in `src/creditsentinel/monitoring/drift.py`
- [x] T005 [US1] Tests: flag injected drift, stable not flagged, score PSI in `tests/test_drift.py`

## Phase 4: User Story 2 — Reproducible, explainable readings (P2)

**Goal**: self-vs-self ≈ 0; numeric index + breach flag per feature.
**Independent test**: identical distributions → ~0; report has numeric indices.

- [x] T006 [US2] Tests: `test_psi_zero_for_identical_distribution`, `test_feature_psi_small_for_same_distribution` in `tests/test_drift.py`

## Phase 5: Polish & Cross-Cutting

- [x] T007 [P] `psi_cutoff` config default (0.20) in `src/creditsentinel/config.py`
- [x] T008 [P] Ruff clean + coverage maintained (verify)

## Dependencies

- Setup (T001) → Foundational (T002) → US1 (T003–T005) → US2 (T006) → Polish (T007–T008).
- Baseline (T002) is produced during feature 001's training run and consumed here.

## Parallel opportunities

- T007 ∥ T008; T002 is shared with feature 001.

## Implementation strategy

MVP = US1 (detect + signal). US2 adds the interpretability guarantees. Cutoff config in polish.
