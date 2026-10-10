# Governance & Quality Checklist: RAG Policy Store + LLM Reason Codes

**Purpose**: Unit-test the REQUIREMENTS against the constitution's non-negotiables — not the implementation.
**Created**: 2026-07-18
**Feature**: [spec.md](../spec.md)
**Focus**: grounding, graceful fallback, PII discipline, reproducible retrieval

## Requirement Completeness

- [x] CHK001 Are the reason-code fields enumerated (text, grounded drivers, policy refs, generator)? [Completeness, Spec §FR-003]
- [x] CHK002 Is the rebuild-from-source requirement for the policy store stated? [Completeness, Spec §FR-001]
- [x] CHK003 Is the fallback condition set complete (no key, error, ungrounded output)? [Completeness, Spec §FR-004]

## Requirement Clarity

- [x] CHK004 Is "grounded" defined as citing actual top drivers + retrieved policy? [Clarity, Spec §FR-003]
- [x] CHK005 Is the prompt's PII boundary specified (labels + policy only; no id, no raw values)? [Clarity, Spec §FR-005]
- [x] CHK006 Is "deterministic retrieval" defined as reproducible + network-free? [Clarity, Spec §FR-006]

## Requirement Consistency

- [x] CHK007 Do the LLM path and template path share one grounding contract without conflict? [Consistency, Spec §FR-003/FR-004]
- [x] CHK008 Is the "store unbuilt → still grounded in drivers" rule consistent with FR-003? [Consistency, Spec §Edge Cases]

## Acceptance Criteria Quality

- [x] CHK009 Is "decline includes ≥1 policy ref and references a driver" objectively checkable? [Measurability, Spec §SC-001]
- [x] CHK010 Is keyless operation expressed as a measurable outcome (template generator)? [Measurability, Spec §SC-002]
- [x] CHK011 Can "0 ids/raw values in prompt" be objectively verified? [Measurability, Spec §SC-003]
- [x] CHK012 Is deterministic rebuild stated as identical retrievable passages? [Measurability, Spec §SC-004]

## Scenario & Edge-Case Coverage

- [x] CHK013 Is the unbuilt-store scenario covered (retrieval returns nothing, graceful)? [Coverage, Spec §Edge Cases]
- [x] CHK014 Is the ungrounded-LLM-output scenario covered (discard → template)? [Exception Flow, Spec §US2/AC2]
- [x] CHK015 Is offline embedding explicitly required? [Coverage, Spec §FR-006]

## Constitution Alignment

- [x] CHK016 Does the spec preserve the driver-reference grounding assertion (Constitution IV)? [Traceability, Constitution §IV]
- [x] CHK017 Is no-PII-to-external-service required (Constitution V)? [Traceability, Constitution §V]

## Notes

- All items resolved; no open [Gap]/[Conflict]/[Ambiguity].
