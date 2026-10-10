# Feature Specification: Training & Governance Pipeline

**Feature Branch**: `001-training-governance-pipeline`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "Training & governance pipeline for the CreditSentinel credit-risk service — ingest synthetic credit data with provenance, deterministic versioned features, train a PD model, log/register with core metrics + calibration + fairness, auto-generate a model card, and gate registration so ungoverned models cannot be registered (FR-1..FR-7)."

## Clarifications

### Session 2026-07-18

- Q: Which fairness reading defines "parity" for FR-005, and against which decision boundary is it measured? → A: Approval-rate parity (per-group approval rate, parity gap, disparate-impact ratio) measured at the decline threshold — approve = score below the decline threshold.
- Q: Does the governance gate need to block writes to the registry, or only warn? → A: Hard block — registration MUST be refused before anything is written when any governance artifact is missing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce a governed, registered PD model (Priority: P1)

A model developer runs the offline pipeline once and ends up with a probability-of-default model that is recorded in a versioned registry together with everything a model-risk reviewer needs to sign it off: performance metrics, a calibration summary, a fairness reading, and a model card. The model cannot enter the registry unless all of that governance evidence is present.

**Why this priority**: Without a governed, registered model there is nothing for the online service to serve and nothing for a reviewer to audit. This is the foundational slice; every later capability depends on it.

**Independent Test**: Run the pipeline end to end and confirm a new model version appears in the registry with metrics, calibration, fairness, and a model card attached, and that the model can be loaded back for scoring.

**Acceptance Scenarios**:

1. **Given** a clean environment with no registered model, **When** the pipeline runs, **Then** exactly one governed model version is registered and can be reloaded.
2. **Given** a model version that is missing any governance evidence (metrics, calibration, fairness, or model card), **When** registration is attempted, **Then** registration is refused with a clear governance error.
3. **Given** the same input data and configuration, **When** the pipeline is run twice, **Then** the produced features and the model's scores are identical.

### User Story 2 - Reproducible, honest data foundation (Priority: P2)

An analyst needs to trust and reproduce the data the model was trained on. The pipeline generates a synthetic dataset from a fixed seed, writes a provenance note that clearly labels the data as synthetic with no real people, and derives model features through a transform that carries a version identifier.

**Why this priority**: Reproducibility and honest provenance are prerequisites for any defensible metric or fairness claim, but they are only valuable once there is a model to attach them to (hence P2, tightly coupled to P1).

**Independent Test**: Regenerate the dataset twice with the same seed and confirm the rows are identical; confirm a provenance note exists and labels the data as synthetic.

**Acceptance Scenarios**:

1. **Given** a fixed seed, **When** the dataset is generated twice, **Then** both datasets are identical.
2. **Given** a generated dataset, **When** the analyst inspects the accompanying provenance note, **Then** it states the data is synthetic with no real personal information.

### User Story 3 - Fairness reading a reviewer can act on (Priority: P3)

A model-risk reviewer wants evidence that the model is not producing materially different approval rates across a protected group. The pipeline computes an approval-rate parity reading across a protected attribute and records it, while guaranteeing that the protected attribute is never used as a model input.

**Why this priority**: Fairness evidence strengthens the governance package and is required for sign-off, but the pipeline can register a model and report metrics without it, so it ranks after the core governed-model and data stories.

**Independent Test**: Inspect the registered version's fairness reading and confirm per-group approval rates and a parity gap are present, and that the protected attribute does not appear among the model's features.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** fairness is computed, **Then** per-group approval rates and a parity gap/ratio are recorded for the version.
2. **Given** the model's feature set, **When** it is inspected, **Then** the protected attribute is absent from it.

### Edge Cases

- What happens when the pipeline is re-run and a model is already registered? A new version is created; the latest governed version is the one served.
- How does the system handle an attempt to register a model whose governance evidence is incomplete? Registration is refused before anything is written to the registry.
- What happens with a constant or degenerate feature when building the drift baseline? The baseline is still produced with safe bin edges rather than failing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest a labeled credit dataset generated from a pinned seed and MUST record a provenance note that clearly labels the data as synthetic with no real personal information.
- **FR-002**: The system MUST derive model features through a deterministic transform that carries a version identifier, such that identical input at the same version yields identical features.
- **FR-003**: The system MUST train a probability-of-default model and record its parameters, metrics, and the model artifact in a versioned registry.
- **FR-004**: The system MUST compute and store core discrimination metrics (AUC-ROC, KS, Brier) and a calibration summary for each model version.
- **FR-005**: The system MUST compute and store an approval-rate parity reading across a protected attribute, and MUST NOT include the protected attribute among the model's features.
- **FR-006**: The system MUST refuse to register a model version unless its metrics, calibration, fairness reading, and model card are all present.
- **FR-007**: The system MUST auto-generate a model card capturing intended use, data provenance, metrics, fairness, and limitations for each registered version.
- **FR-008**: The system MUST write a distribution baseline of the training features and scores so that later drift monitoring can compare incoming data against it.

### Key Entities *(include if feature involves data)*

- **Applicant record**: One synthetic credit application — numeric and categorical attributes plus a default outcome label and a protected-group label used only for fairness.
- **Model version**: A registered probability-of-default model with a version identifier and an attached governance package.
- **Governance package**: Metrics (AUC-ROC, KS, Brier), a calibration summary, a fairness reading, and a model card — the evidence required for registration.
- **Drift baseline**: A recorded reference distribution of training features and scores for later monitoring.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After one pipeline run, exactly one governed model version is available in the registry and can be reloaded for scoring.
- **SC-002**: 100% of attempts to register a model missing any governance evidence are refused.
- **SC-003**: Re-running the pipeline with the same seed reproduces identical features and identical model scores (bit-for-bit on features).
- **SC-004**: Every registered version carries all four governance artifacts (metrics, calibration, fairness, model card) — verifiable by inspection.
- **SC-005**: The protected attribute appears in 0 of the model's features.

## Assumptions

- Synthetic data generated from a pinned seed is an acceptable, clearly-labeled data source for this portfolio context (no licensed public dataset required).
- Approval-rate parity across a single protected attribute is a sufficient fairness reading for this slice; broader fairness analysis is out of scope here.
- A gradient-boosted tree model is an acceptable default PD model family; the exact algorithm is an implementation detail chosen at planning time.
- The pipeline runs offline/batch; real-time serving is a separate feature.
