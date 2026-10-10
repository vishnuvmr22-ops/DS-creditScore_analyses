# Governance & Quality Checklist: Packaging, CI & Documentation

**Purpose**: Unit-test the REQUIREMENTS against the constitution's non-negotiables — not the implementation.
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)
**Focus**: no-manual-steps bring-up, CI quality gate, honest documentation

## Requirement Completeness

- [x] CHK001 Are the three services that must come up enumerated (API, vector store, registry)? [Completeness, Spec §FR-001]
- [x] CHK002 Is first-boot self-sufficiency specified (governed model + policy store before serving)? [Completeness, Spec §FR-002]
- [x] CHK003 Are the required README contents enumerated (architecture, run steps, ≥5 talking points, provenance)? [Completeness, Spec §FR-004]

## Requirement Clarity

- [x] CHK004 Is "no manual steps" defined concretely (single command yields a scorable service)? [Clarity, Spec §Clarifications]
- [x] CHK005 Is the CI gate quantified (lint + tests + ≥80% coverage floor, fail on violation)? [Clarity, Spec §FR-003]
- [x] CHK006 Is "runs without an external key" defined (template fallback)? [Clarity, Spec §FR-005]

## Requirement Consistency

- [x] CHK007 Do the coverage floor here and the constitution's ≥80% core-coverage rule agree? [Consistency, Constitution §I]
- [x] CHK008 Is the one-shared-image decision consistent with the version-match rationale? [Consistency, Plan §Structure Decision]

## Acceptance Criteria Quality

- [x] CHK009 Is "single command brings up all three and serves a decision" objectively checkable end-to-end? [Measurability, Spec §SC-001]
- [x] CHK010 Is "0 manual steps for a governed model + policy store" measurable? [Measurability, Spec §SC-002]
- [x] CHK011 Is "stranger runs it in <10 minutes" a stated, testable outcome? [Measurability, Spec §SC-004]
- [x] CHK012 Is "≥5 talking points + synthetic-data label" objectively countable? [Measurability, Spec §SC-005]

## Scenario & Edge-Case Coverage

- [x] CHK013 Is the port-conflict scenario addressed (non-conflicting host port documented)? [Edge Case, Spec §Edge Cases]
- [x] CHK014 Is the no-key scenario covered (template reason, still runs)? [Coverage, Spec §Edge Cases]
- [x] CHK015 Is the empty-registry first-boot scenario covered (train before serving)? [Exception Flow, Spec §Edge Cases]

## Constitution Alignment

- [x] CHK016 Does CI enforce lint + the ≥80% coverage gate on every push? [Traceability, Constitution §I]
- [x] CHK017 Does the README require honest synthetic-data provenance? [Traceability, Constitution §V]

## Notes

- All items resolved; no open [Gap]/[Conflict]/[Ambiguity]. Compose bring-up verified live; CI green on Linux.
