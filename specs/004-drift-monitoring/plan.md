# Implementation Plan: Drift Monitoring

**Branch**: `004-drift-monitoring` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-drift-monitoring/spec.md`

## Summary

A batch job that computes PSI for incoming feature and score distributions against the training baseline written by feature 001, flags features whose PSI ≥ the configured cutoff, and signals a breach (non-zero exit) for automation gating. Ships stable and drift demonstration scenarios. Reads the baseline (AD-1) — never the registry directly for drift, and never trains.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: numpy, pandas; reuses `monitoring/baseline.py` and (optionally) the registry adapter for score PSI
**Storage**: reads `data/baseline_stats.json`
**Testing**: pytest (self-vs-self ≈ 0, injected shift flagged, stable not flagged, score PSI)
**Target Platform**: CLI / CI job
**Project Type**: Offline batch job (single-project layout)
**Performance Goals**: Sub-second over a few-thousand-row batch
**Constraints**: Deterministic bin edges; safe handling of degenerate features
**Scale/Scope**: One baseline, per-feature + score PSI

## Constitution Check

- **I. Test-first**: PASS — `tests/test_drift.py` (self≈0, flag injected drift, stable not flagged, score PSI).
- **II. Determinism**: PASS — fixed decile bin edges from the baseline; reproducible readings.
- **III. Governance-first**: Supports governance (monitoring), no registration.
- **IV. Explainability**: N/A.
- **V. PII discipline**: PASS — operates on distributions, not identities.

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-drift-monitoring/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/drift-cli.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
src/creditsentinel/monitoring/
├── baseline.py     # reference distribution builder (written at training time)
└── drift.py        # psi(), feature_psi(), run_drift(), CLI (creditsentinel-drift)

tests/test_drift.py
```

**Structure Decision**: `drift.py` is a self-contained job that consumes the baseline artifact. Score PSI optionally loads the latest model via the registry adapter but degrades gracefully if unavailable, keeping feature PSI always computable.

## Complexity Tracking

No constitution violations — section intentionally empty.
