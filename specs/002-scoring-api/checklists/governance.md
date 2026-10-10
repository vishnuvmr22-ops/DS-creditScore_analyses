# Governance & Quality Checklist: Real-Time Scoring API

**Purpose**: Unit-test the REQUIREMENTS against the constitution's non-negotiables — not the implementation.
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)
**Focus**: grounded explainability, determinism, PII discipline, validation, auditability

## Requirement Completeness

- [x] CHK001 Are all response fields enumerated (PD, decision, thresholds, versions, drivers, reason, audit id)? [Completeness, Spec §FR-002..006]
- [x] CHK002 Is the health-check contract specified (liveness + model-loaded)? [Completeness, Spec §FR-007]
- [x] CHK003 Are audit-entry contents specified (pseudonymized id, PD, decision, versions, drivers, generator)? [Completeness, Spec §US3/AC2]

## Requirement Clarity

- [x] CHK004 Is "grounded" defined concretely (reason references actual top drivers)? [Clarity, Spec §FR-005]
- [x] CHK005 Is the decision policy quantified as thresholds (approve/decline/review) rather than described vaguely? [Clarity, Spec §FR-003]
- [x] CHK006 Is "no raw PII" defined as pseudonymization before any write/egress? [Clarity, Spec §Clarifications]

## Requirement Consistency

- [x] CHK007 Do the "decline always includes drivers" and "no decline without grounded reason" rules agree? [Consistency, Spec §FR-004/FR-005]
- [x] CHK008 Are determinism guarantees consistent between the spec and the echoed versions requirement? [Consistency, Spec §FR-002/FR-008]

## Acceptance Criteria Quality

- [x] CHK009 Is "complete response in one call" objectively checkable (field set present)? [Measurability, Spec §SC-001]
- [x] CHK010 Can "0 raw ids in audit" be objectively verified? [Measurability, Spec §SC-004]
- [x] CHK011 Is determinism expressed as a repeatable equality (same input ⇒ same pd/decision/driver order)? [Measurability, Spec §SC-005]

## Scenario & Edge-Case Coverage

- [x] CHK012 Are approve/review reason requirements defined (neutral/favorable but still driver-referencing)? [Coverage, Spec §Edge Cases]
- [x] CHK013 Is the no-governed-model-at-startup case specified (health degraded, scoring unavailable)? [Exception Flow, Spec §Edge Cases]
- [x] CHK014 Are invalid-input requirements defined for both bad category and missing field? [Coverage, Spec §US2]

## Constitution Alignment

- [x] CHK015 Does the spec require a test asserting the reason references actual drivers? [Traceability, Constitution §IV]
- [x] CHK016 Is redaction required before any audit write / external egress? [Traceability, Constitution §V]

## Notes

- All items resolved against the current spec; no open [Gap]/[Conflict]/[Ambiguity].
