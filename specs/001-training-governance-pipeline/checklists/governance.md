# Governance & Quality Checklist: Training & Governance Pipeline

**Purpose**: Unit-test the REQUIREMENTS (completeness/clarity/consistency/measurability/coverage) against the constitution's non-negotiables — not the implementation.
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)
**Focus**: determinism, governed-registration gate, fairness, honest provenance, test-first

## Requirement Completeness

- [x] CHK001 Are the governance artifacts required for registration enumerated exhaustively (metrics, calibration, fairness, model card)? [Completeness, Spec §FR-006]
- [x] CHK002 Are the specific core metrics named rather than left generic? [Completeness, Spec §FR-004]
- [x] CHK003 Is the drift-baseline output requirement documented as a deliverable of this feature? [Completeness, Spec §FR-008]
- [x] CHK004 Are provenance-note contents specified (synthetic label, seed, no PII)? [Completeness, Spec §FR-001]

## Requirement Clarity

- [x] CHK005 Is "deterministic" defined with an objective criterion (identical input+version ⇒ identical features)? [Clarity, Spec §FR-002]
- [x] CHK006 Is the fairness metric's decision boundary specified (measured at the decline threshold)? [Clarity, Spec §Clarifications]
- [x] CHK007 Is "governed" defined as a concrete set of artifacts rather than a vague adjective? [Clarity, Spec §FR-006]

## Requirement Consistency

- [x] CHK008 Do the fairness requirement and the "protected attribute is never a feature" rule agree without contradiction? [Consistency, Spec §FR-005]
- [x] CHK009 Are the feature-local FR IDs reconciled with the product PRD IDs to avoid reference drift? [Consistency, checklists/requirements.md]

## Acceptance Criteria Quality

- [x] CHK010 Can "ungoverned models cannot be registered" be objectively verified (a refused registration)? [Measurability, Spec §SC-002]
- [x] CHK011 Is reproducibility stated as a measurable outcome (bit-for-bit features)? [Measurability, Spec §SC-003]
- [x] CHK012 Is fairness completeness expressed as a checkable artifact set on the version? [Measurability, Spec §SC-004]

## Scenario & Edge-Case Coverage

- [x] CHK013 Are requirements defined for the re-run scenario (model already registered)? [Coverage, Spec §Edge Cases]
- [x] CHK014 Is the degenerate/constant-feature baseline case addressed? [Edge Case, Spec §Edge Cases]
- [x] CHK015 Is the missing-governance-artifact path specified as a hard refusal before any write? [Exception Flow, Spec §FR-006]

## Constitution Alignment

- [x] CHK016 Does the spec require tests for the core decision/governance logic (test-first)? [Traceability, Constitution §I]
- [x] CHK017 Is honest synthetic-data provenance required everywhere the data appears? [Traceability, Constitution §V]

## Notes

- All items resolved against the current spec; no [Gap]/[Conflict]/[Ambiguity] markers remain open.
- This checklist validates requirement quality; behavioral verification lives in `tasks.md` + tests.
