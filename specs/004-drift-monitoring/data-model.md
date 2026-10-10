# Phase 1 Data Model — Drift Monitoring

## Training baseline (input artifact)
`features`: {feature → {edges[], props[]}}, `score`: {edges[], props[]}, `n_bins`. Persisted at `data/baseline_stats.json`.
- **Rule**: outer bin edges are open (−inf, +inf); a small epsilon guards empty bins.

## Monitoring batch
A DataFrame of incoming feature rows; optionally scored to a PD array.

## Drift report
```json
{
  "cutoff": 0.20,
  "features": {"debt_to_income": {"psi": 0.61, "breach": true}, "...": {"psi": 0.00, "breach": false}},
  "breached_features": ["debt_to_income"],
  "score": {"psi": 0.03, "breach": false},
  "any_breach": true
}
```
- **Rule (FR-004)**: `any_breach` = (breached_features non-empty) OR (score breached).
