---

description: "Task list for Web Operator Console (slice 006)"
---

# Tasks: Web Operator Console

**Input**: Design documents from `/specs/006-web-console/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: REQUIRED. Constitution I ("Test-First — NON-NEGOTIABLE") applies to every module in this slice; test tasks precede the implementation they cover and must fail first.

**Organization**: Grouped by user story so each is independently implementable and demoable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 Decisioning · US2 Governance · US3 Drift · US4 Audit

## Path Conventions

Web application per plan.md: Python service at `src/creditsentinel/` with `tests/` at repo root; console at `web/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Stand the console project up so anything can be built in it.

- [X] T001 Scaffold the Next.js 15 App Router + TypeScript project at `web/` — `web/package.json`, `web/tsconfig.json`, `web/next.config.ts` (standalone output), `web/app/layout.tsx`, `web/app/page.tsx` placeholder
- [X] T002 [P] Configure Tailwind CSS v4 and declare the light/dark design tokens (surface, text, border, decision, risk-direction, chart scales) in `web/app/globals.css`
- [X] T003 [P] Configure Vitest + React Testing Library on jsdom in `web/vitest.config.ts` and `web/tests/setup.ts`
- [X] T004 [P] Configure ESLint and the `dev`/`build`/`lint`/`test` scripts in `web/eslint.config.mjs` and `web/package.json`
- [X] T005 [P] Add `web/.dockerignore` and `web/.env.example` documenting `CS_API_BASE_URL`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The service's read-only plumbing and the console's shell, client and shared states — every user story depends on these.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Add settings `cors_allow_origins`, `drift_runs_path`, `audit_read_default_limit` (50) and `audit_read_max_limit` (200) in `src/creditsentinel/config.py`
- [X] T007 [P] Test: a configured origin receives CORS headers and an unlisted origin does not, in `tests/test_cors.py`
- [X] T008 Register `CORSMiddleware` from settings (`GET`/`POST`, credentials off) in `src/creditsentinel/api/app.py`
- [X] T008a [P] Test (FR-022): the mounted application exposes exactly one non-idempotent route — `POST /score` — and every route added by this slice is `GET`, in `tests/test_no_mutation_surface.py`
- [X] T009 Create the read-only router with the `not_produced` 404 helper (`status`/`artifact`/`remedy` per contracts/console-read-api.md) in `src/creditsentinel/api/reads.py` and register it in `src/creditsentinel/api/app.py`
- [X] T010 [P] TypeScript types mirroring the service contracts in `web/lib/types.ts`
- [X] T011 [P] Test: API client distinguishes success, `not_produced` 404, server error and unreachable, in `web/tests/api-client.test.ts`
- [X] T012 Typed API client for all five endpoints with that error classification in `web/lib/api.ts`
- [X] T013 [P] Test: `useResource` transitions loading → loaded / failed and reloads on demand, in `web/tests/use-resource.test.ts`
- [X] T014 `useResource` hook in `web/lib/use-resource.ts`
- [X] T015 [P] Runtime configuration — read `CS_API_BASE_URL` server-side and provide it to client components — in `web/lib/config.tsx` and `web/app/layout.tsx`
- [X] T016 [P] Shared Loading / Failed / Empty / NotProduced state components (each naming what is missing and its remedy) in `web/components/states.tsx`
- [X] T017 [P] Test: shell renders the provenance statement on every view, distinguishes healthy from degraded, and persists the appearance choice, in `web/tests/shell.test.tsx`
- [X] T018 App shell — provenance statement, health strip with served versions, four-destination nav, light/dark switch with persistence — in `web/components/shell.tsx` and `web/app/layout.tsx`

**Checkpoint**: Service accepts browser calls from the console's origin; console renders a shell with health and can call the API.

---

## Phase 3: User Story 1 - Score an applicant and read the decision (Priority: P1) 🎯 MVP

**Goal**: An operator enters an applicant and reads the full decision — probability, outcome against thresholds, drivers, grounded reason, pinned versions, audit id.

**Independent Test**: Submit the high-risk preset; the rendered decision, drivers and reason match what `POST /score` returns for the same payload, and every response field is visible (quickstart V1, V2).

### Tests for User Story 1

