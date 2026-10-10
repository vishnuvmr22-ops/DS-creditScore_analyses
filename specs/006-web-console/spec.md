# Feature Specification: Web Operator Console

**Feature Branch**: `006-web-console`

**Created**: 2026-07-21

**Status**: Draft

**Input**: User description: "Web console UI for CreditSentinel: a professional operator-facing dashboard (Decisioning console, Model Governance, Drift monitoring, Audit log) served as a separate frontend app, plus the read-only API surface it needs."

## Clarifications

### Session 2026-07-21

- Q: How is the console delivered and served relative to the scoring service? → A: The console runs as its own service alongside the existing ones; the browser calls the scoring service directly, restricted to an explicitly allowed set of origins.
- Q: Where does the drift evaluation shown in the console come from? → A: The existing drift job records its report as a durable artifact (with the time it ran and which scenario); the service serves the most recent recorded one and reports "not yet produced" when none exists. First bring-up records an initial evaluation so the view is populated.
- Q: What visual direction does the console take? → A: A restrained, dense institutional treatment — light appearance by default, with a complete and user-switchable dark appearance. Both appearances are first-class and must be legible and accessible.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Score an applicant and read the decision (Priority: P1)

A credit-risk operator opens the console, fills in an applicant's attributes, and submits. Within moments they see the probability of default, the resulting approve / decline / review decision positioned against the active decision thresholds, the top model drivers behind that decision, and the plain-language adverse-action reason with the policy passages it was grounded in. The pinned model version, feature-pipeline version and audit identifier are shown alongside, so the operator can prove which model produced the decision.

**Why this priority**: This is the product. Every other view exists to make this one defensible. A console that only did this would already be worth shipping.

**Independent Test**: Fill the applicant form with a known high-risk profile, submit, and confirm the displayed decision, drivers and reason text match what the scoring service returns for the same input.

**Acceptance Scenarios**:

1. **Given** the console is open and the service is healthy, **When** the operator submits a valid applicant, **Then** the decision, probability of default, top drivers and grounded reason are displayed together with the model version, pipeline version and audit identifier.
2. **Given** an applicant whose value is outside the accepted range for a field, **When** the operator submits, **Then** the offending field is identified inline with a human-readable message and no decision is displayed.
3. **Given** a scored applicant, **When** the operator reads the reason, **Then** every driver the reason cites is visible in the displayed driver list, and the policy references are shown as their source passages.
4. **Given** the operator wants to demonstrate the system quickly, **When** they choose a preset applicant profile, **Then** the form is populated with a profile that reliably produces the corresponding decision.

---

### User Story 2 - Inspect model governance (Priority: P2)

A model-risk reviewer opens the governance view and sees, for the currently served model version, its discrimination and calibration metrics, the calibration curve of predicted versus observed default rates, the fairness comparison across the protected group in the synthetic data, and the generated model card — all clearly labelled as derived from synthetic data.

**Why this priority**: Governance is the differentiator of this project over a plain scoring demo, but it is meaningless until a decision can be produced and shown (P1).

**Independent Test**: Open the governance view with the trained model registered and confirm the displayed metrics, calibration bins and fairness figures match the recorded governance artifacts for that model version.

**Acceptance Scenarios**:

1. **Given** a governed registered model, **When** the reviewer opens the governance view, **Then** discrimination, calibration and fairness metrics are displayed for the exact model version being served.
2. **Given** the calibration data, **When** displayed, **Then** predicted versus observed default rates are shown per bin together with the overall calibration error.
3. **Given** the fairness data, **When** displayed, **Then** approval rate per group, the parity gap and the disparate-impact ratio are shown with a note that a disparity was deliberately injected into the synthetic data.
4. **Given** the model card exists, **When** the reviewer opens it, **Then** its full content is readable in the console.

---

### User Story 3 - Monitor population drift (Priority: P3)

An operations owner opens the drift view and sees, per feature, how far the current scoring population has moved from the training baseline, which features breach the alert threshold, and the overall drift verdict — so they know whether the model is still operating on the population it was trained for.

**Why this priority**: Drift is the "is this still safe to run" signal; valuable, but it depends on both a served model and recorded baselines.

**Independent Test**: Open the drift view after a drift evaluation and confirm the per-feature figures and the overall verdict match the recorded evaluation.

**Acceptance Scenarios**:

1. **Given** a recorded drift evaluation, **When** the view is opened, **Then** each monitored feature shows its drift magnitude, its status against the threshold, and the features are ordered worst-first.
2. **Given** at least one feature breaches the threshold, **When** the view is opened, **Then** the overall verdict reads as drifted and the breaching features are visually distinguished.
3. **Given** no drift evaluation has ever been recorded, **When** the view is opened, **Then** the console explains that no evaluation exists and how to produce one, rather than showing an empty or broken chart.

---

### User Story 4 - Review the decision audit trail (Priority: P4)

