# Phase 0 Research — Drift Monitoring

No NEEDS CLARIFICATION remain.

## Decision: PSI (Population Stability Index) as the drift statistic
- **Rationale**: Industry-standard for credit scorecards; interpretable thresholds (≥0.1 minor, ≥0.2 material shift); works per-feature and on the score.
- **Alternatives**: KS between batches (less standard for monitoring), KL divergence (unbounded, less interpretable), evidently-style suites (heavier dependency).

## Decision: Compare against the training baseline (decile bins)
- **Rationale**: The training distribution is the correct reference; decile bins from training give stable expected proportions. Bin edges + reference proportions are persisted at training time.
- **Alternatives**: Recomputing a reference from a recent batch (rejected — drifts the reference itself).

## Decision: Breach signals non-zero exit
- **Rationale**: Lets the job gate CI/automation and makes the demo scenario check trivial.
- **Alternatives**: Always exit 0 with a flag in output (rejected — harder to gate).

## Decision: Score PSI optional
- **Rationale**: Feature PSI needs no model; score PSI needs the model. Making score PSI optional keeps the job runnable even if the model can't be loaded.
- **Alternatives**: Requiring the model (rejected — reduces robustness).
