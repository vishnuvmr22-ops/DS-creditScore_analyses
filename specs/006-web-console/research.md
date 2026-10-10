# Phase 0 Research — Web Operator Console

All Technical Context unknowns resolved below. No `NEEDS CLARIFICATION` remains.

---

## R1. Frontend framework

**Decision**: Next.js 15 (App Router) + React 19 + TypeScript 5, running as its own containerized service with `output: "standalone"`.

**Rationale**: Clarify Q1 fixed the console as its own service, so it needs a real server process anyway. Next.js gives that server for free and — critically for FR-023 — lets the API base URL be read from the environment **at request time** in a server component and handed down to the client, so one image works across environments. A pure static build would bake the URL in at compile time and need a generated `config.js` shim. App Router + TypeScript is also the least surprising stack for anyone reviewing this repo.

**Alternatives considered**:
- *Vite + React SPA behind nginx* — lighter, but runtime configuration becomes a hand-rolled `env.js` injection at container start. Rejected: solving FR-023 badly to save a Node process.
- *Vue / Nuxt* — equivalent capability, no advantage here, and the rest of the repo's typed-contract style maps more directly onto React + TS interfaces mirroring the Pydantic models.
- *Server-side rendering of the data views* — pointless: Clarify Q1 put data fetching in the browser against the scoring service, so SSR would only proxy. The Next server does exactly one job: serve the app and expose runtime config.

---

## R2. Charts and data visualization

**Decision**: Hand-built SVG chart primitives (driver bars, threshold meter, calibration plot, PSI bars, fairness comparison) sharing one token-driven colour system. No charting dependency.

**Rationale**: Four chart forms, all simple, all needing to look identical in light and dark (FR-014a) and to encode status without relying on colour alone (FR-014b). A chart library would be fought on exactly those two points — theming and semantic colour — for charts that are 40 lines of SVG each. Zero runtime chart deps also keeps the image small and the visual system fully under our control, which is the whole point of "looks professional".

**Alternatives considered**:
- *Recharts* — the default reach; rejected because per-theme restyling of axes/tooltips costs more than writing the marks, and its DOM is hard to assert on in tests.
- *Chart.js / D3 direct* — canvas rendering (Chart.js) breaks text contrast auditing and accessibility; D3 without a wrapper is the same hand-rolled SVG work plus a dependency.

---

## R3. Client data fetching and state

**Decision**: A typed API client module plus a ~30-line `useResource` hook exposing `{ data, error, loading, reload }`. No data-fetching library.

**Rationale**: Five endpoints, no cross-view cache, no invalidation graph, manual refresh only (spec Assumptions: no live streaming). The hook is trivially unit-testable and makes FR-013's empty/error states explicit rather than incidental.

**Alternatives considered**: *TanStack Query* — excellent for cache-coherent apps; here it would add a dependency and a mental model for zero benefit.

---

## R4. Applicant form validation

**Decision**: One declarative field-specification table (name, label, unit, min, max, step, help text, or the allowed values for the two categorical fields) that drives both form rendering and pre-submit validation, mirroring the Pydantic constraints exactly. Server 422 responses are mapped back onto the offending fields by field name.

**Rationale**: FR-001 requires the console to enforce the same ranges as the service *and* to surface server rejections per field. Deriving the form from one table guarantees the two never drift apart and keeps the ranges reviewable in a single place. Client-side checks are a UX affordance; the service stays the authority.

**Alternatives considered**: *react-hook-form + zod* — two dependencies for a single twelve-field form whose rules are already a table.

---

## R5. Where governance data comes from

**Decision**: Read it from MLflow. The registry adapter resolves the served model version → its run → the `metrics.json`, `fairness.json` and `model_card.md` artifacts already logged at registration time.

**Rationale**: Constitution III makes the registry the governance system of record, and registration already writes exactly these three artifacts. Reading local files under `mlflow/artifacts/` instead would work locally and break in Compose, where the API talks to the MLflow server over HTTP and has no shared artifact volume. This also guarantees the console shows governance *for the version actually being served*, which is FR-006's requirement.

**Alternatives considered**:
- *Re-derive metrics at read time* — would recompute governance figures outside the governed registration path. Rejected on Constitution III grounds.
- *Read the JSON artifacts off disk* — breaks in Compose; couples the API to an artifact layout.

---

## R6. Drift evaluation persistence

