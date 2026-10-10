# Implementation Plan: Training & Governance Pipeline

**Branch**: `001-training-governance-pipeline` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-training-governance-pipeline/spec.md`

## Summary

Offline batch pipeline that produces a governed, registered probability-of-default (PD) model from synthetic credit data. It generates reproducible data with provenance, applies a deterministic versioned feature transform, trains a gradient-boosted PD model, computes discrimination + calibration + fairness evidence, auto-generates a model card, and enforces a hard governance gate at registration. A drift baseline is written for the downstream monitoring feature. Technical approach follows the project's hexagonal spine (AD-1 two planes, AD-2 determinism, AD-5 governed-registration gate).

## Technical Context

**Language/Version**: Python 3.12 (pinned via uv; local 3.14 lacks some ML wheels)

**Primary Dependencies**: scikit-learn, XGBoost, SHAP-adjacent (attribution handled in a later slice), MLflow (tracking + registry), pandas, numpy

**Storage**: MLflow with a SQLite backend (`mlflow.db`) + local artifact store; dataset + baseline as files under `data/`

**Testing**: pytest (+ pytest-cov), ruff for lint

**Target Platform**: Linux/Windows dev; Linux container in Docker Compose

**Project Type**: Offline pipeline (CLI entrypoint) within a single-project layout under `src/creditsentinel/`

**Performance Goals**: Not latency-sensitive (batch). Training on ~8k synthetic rows completes in well under a minute on a dev machine.

**Constraints**: Deterministic (pinned seed); reproducible features (version identifier echoed downstream); no network required for data (synthetic).

**Scale/Scope**: Single dataset (~8k rows), one PD model family, one protected attribute for fairness.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Test-first**: PASS — feature ships with `tests/test_features.py`, `test_governance.py`, `test_registry.py`; determinism, gate-refusal, and metric tests included.
- **II. Determinism**: PASS — feature transform carries `FEATURE_PIPELINE_VERSION`; pinned seed; identical features/scores on re-run (SC-003).
- **III. Governance-first**: PASS — `assert_governed` gate blocks registration without metrics + calibration + fairness + model card (FR-006/SC-002).
- **IV. Explainability mandatory**: N/A for this slice (SHAP/reason codes are the scoring + explanation slices); no decision is served here.
- **V. PII discipline & honest provenance**: PASS — data is synthetic with a provenance note; no PII exists to leak.

No violations → Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-training-governance-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (pipeline output contract)
├── checklists/          # requirements.md (from /speckit-specify)
└── tasks.md             # /speckit-tasks output
```

### Source Code (repository root)

```text
src/creditsentinel/
├── config.py                 # Settings: seed, thresholds, mlflow uris, paths
├── dataset.py                # synthetic data generation + provenance note
├── features/
│   ├── schema.py             # canonical fields; PROTECTED_ATTRIBUTE (governance-only)
│   └── pipeline.py           # deterministic transform + FEATURE_PIPELINE_VERSION
├── governance/
│   ├── metrics.py            # AUC-ROC, KS, Brier, calibration
│   ├── fairness.py           # approval-rate parity
│   ├── model_card.py         # model card generation
│   └── gate.py               # GovernedModel + assert_governed (hard gate)
├── models/
│   ├── registry.py           # ModelRegistryPort + MLflow adapter
│   └── train.py              # orchestration CLI (creditsentinel-train)
└── monitoring/
    └── baseline.py           # PSI baseline written here (consumed by drift slice)

tests/
├── test_features.py          # determinism, protected-attr exclusion
├── test_governance.py        # metrics, fairness, gate refusal
└── test_registry.py          # register+load roundtrip, gate at registry boundary
```

**Structure Decision**: Single-project hexagonal layout. Pure core (`features`, `governance/metrics|fairness`) is I/O-free and unit-tested; MLflow is isolated behind `ModelRegistryPort` (`models/registry.py`) so the governance gate runs before any registry write.

## Complexity Tracking

No constitution violations — section intentionally empty.
