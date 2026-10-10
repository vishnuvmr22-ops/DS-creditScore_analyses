# Quickstart — Training & Governance Pipeline

Validates the feature end-to-end.

## Prerequisites
- Python 3.12 + `uv`
- `uv sync --extra dev`

## Run
```bash
uv run creditsentinel-train
```
Expected: prints the summary JSON (model_version, metrics, calibration_ece, fairness) and exits 0. A `creditsentinel-pd` version appears in the MLflow store; `data/PROVENANCE.md` and `data/baseline_stats.json` are written.

## Validate the governance gate (FR-006 / SC-002)
```bash
uv run pytest tests/test_governance.py tests/test_registry.py -q
```
Expected: tests pass, including `test_gate_rejects_missing_*` and `test_registry_refuses_ungoverned`.

## Validate determinism (SC-003)
```bash
uv run pytest tests/test_features.py -q
```
Expected: `test_transform_is_deterministic`, `test_dataset_generation_reproducible`, and `test_protected_attribute_not_a_feature` pass.

## Success signals
- Summary JSON contains all metric + fairness fields.
- Registered version carries model card + metrics + fairness (governance package complete).
- Protected attribute absent from `feature_names()`.