- [X] T019 [P] [US1] Test: `GET /decision-policy` returns the active thresholds with `approve_below < decline_at_or_above`, in `tests/test_reads_api.py`
- [X] T020 [P] [US1] Test: field-spec validator accepts boundary values and rejects out-of-range per the service's constraints, in `web/tests/field-spec.test.ts`
- [X] T021 [P] [US1] Test: driver bars scale relative to the largest driver and encode direction without colour; threshold meter places the probability correctly in each of the three bands — in `web/tests/decision-viz.test.tsx`
- [X] T022 [P] [US1] Test: decisioning view renders every field of a scored response, maps a server 422 onto the offending field, and disables scoring when degraded — in `web/tests/decisioning.test.tsx`
- [X] T022a [P] [US1] Test (SC-003): every driver named in the rendered reason text also appears in the rendered driver list — in `web/tests/decisioning.test.tsx`
- [X] T022b [P] [US1] Test (FR-012): after scoring, no applicant attribute value is present in any client-side storage, and the client issues no request to a host other than the scoring service — in `web/tests/no-client-persistence.test.ts`

### Implementation for User Story 1

- [X] T023 [US1] Add `DecisionPolicyOut` in `src/creditsentinel/api/schemas.py` and implement `GET /decision-policy` in `src/creditsentinel/api/reads.py`
- [X] T024 [US1] Declarative field-specification table (label, unit, range, step, help, enum values) plus its validator in `web/lib/field-spec.ts`
- [X] T025 [P] [US1] Preset applicant profiles — one per outcome — in `web/lib/presets.ts`
- [X] T026 [P] [US1] Threshold meter component in `web/components/threshold-meter.tsx`
- [X] T027 [P] [US1] Driver bars component (relative magnitude, direction by label and shape) in `web/components/driver-bars.tsx`
- [X] T028 [US1] Applicant form driven by the field spec, with inline per-field messages and preset selection, in `web/components/applicant-form.tsx`
- [X] T029 [US1] Map `POST /score` 422 detail onto field names in `web/lib/api.ts` and surface it in `web/components/applicant-form.tsx`
- [X] T030 [US1] Decision result panel — probability, outcome, threshold meter, drivers, reason text, `grounded_in`, `policy_refs`, generator label, both versions, `audit_id`, pseudonymized reference — in `web/components/decision-result.tsx`
- [X] T031 [US1] Decisioning page wiring form + result + states, scoring disabled while degraded, in `web/app/page.tsx`

**Checkpoint**: US1 fully functional — the console scores and explains a decision on its own.

---

## Phase 4: User Story 2 - Inspect model governance (Priority: P2)

**Goal**: A reviewer sees discrimination, calibration, fairness and the model card for the version actually being served.

**Independent Test**: Open Governance with a registered model; figures match the logged artifacts and the stated version matches `/health` (quickstart V3).

### Tests for User Story 2

- [X] T032 [P] [US2] Test: governance resolves the artifacts of the **served** version's run, and reports not-produced when the registry is empty, in `tests/test_governance_read.py`
- [X] T033 [P] [US2] Test: `GET /governance` and `GET /governance/model-card` contracts — shape, version agreement with `/health`, 404 `not_produced` — in `tests/test_reads_api.py`
- [X] T034 [P] [US2] Test: calibration plot maps bins to the perfect-calibration reference and tolerates a short bin list, in `web/tests/calibration.test.tsx`
- [X] T035 [P] [US2] Test: governance view renders metrics, fairness with the injected-disparity note, the model card, and the not-produced state, in `web/tests/governance-view.test.tsx`

### Implementation for User Story 2

- [X] T036 [US2] Add `GovernanceReaderPort` and `load_governance()` — resolve served version → run → `metrics.json`, `fairness.json`, `model_card.md` — in `src/creditsentinel/models/registry.py`
- [X] T037 [US2] Add `GovernanceOut`, `CalibrationBinOut`, `FairnessOut`, `ModelCardOut` in `src/creditsentinel/api/schemas.py`
- [X] T038 [US2] Implement `GET /governance` and `GET /governance/model-card` in `src/creditsentinel/api/reads.py`
- [X] T039 [P] [US2] Calibration plot (predicted vs observed against the reference diagonal) in `web/components/calibration-plot.tsx`
- [X] T040 [P] [US2] Fairness panel — approval rate per group, parity gap, disparate-impact ratio, injected-disparity note — in `web/components/fairness-panel.tsx`
- [X] T041 [P] [US2] Model card renderer in `web/components/model-card.tsx`
- [X] T042 [US2] Governance page composing metrics, calibration, fairness, model card and states in `web/app/governance/page.tsx`

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 - Monitor population drift (Priority: P3)

