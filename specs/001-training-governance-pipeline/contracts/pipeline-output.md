# Contract — Training Pipeline Output

The pipeline is invoked as a CLI (`creditsentinel-train`) and is contractually
required to produce the following observable outputs.

## CLI
`creditsentinel-train` → runs generate → transform → train → govern → register → write baseline.
Prints a JSON summary and exits 0 on success.

## Summary JSON (stdout)
```json
{
  "model_version": "1",
  "feature_pipeline_version": "1.0.0",
  "metrics": {"auc_roc": <float>, "ks": <float>, "brier": <float>},
  "calibration_ece": <float>,
  "fairness": {
    "approval_rate_by_group": {"A": <float>, "B": <float>},
    "parity_gap": <float>,
    "disparate_impact_ratio": <float>
  },
  "n_train": <int>,
  "n_test": <int>
}
```

## Registry side effects
- A new **model version** is registered under `creditsentinel-pd` with logged params and metrics, tagged `feature_pipeline_version`.
- Artifacts attached: `model_card.md`, `metrics.json`, `fairness.json`, and the serialized model.

## Filesystem side effects
- `data/applicants.parquet` + `data/PROVENANCE.md` (synthetic-data label).
- `data/baseline_stats.json` (PSI reference).

## Failure contract
- If any governance artifact is missing, registration raises `GovernanceError` and **no version is written**.
