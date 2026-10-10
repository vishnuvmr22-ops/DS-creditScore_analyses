# Quickstart — Drift Monitoring

## Prerequisites
- A training baseline exists (`uv run creditsentinel-train` writes `data/baseline_stats.json`).

## Run
```bash
uv run creditsentinel-drift --scenario stable   # → "No drift detected", exit 0
uv run creditsentinel-drift --scenario drift    # → "DRIFT DETECTED: [...]", exit 1
```

## Validate
```bash
uv run pytest tests/test_drift.py -q
```
Expected: pass, including `test_psi_zero_for_identical_distribution`, `test_run_drift_flags_injected_drift`, `test_run_drift_stable_batch_not_flagged`, `test_score_psi_reported`.

## Success signals
- Self-vs-self ≈ 0 (SC-001); injected drift flagged (SC-002); stable not flagged (SC-003); exit signal matches flags (SC-004).