**Goal**: An operations owner sees the latest recorded drift evaluation, worst-first, with the overall verdict.

**Independent Test**: Run the drift job in each scenario and confirm the view flips verdict; two reads with no run between them return the identical record (quickstart V4, V5).

### Tests for User Story 3

- [X] T043 [P] [US3] Test: drift run store appends without rewriting, returns the last record as latest, and reports not-produced on an absent file, in `tests/test_drift_runs.py`
- [X] T044 [P] [US3] Test: the drift job's printed output and exit-code behaviour are unchanged by recording, in `tests/test_drift.py`
- [X] T045 [P] [US3] Test: `GET /drift` returns the recorded record verbatim, never computes (identical `run_id` across consecutive reads), and 404s `not_produced` when none exists, in `tests/test_reads_api.py`
- [X] T046 [P] [US3] Test: PSI bars order worst-first and mark breaches by label as well as colour, in `web/tests/psi-bars.test.tsx`
- [X] T047 [P] [US3] Test: drift view renders the verdict, run time and scenario, and the not-produced empty state naming the command, in `web/tests/drift-view.test.tsx`

### Implementation for User Story 3

- [X] T048 [US3] `DriftRunStorePort` + `JsonlDriftRunStore` (append record, read latest) in `src/creditsentinel/monitoring/runs.py`
- [X] T049 [US3] Record each run — `run_id`, `ts`, `scenario` plus the existing report — leaving print and exit code untouched, in `src/creditsentinel/monitoring/drift.py`
- [X] T050 [US3] Add `DriftRunOut` in `src/creditsentinel/api/schemas.py` and implement `GET /drift` in `src/creditsentinel/api/reads.py`
- [X] T051 [US3] Record an initial drift evaluation on first boot in `docker/entrypoint.sh`
- [X] T052 [P] [US3] PSI bars component with the threshold line in `web/components/psi-bars.tsx`
- [X] T053 [US3] Drift page — verdict, run provenance, per-feature bars, score drift when present, states — in `web/app/drift/page.tsx`

**Checkpoint**: US1–US3 independently functional.

---

## Phase 6: User Story 4 - Review the decision audit trail (Priority: P4)

**Goal**: A compliance reviewer reads recent decisions, newest-first, pseudonymized, filterable by outcome.

**Independent Test**: Score a few applicants, open Audit, confirm newest-first pseudonymized entries and that filtering narrows the list (quickstart V6).

### Tests for User Story 4

- [X] T054 [P] [US4] Test: audit reader honours the limit, orders newest-first, filters **before** truncating, skips malformed lines, and never returns a raw identifier, in `tests/test_audit_reader.py`
- [X] T055 [P] [US4] Test: `GET /audit` contract — `count`/`entries`, 422 below floor and above cap, invalid `decision` rejected, empty result is 200 not 404 — in `tests/test_reads_api.py`
- [X] T056 [P] [US4] Test: audit view renders entries and drivers, applies the outcome filter, and shows the empty and not-produced states distinctly, in `web/tests/audit-view.test.tsx`

### Implementation for User Story 4

- [X] T057 [US4] `AuditReaderPort` + `JsonlAuditReader` (bounded, newest-first, filter-then-truncate, malformed-tolerant) in `src/creditsentinel/api/audit.py`
- [X] T058 [US4] Add `AuditEntryOut` and `AuditPageOut` in `src/creditsentinel/api/schemas.py` and implement `GET /audit` with validated `limit`/`decision` query parameters in `src/creditsentinel/api/reads.py`
- [X] T059 [P] [US4] Audit table component (timestamp, pseudonymized reference, probability, decision, versions, drivers, generator) in `web/components/audit-table.tsx`
- [X] T060 [US4] Audit page with the outcome filter and bounded requests in `web/app/audit/page.tsx`

