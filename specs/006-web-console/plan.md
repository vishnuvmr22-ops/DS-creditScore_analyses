# Implementation Plan: Web Operator Console

**Branch**: `006-web-console` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-web-console/spec.md`

## Summary

Add a four-view operator console — Decisioning, Model Governance, Drift, Audit — as its own containerized web app, plus the read-only surface on the scoring service that feeds it. The console is strictly read-and-score: it calls the existing `POST /score` and four new read endpoints, and has no path to mutate models, policies, thresholds or audit records. Governance figures are read back out of MLflow for the version actually being served; drift gains durable per-run records (the job only printed before); audit reads are bounded and pseudonymized. The frontend is Next.js + TypeScript with hand-built SVG charts on one token-driven colour system, light by default with a first-class dark appearance.

## Technical Context

**Language/Version**: Python 3.12 (service, unchanged) · TypeScript 5 on Node 22 LTS (console)

**Primary Dependencies**: Service — FastAPI, Pydantic v2, MLflow client (all already present); adds only FastAPI's bundled `CORSMiddleware`. Console — Next.js 15 (App Router), React 19, Tailwind CSS v4. No charting, data-fetching or form library (see research R2–R4).

**Storage**: No database. Governance is read from MLflow run artifacts; drift runs append to `data/drift_runs.jsonl`; audit entries read from the existing `data/audit_log.jsonl`. The console persists nothing but the viewer's appearance preference.

**Testing**: pytest + pytest-cov (service, ≥80% floor on core logic per Constitution I) · Vitest + React Testing Library on jsdom (console). Both run in CI; either failing blocks.

**Target Platform**: Linux containers via the existing `docker compose up`; console served on host port 3000, service on 8080.

**Project Type**: Web application — existing Python service plus a new frontend app at `web/`.

**Performance Goals**: Views fully rendered under 2 s and a scored decision rendered under 3 s on a local bring-up (SC-004). Read endpoints do no computation — drift reads never evaluate (FR-016a), governance reads fetch already-logged artifacts.

**Constraints**: Browser-to-service calls restricted to an explicitly configured origin list (FR-021). No mutation surface (FR-022). No raw applicant identifiers or attribute values in any read response (FR-019). Synthetic-data statement visible on every view without scrolling (SC-007). Usable from tablet width up, both appearances legible (FR-014/014a/014b).

**Scale/Scope**: Single-operator local demonstration; no auth, no multi-tenancy. Four views, five endpoints (one existing + four new), twelve applicant input fields, four chart forms.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Verdict |
|---|---|---|
| **I. Test-First** | Every new module ships with tests; core coverage floor ≥80% holds; CI blocks on failure | **PASS** — each new service module (reads router, governance reader, drift store, audit reader) gets its test written before implementation; console gets a Vitest suite; both wired into CI. The ≥80% floor stays measured on the Python core, which this slice does not alter. |
| **II. Determinism Where It Matters** | Same input at pinned versions ⇒ identical features and PD; every `/score` response echoes both versions | **PASS** — no change to the feature pipeline, model or scoring path. The console *displays* both versions (FR-002), strengthening the invariant's visibility. Read endpoints are pure reads. |
| **III. Model Governance Is First-Class** | Every version has logged metrics, model card, fairness; ungoverned models cannot be registered | **PASS** — the console reads governance from the registry rather than recomputing it (research R5), so the registry stays the system of record. No registration path is touched and FR-022 forbids any mutation endpoint, so the governed-registration gate cannot be bypassed through a UI. |
| **IV. Explainability Is Mandatory** | No decline without SHAP drivers + plain-language reason; reason grounded in actual drivers | **PASS** — the console surfaces drivers, reason text, `grounded_in`, `policy_refs` and the authoring generator (FR-002); SC-003 asserts every cited driver is visible. Grounding remains enforced server-side; the console never composes reason text. |
| **V. PII Discipline & Honest Provenance** | No raw PII in logs or prompts; redaction unbypassable; synthetic data labelled everywhere | **PASS** — read responses carry only pseudonymized references (FR-019), the console persists no applicant data (FR-012), and the synthetic-data statement is on every view (FR-011, SC-007). The console adds no new egress: it talks only to the scoring service. |
| **Hard MVP boundary** | No stretch feature until the MVP is deployed and demonstrably working end-to-end | **PASS** — slices 001–005 are complete; the MVP runs end-to-end under `docker compose up` with `/score` returning 200. The boundary is satisfied, so post-MVP work is admissible. |
| **Architecture compliance (AD-1..AD-6)** | Hexagonal core, two planes, determinism echoed, grounded explanation, redaction before egress, governed-registration gate | **PASS** — new capabilities enter as ports + adapters (`GovernanceReaderPort`, `DriftRunStorePort`, `AuditReaderPort`) with the FastAPI router as a driving adapter, matching AD-6. The console is one more driving adapter over the same HTTP contract. |
| **Stack constraint** | Constitution's declared stack | **PASS (as of constitution v1.1.0).** The v1.0.1 stack named no UI technology, so this slice originally ran as a justified deviation. `/speckit-analyze` finding D1 established that a plan-level justification does not amend the constitution, which requires an explicit note and a version bump. The constitution was amended to 1.1.0, declaring the console's stack, bounding it to `web/` with HTTP as its only coupling, and making its read-only nature a constitutional MUST. The deviation is now a declared constraint, and FR-022 plus its verifying test enforce it. |

**Post-Phase-1 re-check**: Re-evaluated after the design artifacts below were written — all verdicts unchanged. The contracts introduce no write verbs, no new egress, and no field carrying raw applicant data; `data-model.md` records that the drift store is append-only and that the audit reader is read-only over a file the scoring path alone writes.

## Project Structure

### Documentation (this feature)

```text
specs/006-web-console/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── console-read-api.md   # The four read endpoints
│   └── console-ui.md         # View-level UI contract
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/creditsentinel/
├── api/
│   ├── app.py               # + CORS middleware, + reads router registration
│   ├── schemas.py           # + governance / drift / audit / decision-policy models
│   ├── reads.py             # NEW — read-only router (driving adapter)
│   ├── audit.py             # + AuditReaderPort, JsonlAuditReader
│   └── service.py           # unchanged
├── models/
│   └── registry.py          # + GovernanceReaderPort, load_governance() on MlflowRegistry
├── monitoring/
│   ├── drift.py             # + record each run through the store (print/exit unchanged)
│   └── runs.py              # NEW — DriftRunStorePort, JsonlDriftRunStore
└── config.py                # + cors_allow_origins, drift_runs_path, audit read caps