A compliance reviewer opens the audit view and sees the most recent decisions in reverse-chronological order — timestamp, pseudonymized applicant reference, probability of default, decision, model and pipeline versions, the drivers recorded at decision time, and whether the reason was model-authored or the deterministic template. They can filter by decision outcome and confirm no raw applicant identifier is ever shown.

**Why this priority**: Completes the governance story and is the natural closing beat of a demo, but is the least load-bearing of the four views.

**Independent Test**: Score several applicants, open the audit view, and confirm the new entries appear newest-first with pseudonymized references and correct decisions.

**Acceptance Scenarios**:

1. **Given** prior decisions exist, **When** the audit view is opened, **Then** the most recent entries are listed newest-first with their decision, probability, versions and recorded drivers.
2. **Given** an audit entry, **When** displayed, **Then** the applicant reference is pseudonymized and no raw identifier or applicant attribute values appear anywhere in the view.
3. **Given** the reviewer filters by an outcome, **When** the filter is applied, **Then** only entries with that outcome are listed.

---

### Edge Cases

- **Scoring service unreachable or still starting**: the console shows an explicit disconnected state naming the service it could not reach, and offers a retry — never a blank screen or a silent failure.
- **Service healthy but no governed model registered**: the console reports the degraded state and explains that a model must be trained and registered, disabling the scoring action rather than letting it fail.
- **Governance, drift or audit data not yet produced**: each view shows a purposeful empty state explaining what to run to produce it.
- **Reason produced by the deterministic template rather than the model**: the console labels which generator authored the reason; the reason is never presented as model-authored when it was not.
- **Very long reason text or an unusually large driver magnitude**: layout absorbs it without clipping or breaking the driver chart's scale.
- **Audit log grown large**: the audit view requests a bounded number of recent entries rather than the whole history.
- **Narrow screens**: all four views remain usable down to tablet width; wide tables and charts scroll within their own region rather than breaking the page.

## Requirements *(mandatory)*

### Functional Requirements

#### Console — decisioning

- **FR-001**: The console MUST let an operator enter every applicant attribute the scoring service accepts, enforcing the same accepted ranges and allowed values before submission, and MUST show field-level, human-readable messages when the service rejects the input.
- **FR-002**: The console MUST display, for a scored applicant: the probability of default, the decision, the active decision thresholds with the probability positioned against them, the top drivers with their direction and magnitude, the reason text, the drivers the reason was grounded in, the policy references, the reason's generator, the model version, the feature-pipeline version and the audit identifier.
- **FR-003**: The console MUST make the drivers visually comparable (relative magnitude and risk direction), not merely list numbers.
- **FR-004**: The console MUST offer preset applicant profiles that demonstrate each decision outcome without manual data entry.
- **FR-005**: The console MUST never display an applicant identifier in a scored result other than the pseudonymized reference returned by the service.

#### Console — governance, drift, audit

- **FR-006**: The console MUST present, for the served model version, its discrimination and calibration metrics, its per-bin predicted-versus-observed calibration data with the overall calibration error, and its fairness figures (approval rate per group, parity gap, disparate-impact ratio).
- **FR-007**: The console MUST make the generated model card readable in the interface.
- **FR-008**: The console MUST present per-feature drift magnitude against the training baseline with each feature's status relative to the alert threshold, ordered worst-first, plus an overall verdict.
- **FR-009**: The console MUST present the most recent decisions newest-first with their timestamp, pseudonymized reference, probability, decision, versions, recorded drivers and reason generator, filterable by outcome, requesting a bounded number of entries.
- **FR-010**: The console MUST display the served model version and service health prominently and continuously, and MUST distinguish healthy from degraded.

#### Console — cross-cutting

- **FR-011**: The console MUST state, visibly and on every view, that all data is synthetic and that no decision shown is a real lending decision.
- **FR-012**: The console MUST NOT persist or transmit applicant attribute values anywhere other than to the scoring service for the scoring request itself.
- **FR-013**: The console MUST render a purposeful empty or error state — naming what is missing and what would produce it — for every view whose data source may be absent or unreachable.
- **FR-014**: The console MUST remain usable and legible from tablet width upward, with oversized tables and charts scrolling within their own region.
- **FR-014a**: The console MUST offer both a light and a dark appearance, light by default, switchable by the viewer and remembered across visits. Both appearances MUST render every view — including all charts and status colours — legibly and completely.
- **FR-014b**: Decision outcomes and drift statuses MUST be distinguishable by more than colour alone (label or shape as well). In both appearances, text MUST meet a contrast ratio of at least **4.5:1** against its background (**3:1** for text at or above 18.66px bold / 24px regular), and non-text indicators that carry meaning — status dots, chart marks, focus rings — MUST meet at least **3:1**.

#### Service — read-only surface