**Checkpoint**: All four stories independently functional.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T061 [P] Multi-stage `web/Dockerfile` (deps → build → runner) on `node:22-alpine`, non-root, standalone output
- [X] T062 Add the `console` service — port 3000, `CS_API_BASE_URL`, healthcheck, `depends_on` the API — in `docker-compose.yml`, and set `CS_CORS_ALLOW_ORIGINS` on the API service
- [X] T063 [P] Add the console lint/test/build job to `.github/workflows/ci.yml`
- [X] T064 [P] Document the console's address and purpose in `README.md`
- [X] T065 Accessibility pass — contrast for body and label text in both appearances, every decision outcome and drift status identifiable without colour (SC-011, SC-012)
- [X] T066 Responsive pass — all four views usable from tablet width with wide tables and charts scrolling within their own region, page never scrolling horizontally (SC-010)
- [X] T067 [P] Run `uv run ruff check .` and `uv run pytest --cov=creditsentinel --cov-report=term-missing`; hold the ≥80% floor on core logic
- [X] T068 [P] Run `npm run lint`, `npm test` and `npm run build` in `web/`
- [X] T069 Verify no raw applicant identifier or attribute value appears in any read response (SC-005) — grep a submitted identifier out of `GET /audit`
- [X] T070 Execute the full `specs/006-web-console/quickstart.md` validation V1–V10 against `docker compose up --build`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup — **blocks all user stories**
- **User Stories (Phases 3–6)**: each depends only on Foundational; they touch disjoint files and can proceed in parallel or in priority order P1 → P2 → P3 → P4
- **Polish (Phase 7)**: depends on the stories being delivered

### User Story Dependencies

- **US1 (P1)**: after Phase 2. No dependency on other stories.
- **US2 (P2)**: after Phase 2. Independent of US1.
- **US3 (P3)**: after Phase 2. Independent — but T051 (initial boot evaluation) is what makes the view populated in a clean bring-up.
- **US4 (P4)**: after Phase 2. Independent of the others; its data is produced by scoring, so demoing it is most natural after US1.

### Within Each User Story

- Tests first and failing, then implementation.
- Service-side port/adapter before the endpoint that exposes it; endpoint before the view that consumes it.
- Chart primitives before the page that composes them.

### Parallel Opportunities

- T002–T005 (Setup) in parallel.
- Within Phase 2: the service track (T006–T009) and the console track (T010–T018) are independent; inside the console track T010/T013/T015/T016/T017 are parallel.
- All test tasks within a story are parallel — different files.
- Chart/component tasks marked [P] within a story are parallel; the page task that composes them is not.
- Across stories: after Phase 2, four developers could take US1–US4 simultaneously; the only shared files are `schemas.py` and `reads.py`, which each story appends to.

---

## Parallel Example: User Story 2

```bash
# All four US2 tests together (each a different file):
Task: "Governance resolves the served version's artifacts in tests/test_governance_read.py"
Task: "GET /governance + /governance/model-card contracts in tests/test_reads_api.py"
Task: "Calibration plot scaling in web/tests/calibration.test.tsx"
Task: "Governance view states in web/tests/governance-view.test.tsx"

# Then the three independent view components together:
Task: "Calibration plot in web/components/calibration-plot.tsx"
Task: "Fairness panel in web/components/fairness-panel.tsx"
Task: "Model card renderer in web/components/model-card.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1
4. **STOP and VALIDATE**: quickstart V1 and V2 pass — the console scores an applicant and shows a grounded, versioned decision.
5. That alone is a demoable console.

### Incremental Delivery

Setup + Foundational → US1 (MVP, demo) → US2 (governance, demo) → US3 (drift, demo) → US4 (audit, demo) → Polish. Each story adds a view without touching the previous ones.

---

## Notes

- [P] = different files, no dependencies on incomplete work.
- Constitution I is non-negotiable here: every test task precedes its implementation and must fail before that implementation exists.
- `src/creditsentinel/api/reads.py`, `src/creditsentinel/api/schemas.py` and `tests/test_reads_api.py` are appended to by all four stories — sequence those edits per story rather than in parallel across stories, despite the per-story `[P]` markers on the test tasks that target them (T019, T033, T045, T055).
- No task in this slice adds a write verb, a new egress, or a field carrying raw applicant data.
- Commit per task or logical group; stop at any checkpoint to validate a story independently.
