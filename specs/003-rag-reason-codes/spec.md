# Feature Specification: RAG Policy Store + LLM Reason Codes

**Feature Branch**: `003-rag-reason-codes`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "RAG policy store + LLM reason-code layer — ingest policy/model-card docs into a vector store, retrieve relevant policy for a decision, and generate an adverse-action reason grounded in the actual SHAP drivers + retrieved policy; use an LLM when a key is configured, else a deterministic template; never send PII to the LLM (FR-13..FR-16)."

## Clarifications

### Session 2026-07-18

- Q: What happens to reason generation when no LLM key is configured or the LLM fails? → A: Degrade gracefully to the deterministic template, which obeys the same grounding contract — the endpoint always returns a grounded reason.
- Q: What may be sent to the LLM? → A: Only driver labels/directions and retrieved policy text — never the applicant id or raw feature values.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Policy-grounded adverse-action reason (Priority: P1)

When an application is declined, the reason returned to the applicant cites both the model's actual top risk factors and the relevant risk-policy passages, so the explanation is specific and defensible rather than generic.

**Why this priority**: Grounded, policy-anchored reason codes are the LLM layer's real value and the project's regulatory justification.

**Independent Test**: Score a decline through the service with the policy store built and confirm the reason references actual drivers and includes policy references.

**Acceptance Scenarios**:

1. **Given** the policy store is built, **When** a decline is scored, **Then** the reason references at least one actual top driver and includes ≥1 policy reference.
2. **Given** relevant policy exists for a decline reason, **When** retrieval runs, **Then** the most relevant policy passages are returned.

### User Story 2 - Works with or without an LLM (Priority: P2)

The service produces a grounded reason whether or not an external LLM is available: with a key it uses the LLM; without one (or on failure) it falls back to a deterministic template that still cites the actual drivers.

**Why this priority**: Reliability and zero-config runnability — the demo must work end-to-end with no external key, and must never fail because the LLM is unavailable.

**Independent Test**: With no key configured, score a decline and confirm a grounded reason is returned with the template generator.

**Acceptance Scenarios**:

1. **Given** no LLM key, **When** a decline is scored, **Then** a grounded reason is returned by the template generator.
2. **Given** the LLM returns an ungrounded reason, **When** validated, **Then** the template reason is used instead.

### User Story 3 - No PII to the LLM (Priority: P3)

When the LLM is used, the prompt contains only the model's driver factors and retrieved policy — no applicant id and no raw feature values.

**Why this priority**: PII discipline is mandatory for a regulated context and for calling any external service.

**Independent Test**: Inspect the constructed LLM prompt and confirm it contains no id and no raw feature values.

**Acceptance Scenarios**:

1. **Given** a decision with drivers, **When** the LLM prompt is built, **Then** it contains driver labels and policy text only — no id, no raw values.

### Edge Cases

- What happens when the policy store has not been built? Retrieval returns nothing and the reason is still grounded in drivers (degrades, does not fail).
- What happens when the LLM output omits the drivers? The output is rejected and the template is used.
- What happens when embeddings must run offline? A deterministic local embedder is used so retrieval works with no network.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest policy and model-card documents into a vector store and MUST support rebuilding the store from source documents.
- **FR-002**: The system MUST retrieve the most relevant policy passages for a given decision/driver context.
- **FR-003**: The system MUST generate a reason code that references the actual top drivers and includes references to the retrieved policy passages used.
- **FR-004**: The system MUST use an external LLM to author the reason when a key is configured, and MUST fall back to a deterministic template when no key is configured or the LLM output is unavailable or ungrounded.
- **FR-005**: The system MUST NOT include the applicant id or raw feature values in any external LLM prompt.
- **FR-006**: Retrieval MUST be deterministic and function without network access (so the store is reproducible).

### Key Entities *(include if feature involves data)*

- **Policy passage**: A retrievable chunk of a policy/model-card document with a stable reference id.
- **Policy store**: The vector index over policy passages, rebuildable from source docs.
- **Reason code**: Grounded adverse-action text with cited drivers, policy references, and the generator used.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of declines (with the store built) include ≥1 policy reference and reference an actual driver.
- **SC-002**: With no LLM key, 100% of scored declines still return a grounded reason (template generator).
- **SC-003**: 0 applicant ids or raw feature values appear in LLM prompts.
- **SC-004**: Rebuilding the store from the same documents yields the same retrievable passages (deterministic).

## Assumptions

- A deterministic local embedder is acceptable for a small policy corpus (lexical overlap retrieves well); a stronger embedder can be swapped behind the same interface.
- The policy corpus is a small curated set of risk-policy and model-card documents shipped with the repo.
- The LLM provider is Anthropic; the exact model id is configuration.
