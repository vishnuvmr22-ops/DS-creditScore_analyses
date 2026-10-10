# Feature Specification: Real-Time Scoring API

**Feature Branch**: `002-scoring-api`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "Scoring API core — validate an applicant, transform features, infer PD from the pinned registered model, apply the decision policy, compute SHAP top drivers, return a grounded reason code, and write a PII-safe audit log, all in one request (FR-8..FR-12, FR-15/16)."

## Clarifications

### Session 2026-07-18

- Q: What must a `decline` response always include? → A: Both the top SHAP drivers AND a reason code that references the actual top drivers (no decline without a grounded explanation).
- Q: How is the applicant id handled in logs? → A: Pseudonymized via a one-way salted hash before any audit write; the raw id is never logged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time decision with explanation (Priority: P1)

A risk engineer submits an applicant's details to the service and receives, in a single response, the estimated default probability, an approve/decline/review decision, the top factors that drove the score, and — for a decline — a plain-language reason that cites those factors. A record of the decision is written for audit.

**Why this priority**: This is the product's core promise: a governed, explainable decision in real time. Everything else supports it.

**Independent Test**: Submit a high-risk applicant and confirm the response contains a PD, a decline, non-empty drivers, a reason that references those drivers, and an audit id.

**Acceptance Scenarios**:

1. **Given** a governed model is loaded, **When** a valid applicant is scored, **Then** the response contains PD, decision, thresholds, model + feature versions, drivers, a reason code, and an audit id.
2. **Given** a high-risk applicant, **When** scored, **Then** the decision is decline and the reason references at least one of the actual top drivers.
3. **Given** the same applicant scored twice, **When** compared, **Then** PD, decision, and driver ordering are identical.

### User Story 2 - Reject bad input safely (Priority: P2)

A client sends a malformed or out-of-range applicant payload and receives a clear validation error rather than an unpredictable result.

**Why this priority**: Input trust is a prerequisite for a decision anyone can rely on, but it only matters once scoring exists (P2).

**Independent Test**: Submit a payload with an invalid category or a missing field and confirm a validation error with field detail is returned.

**Acceptance Scenarios**:

1. **Given** a payload with an invalid categorical value, **When** submitted, **Then** the service rejects it with a validation error.
2. **Given** a payload missing a required field, **When** submitted, **Then** the service rejects it with a validation error.

### User Story 3 - PII-safe audit trail (Priority: P3)

A compliance reviewer inspects the audit log and finds a record for every decision that contains no raw personally-identifying applicant id.

**Why this priority**: Auditability is required for a regulated context, but it is a property of the decision path rather than the decision itself (P3).

**Independent Test**: Score an applicant, read the last audit entry, and confirm the id is pseudonymized and the raw id is absent.

**Acceptance Scenarios**:

1. **Given** an applicant is scored, **When** the audit entry is written, **Then** the id is pseudonymized and the raw id does not appear.
2. **Given** an audit entry, **When** inspected, **Then** it records PD, decision, model + feature versions, drivers, and which reason generator was used.

### Edge Cases

- What happens when no governed model is available at startup? Health reports the model is not loaded and scoring is unavailable rather than returning a wrong answer.
- What happens for an approve/review decision? Drivers are still returned; the reason text is neutral/favorable but still references an actual driver.
- What happens with an out-of-range numeric (e.g., negative income)? Rejected by validation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST validate the applicant payload and reject invalid or out-of-range input with a clear, field-level validation error.
- **FR-002**: The system MUST infer PD using the pinned registered model and MUST echo the model version and feature-pipeline version in the response.
- **FR-003**: The system MUST map PD to a decision (approve / decline / review) using configured thresholds and MUST report the thresholds used.
- **FR-004**: The system MUST return the top-N SHAP drivers (signed contribution + risk direction) for every scored decision; a decline MUST always include drivers.
- **FR-005**: The system MUST return a reason code whose text references the actual top drivers; no decline is returned without a grounded reason.
- **FR-006**: The system MUST write exactly one audit-log entry per scored request, with the applicant id pseudonymized and no raw id present.
- **FR-007**: The system MUST expose a health check reporting liveness and whether a governed model is loaded.
- **FR-008**: The system MUST produce identical PD, decision, and driver ordering for identical input (determinism).

### Key Entities *(include if feature involves data)*

- **Score request**: Validated applicant attributes + an applicant id.
- **Score response**: PD, decision, thresholds, model + feature versions, drivers, reason code, audit id.
- **Driver**: A feature with its signed contribution and risk direction.
- **Audit entry**: A PII-safe record of one decision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of valid requests return a complete response (PD, decision, drivers, reason, audit id) in a single call.
- **SC-002**: 100% of decline responses include ≥1 driver and a reason that references an actual top driver.
- **SC-003**: 100% of invalid payloads are rejected with a validation error (no partial scoring).
- **SC-004**: 0 raw applicant ids appear in the audit log.
- **SC-005**: Identical input yields identical PD and driver ordering across repeated calls.

## Assumptions

- The reason code in this feature may be produced by a deterministic template; an LLM-authored variant is a separate feature that shares the same grounding contract.
- The policy retrieval that enriches reason codes is a separate feature; this feature functions with an empty policy set.
- Top-N defaults to 3 drivers; configurable.
- Authentication/rate-limiting are out of scope for this portfolio artifact.
