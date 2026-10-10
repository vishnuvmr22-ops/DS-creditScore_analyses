# Contract — Drift CLI

## creditsentinel-drift [--scenario stable|drift]
- Loads `data/baseline_stats.json` (errors clearly if missing), builds a batch for the scenario, computes the drift report, prints it as JSON.
- **Exit code**: 0 if no breach; 1 if any feature/score breached (FR-004).
- `--scenario stable`: batch from the same distribution → no breach.
- `--scenario drift`: deliberately shifted batch → breach flagged.

## run_drift(features, baseline, cutoff, scores=None) -> report
- Returns the drift report object (see data-model). Pure function over the baseline.

## psi(expected_props, actual_props) -> float
- PSI between two binned proportion vectors; self-vs-self ≈ 0 (SC-001).