tests/
├── test_reads_api.py            # NEW — contract tests for the four endpoints
├── test_drift_runs.py           # NEW — record/read-latest, append-only
├── test_audit_reader.py         # NEW — bounds, ordering, filtering, no raw PII
├── test_governance_read.py      # NEW — governance resolved for the served version
├── test_cors.py                 # NEW — allowed vs unlisted origin
├── test_no_mutation_surface.py  # NEW — POST /score is the only non-idempotent route
└── test_drift.py                # EXTENDED — print/exit unchanged by recording

web/                         # NEW — the console (own service)
├── app/                     # App Router: layout + the four views
├── components/              # Shell, cards, SVG chart primitives, states
├── lib/                     # API client, field spec, formatting, useResource
├── tests/                   # Vitest + RTL
├── Dockerfile
└── next.config.ts

docker/entrypoint.sh         # + record an initial drift evaluation on first boot
docker-compose.yml           # + console service
README.md                    # + console address and purpose
.github/workflows/           # + frontend lint/test job
```

**Structure Decision**: Web-application layout. The Python service keeps its existing hexagonal shape — the new read capabilities enter as ports with adapters (`monitoring/runs.py`, reader classes in `api/audit.py` and `models/registry.py`) exposed through one new driving adapter, `api/reads.py`. The console lives entirely under `web/` as a separate deployable with no build-time coupling to the Python package; its only contract with the service is HTTP.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Stack extension: TypeScript / Node 22 / Next.js (resolved — ratified into constitution v1.1.0 rather than carried as a standing deviation) | The feature *is* a browser UI; no previously listed technology can deliver FR-001..FR-014. Confined to `web/`, with HTTP as the only coupling, so the service's stack and the ports-and-adapters core are untouched. | Serving hand-written HTML/JS from FastAPI would avoid the extension but fails FR-014a/FR-014b (two audited appearances), FR-013 (per-view states) and FR-003 (comparable driver visualisation) at any credible quality, and would put presentation logic inside the service — a direct AD-6 violation. |
| A second test runner (Vitest) alongside pytest | Constitution I requires every module to ship with tests; the console's modules are TypeScript and cannot be exercised by pytest. | Testing the console through pytest would require driving a browser from Python — heavier infrastructure than a second unit-test runner, and slower in CI. |
| New durable artifact (`data/drift_runs.jsonl`) | FR-016/016a require reads to serve a *recorded* evaluation and never compute one. The drift job previously persisted nothing. | Computing drift inside the read request was rejected at Clarify Q2: it puts data generation and model scoring in an HTTP handler and presents fabricated-on-demand output as monitoring. |