- **FR-015**: The service MUST expose read-only access to the served model version's governance record (discrimination, calibration and fairness figures) and to its model card.
- **FR-016**: The drift job MUST record each evaluation it runs as a durable artifact carrying, at minimum, the per-feature magnitudes, the alert threshold, the overall verdict, the time it ran and which scenario it evaluated — without changing its existing printed output or its pass/fail exit behaviour.
- **FR-016a**: The service MUST expose read-only access to the most recently recorded drift evaluation, and MUST NOT compute a new evaluation in response to a read request.
- **FR-016b**: First bring-up MUST record an initial drift evaluation so the drift view is populated without manual steps.
- **FR-017**: The service MUST expose read-only access to the most recent audit entries, bounded by a caller-supplied limit with a safe default and an enforced maximum, newest-first and filterable by outcome.
- **FR-018**: The service MUST expose the active decision thresholds so the console never hard-codes them.
- **FR-019**: Every read-only response MUST omit raw applicant identifiers and raw applicant attribute values, exposing only pseudonymized references and already-published governance figures.
- **FR-020**: Each read-only endpoint MUST report a distinguishable "not yet produced" condition when its underlying artifact does not exist, rather than failing opaquely.
- **FR-021**: The service MUST permit the console, served from its own origin, to call these endpoints and the scoring endpoint from a browser, restricted to an explicitly configured set of allowed origins.
- **FR-022**: The read-only surface MUST NOT provide any way to mutate models, policies, thresholds or audit records.

#### Delivery

- **FR-023**: The console MUST run as its own service, startable alongside the existing services by the project's single bring-up command, with the scoring service's address supplied as configuration rather than hard-coded.
- **FR-024**: The console MUST be documented in the project README with its address and its purpose.

### Key Entities *(include if feature involves data)*

- **Decision result**: What the console shows after scoring — probability, decision, thresholds, drivers, grounded reason, policy references, pinned versions, audit identifier, pseudonymized reference.
- **Governance record**: The served model version's discrimination metrics, calibration bins with calibration error, fairness figures, and model card.
- **Drift evaluation**: A recorded run of the drift job — per-feature drift magnitudes against the training baseline, the alert threshold, the overall verdict, when it ran and which scenario it evaluated.
- **Audit entry**: A recorded past decision — timestamp, pseudonymized reference, probability, decision, versions, drivers, reason generator.
- **Service status**: Health, whether a governed model is loaded, the served model version and pipeline version, and the active decision thresholds.
- **Applicant draft**: The attribute values held in the console only for the duration of composing and sending one scoring request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time viewer can score an applicant and read its decision, drivers and grounded reason within 60 seconds of opening the console, without reading documentation.
- **SC-002**: 100% of the fields present in a scoring response are surfaced somewhere in the decisioning view — nothing the service returns is silently dropped.
- **SC-003**: Every driver cited in the displayed reason text also appears in the displayed driver list, in 100% of scored results.
- **SC-004**: All four views reach a fully rendered state in under 2 seconds on a local bring-up, and scoring returns a rendered decision in under 3 seconds.
- **SC-005**: Zero raw applicant identifiers or raw applicant attribute values appear in the governance, drift or audit views, verified by inspecting the data the console receives.
- **SC-006**: Each of the four views renders a clear, self-explanatory state when its data source is missing or unreachable — verified by starting the console with each source unavailable in turn.
- **SC-007**: The synthetic-data statement is visible on every view without scrolling.
- **SC-008**: A reviewer can, from the console alone, name the served model version, its discrimination metric, its fairness gap and the current drift verdict within 2 minutes.
- **SC-009**: The console starts as part of the project's single bring-up command with no additional manual steps.
- **SC-010**: All four views remain usable with no horizontal page scrolling from tablet width upward.
- **SC-011**: All four views render completely and legibly in both the light and the dark appearance, with every body and label text pair measuring at least 4.5:1 contrast (3:1 for large text) and every meaning-carrying non-text indicator at least 3:1 — verified view by view in both.
- **SC-012**: Every decision outcome and drift status is identifiable without relying on colour perception.

## Assumptions

- **Audience and access**: The console is a single-operator demonstration and portfolio artifact running locally; there is no authentication, no user accounts and no multi-tenancy. All viewers are trusted and see the same data.
- **Scope boundary**: The console is strictly read-and-score. It does not train models, edit policies, change thresholds, approve model versions, or override decisions — that would breach the governed-registration and determinism invariants.
- **Data source**: All displayed data comes from the existing scoring service and the artifacts the existing offline pipeline already produces; this feature adds no new metrics, no new model behaviour and no new persistence.
- **Freshness**: Governance, drift and audit data are read on demand when a view is opened, refreshable manually. No live streaming or push updates.
- **Batch scoring**: Scoring one applicant at a time is sufficient; bulk upload and batch decisioning are out of scope.
- **Model version scope**: The governance view covers the model version currently being served; browsing historical versions is out of scope (the registry UI already covers that).
- **Drift execution**: Drift evaluations are produced by the existing offline drift job; the console displays the latest recorded evaluation and does not trigger runs.
- **Reason generator**: With no external model key configured the reason is the deterministic template; the console must present this as a labelled, legitimate state rather than a failure.
- **Client-side state**: The viewer's appearance preference is the only thing the console remembers between visits; it holds no applicant data (FR-012).
- **Provenance**: The synthetic-data statement is a hard requirement of the project's governing principles, not a stylistic choice.
