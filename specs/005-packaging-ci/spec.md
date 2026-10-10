# Feature Specification: Packaging, CI & Documentation

**Feature Branch**: `005-packaging-ci`

**Created**: 2026-07-18

**Status**: Draft

**Input**: User description: "Packaging/CI + README — Dockerize; docker-compose brings up API + vector store + MLflow with no manual steps; GitHub Actions runs lint + tests with a coverage gate; README with architecture, run steps, interview talking points, and honest provenance (FR-18..FR-20)."

## Clarifications

### Session 2026-07-18

- Q: What does "no manual steps" mean for `docker compose up`? → A: On first boot the API container trains/registers a governed model and builds the policy store automatically, then serves — a stranger runs one command.
- Q: What gates CI? → A: Lint (ruff) plus the test suite with a coverage floor (≥80% on core logic); failure blocks.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-command local bring-up (Priority: P1)

A newcomer clones the repo and runs a single command; the full system (scoring API, vector store, model registry) comes up with a governed model and policy store already in place, ready to score — no manual setup.

**Why this priority**: The "run it in under 10 minutes" promise is what makes the artifact credible to an interviewer; nothing else matters if it won't start.

**Independent Test**: On a clean machine, run the single bring-up command and confirm the health check reports a loaded model and a score request returns a complete decision.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** the bring-up command runs, **Then** the API, vector store, and registry all start and the API serves.
2. **Given** the stack is up, **When** a valid applicant is scored, **Then** a complete decision (with a grounded reason) is returned.

### User Story 2 - Automated quality gate (Priority: P2)

A contributor pushes a change and an automated pipeline runs linting and the full test suite with a coverage floor, blocking the change if quality regresses.

**Why this priority**: Protects the invariants (determinism, grounding, governance, PII) on every change, but is only meaningful once the system builds and runs (P2).

**Independent Test**: Trigger the pipeline and confirm it runs lint + tests and fails on a lint error or below the coverage floor.

**Acceptance Scenarios**:

1. **Given** a push, **When** the pipeline runs, **Then** it executes lint and the test suite.
2. **Given** coverage below the floor, **When** the pipeline runs, **Then** it fails.

### User Story 3 - Credible, honest documentation (Priority: P3)

A reader (interviewer) opens the README and can, within minutes, understand the architecture, run the system, see concrete talking points, and confirm the data is honestly labeled as synthetic.

**Why this priority**: The documentation converts a working system into a defensible portfolio piece, but depends on the system existing (P3).

**Independent Test**: A reader unfamiliar with the repo follows the README and runs the system in under 10 minutes and can cite ≥5 talking points.

**Acceptance Scenarios**:

1. **Given** the README, **When** a stranger follows it, **Then** they can run the system in under 10 minutes.
2. **Given** the README, **When** read, **Then** it states the data is synthetic and lists concrete interview talking points.

### Edge Cases

- What happens when a required host port is already in use? Documented alternate port mapping; the compose file uses a non-conflicting host port.
- What happens when no external LLM key is provided? The system still runs; reason codes use the deterministic template.
- What happens on first boot with an empty registry? The container trains and registers a governed model before serving.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single command that brings up the API, the vector store, and the model registry with no manual setup steps.
- **FR-002**: On first bring-up, the system MUST ensure a governed model is registered and the policy store is built before serving.
- **FR-003**: The system MUST run, on every push, an automated pipeline executing lint and the full test suite with a coverage floor (≥80% on core logic), failing on violation.
- **FR-004**: The system MUST provide a README with an architecture overview, run steps, at least five concrete interview talking points, and explicit honest data provenance.
- **FR-005**: The system MUST function end-to-end without any external LLM key (reason codes fall back to the deterministic template).

### Key Entities *(include if feature involves data)*

- **Container image**: The runnable packaging of the service and jobs.
- **Compose stack**: API + vector store + model registry services with persisted volumes.
- **CI pipeline**: Lint + test + coverage gate on push.
- **README**: The run guide + architecture + talking points + provenance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A single command brings up all three services and the API serves a complete `/score` decision — verified end-to-end.
- **SC-002**: First bring-up requires 0 manual steps to obtain a governed model + policy store.
- **SC-003**: The CI pipeline runs lint + tests and fails below the coverage floor.
- **SC-004**: A stranger can run the system in under 10 minutes following the README.
- **SC-005**: The README lists ≥5 concrete talking points and labels the data as synthetic.

## Assumptions

- Containerization uses Docker + Docker Compose; CI uses GitHub Actions.
- All three services can run from a single shared image to guarantee matching component versions.
- The demo runs on synthetic data; no external secrets are required to start.