**Decision**: The drift job appends one JSON object per run to a JSONL store (`data/drift_runs.jsonl`), carrying the report plus `run_id`, `ts` and `scenario`. The read endpoint serves the last line. Written through a `DriftRunStorePort` Protocol with a JSONL adapter — the same port/adapter shape as the existing audit sink.

**Rationale**: Clarify Q2 chose recorded evaluations over on-demand computation. JSONL append is what this codebase already does for audit entries, so it is one pattern rather than two; it is append-only (no rewrite races), naturally ordered, and trivially tailed. The job's printed output and its exit-code behaviour are untouched, so slice 004's contract still holds.

**Alternatives considered**:
- *One file per run under `data/drift/`* — needs directory scanning and timestamp parsing to find the latest.
- *Overwrite a single `latest.json`* — discards history, which is the wrong signal for a monitoring artifact.
- *Log runs to MLflow* — plausible, but drift runs are not model versions; it would blur the registry's meaning and require a run context for a CLI job.

---

## R7. Cross-origin access

**Decision**: FastAPI `CORSMiddleware` restricted to an explicit origin list from settings (`CS_CORS_ALLOW_ORIGINS`, comma-separated, default `http://localhost:3000`), methods limited to `GET, POST`, credentials disabled.

**Rationale**: FR-021 is explicit that the allowed set is configured, not wildcarded. Credentials are off because there is no authentication (spec Assumptions) — allowing them would be security theatre that also forbids wildcard reuse later. `OPTIONS` is handled by the middleware.

**Alternatives considered**: *`allow_origins=["*"]`* — fails FR-021. *Server-side proxying* — rejected at Clarify Q1.

---

## R8. Signalling "not yet produced"

**Decision**: HTTP **404** with a structured body: `{"detail": {"status": "not_produced", "artifact": "...", "remedy": "<command that produces it>"}}`.

**Rationale**: FR-020 needs the console to tell three states apart: service unreachable (network failure), artifact absent (404 with this shape), and genuine server fault (5xx). A 404 carrying the remedy string lets the console render FR-013's empty state — naming what is missing and what would produce it — without hard-coding remedies in the frontend.

**Alternatives considered**: *200 with `{"available": false}`* — makes every consumer check a flag and lets a missing artifact look like success in logs and traces.

---

## R9. Bounded audit reads

**Decision**: `GET /audit?limit=&decision=` with `limit` defaulting to 50 and capped at 200 (over-cap requests are rejected 422 by the query-parameter constraint). The reader reads the log and returns the last `limit` entries, newest-first, filtering by decision before truncation.

**Rationale**: FR-009/FR-017 require bounded reads. Filtering before truncation is the behaviour a reviewer expects ("the 50 most recent declines", not "the declines among the 50 most recent"). The audit log is a local JSONL file of modest size; a full read then tail is honest and simple. If it ever outgrew that, the fix is a reverse line reader behind the same port — the contract does not change.

**Alternatives considered**: *Unbounded reads* — fails FR-017. *Offset pagination* — no user story asks to page through history.

---

## R10. Frontend testing

**Decision**: Vitest + React Testing Library (jsdom) covering the logic-bearing units — API client and error/404 classification, the field-spec validator, driver-bar and PSI scaling maths, decision/status formatting, and each view's empty/error/loaded states with a stubbed client. Wired into CI as a separate job alongside the Python suite.

**Rationale**: Constitution I ("every module ships with tests", CI blocks on failure) applies to the console too. The ≥80% floor is defined for the core scoring and explanation logic and stays measured on the Python suite; the frontend gate is "tests exist and pass", targeting the parts where a bug is silent — a mis-scaled bar or a swallowed error state.

**Alternatives considered**: *Playwright end-to-end* — the strongest evidence, but it needs the whole stack up in CI; the quickstart covers that path manually for this slice. *No frontend tests* — violates Constitution I.

---

## R11. Node runtime and image

**Decision**: `node:22-alpine`, multi-stage build (deps → build → runner), non-root `node` user, standalone output, `NODE_ENV=production`, healthcheck on the app root.

**Rationale**: Matches the existing Compose conventions (every service has a healthcheck; `depends_on` waits on health). Standalone output keeps the runtime image to the traced dependency set. Node 22 is the active LTS line and satisfies Next 15.

**Alternatives considered**: *Reusing the Python image* — would force a Node toolchain into it, contradicting the "one image, matching versions" rationale in the Compose file, which is about the MLflow/Chroma trio.
