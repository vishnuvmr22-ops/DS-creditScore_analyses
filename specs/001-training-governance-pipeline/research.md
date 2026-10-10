# Phase 0 Research — Training & Governance Pipeline

All Technical Context items are resolved; no NEEDS CLARIFICATION remain.

## Decision: PD model family = gradient-boosted trees (XGBoost)
- **Rationale**: Strong tabular baseline for credit risk; native handling of monotone-ish risk signals; pairs cleanly with tree-based SHAP attribution in the explanation slice.
- **Alternatives considered**: Logistic regression (more interpretable but weaker on interactions; kept as the tiny-model choice in tests), random forest (comparable accuracy, less efficient SHAP).

## Decision: Experiment tracking + registry = MLflow with SQLite backend
- **Rationale**: MLflow 3.x removed the file-store backend (maintenance mode); SQLite is the zero-infra supported backend and provides a real model registry with versions. cloudpickle serialization is required because MLflow's default `skops` flavor rejects XGBoost types.
- **Alternatives considered**: Plain pickle files (no versioning/governance surface); Weights & Biases (external service, against zero-infra goal).

## Decision: Fairness metric = approval-rate parity at the decline threshold
- **Rationale**: Directly interpretable for adverse-action/fair-lending framing; measured at the actual decision boundary so it reflects served outcomes. Reports per-group approval rate, parity gap, and disparate-impact ratio.
- **Alternatives considered**: Equalized odds / demographic parity on raw scores (harder to act on for a single-threshold policy in this scope).

## Decision: Governance gate is a hard block before registry write
- **Rationale**: Constitution III — ungoverned models cannot be registered. Enforcing before any write keeps the registry clean and makes the invariant testable.
- **Alternatives considered**: Warn-only (rejected: allows ungoverned versions to persist).

## Decision: Data is synthetic with a pinned seed + provenance note
- **Rationale**: Honest provenance (Constitution V); avoids licensing friction; fully reproducible. A small group disparity is deliberately injected only to make the fairness check non-trivial.
- **Alternatives considered**: A public lending dataset (licensing + PII handling overhead not justified for a portfolio artifact).

## Decision: Drift baseline written at training time
- **Rationale**: The training feature/score distributions are the natural reference for PSI; writing them here decouples the drift slice from retraining.
- **Alternatives considered**: Recomputing a baseline in the drift job (rejected: baseline must be the training reference, not an arbitrary batch).
