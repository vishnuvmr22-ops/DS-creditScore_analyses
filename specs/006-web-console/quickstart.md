# Quickstart — Web Operator Console

How to run the console and verify this slice end-to-end. Contract details live in [`contracts/`](./contracts/); field shapes in [`data-model.md`](./data-model.md).

## Prerequisites

- Docker + Docker Compose (path A), or Python 3.12 via `uv` and Node 22 (path B).
- No secrets required. Without `ANTHROPIC_API_KEY` the reason code is the deterministic template — a labelled, legitimate state, not a failure.

## Path A — full stack

```bash
docker compose up --build
```

First boot trains and registers a governed model, builds the policy store, and records an initial drift evaluation, then serves.

| Surface | Address |
|---|---|
| Console | http://localhost:3000 |
| Scoring API | http://localhost:8080 (`/docs`) |
| MLflow UI | http://localhost:5000 |

## Path B — local, two terminals

```bash
# Terminal 1 — service
uv sync --extra dev
uv run creditsentinel-train
uv run creditsentinel-ingest-policy
uv run creditsentinel-drift --scenario stable      # records the first drift evaluation
uv run uvicorn creditsentinel.api.app:app --reload --port 8000

# Terminal 2 — console
cd web && npm install
CS_API_BASE_URL=http://localhost:8000 npm run dev  # http://localhost:3000
```

The service's allowed origins must include the console's address — `CS_CORS_ALLOW_ORIGINS` defaults to `http://localhost:3000`.

---

## Validation scenarios

### V1 — Score and read a decision (US1)

Open the console, choose the high-risk preset, submit.

**Expect**: a decline with its probability placed against the thresholds; three driver bars sized relative to the largest; reason text whose cited drivers all appear in that list; the policy passages it was grounded in; the authoring generator labelled; `model_version`, `feature_pipeline_version`, `audit_id` and a `pseudo_…` reference. Nothing in the response is missing from the view (SC-002).

Cross-check the same payload against the API directly — the console must show what the service returned:

```bash
curl -s -X POST http://localhost:8080/score -H "Content-Type: application/json" -d '{
  "applicant_id":"APP-1","age":24,"annual_income":21000,"employment_length":0.5,
  "debt_to_income":0.95,"credit_utilization":1.4,"num_delinquencies":6,
  "num_open_accounts":14,"loan_amount":42000,"interest_rate":28.0,
  "home_ownership":"RENT","purpose":"debt_consolidation"}'
```

### V2 — Invalid input (US1 scenario 2)

Set debt-to-income to `5` (limit is 2) and submit.

**Expect**: the field is flagged inline with a readable message and no decision is rendered. Then bypass the client check by posting the same body with `curl` and confirm the service answers **422** — the client check is an affordance, the service is the authority.

### V3 — Governance (US2)

Open Governance.

**Expect**: discrimination and probability-accuracy figures, the calibration bins against the perfect-calibration reference plus the overall calibration error, fairness per group with the parity gap and disparate-impact ratio and the injected-disparity note, and the full model card. The stated version matches `/health`.

```bash
curl -s http://localhost:8080/governance | head -20
curl -s http://localhost:8080/health
```

### V4 — Drift, populated and breaching (US3)

```bash
uv run creditsentinel-drift --scenario drift   # exits 1 by design
```

Reload Drift.

**Expect**: the verdict reads drifted, breaching features are distinguished and ordered worst-first, and the run's timestamp and scenario are shown. Re-running `--scenario stable` and reloading flips the verdict back — proving the view reflects *recorded* runs.

**Also verify reads never compute**: read `/drift` twice with no job in between and confirm an identical `run_id` both times (FR-016a).

### V5 — Drift not yet recorded (US3 scenario 3)

Remove `data/drift_runs.jsonl`, restart the service, open Drift.

**Expect**: an explanatory empty state naming the command that produces an evaluation — not a broken or blank chart. The endpoint answers **404** with `status: "not_produced"`.

### V6 — Audit (US4)

Score two or three applicants, open Audit.

**Expect**: newest-first entries with decision, probability, both versions, recorded drivers and reason generator; every reference is `pseudo_…`; filtering by outcome narrows the list.

```bash
curl -s "http://localhost:8080/audit?limit=5&decision=decline"
curl -s "http://localhost:8080/audit?limit=0"     # 422 — below the floor
curl -s "http://localhost:8080/audit?limit=9999"  # 422 — above the cap
```

**Also verify no raw PII (SC-005)**: search the audit response for the identifier you submitted — it must not appear:

```bash
curl -s "http://localhost:8080/audit?limit=200" | grep -c "APP-1"   # expect 0
```

### V7 — Service down and degraded (Edge Cases, SC-006)

Stop the API container and reload the console.

**Expect**: a disconnected state naming the address it tried, with retry — not a blank page. Then start the API with an empty registry: the shell reports degraded, explains that a model must be trained and registered, and the scoring action is disabled.

### V8 — Appearance and accessibility (FR-014a/b, SC-011/012)

Toggle to dark, walk all four views, reload the page.

**Expect**: the preference survives the reload; every view renders completely and legibly in both appearances; decision outcomes and drift statuses remain identifiable from their labels alone with colour disregarded.

### V9 — Responsive (SC-010)

Narrow the window to tablet width.

**Expect**: all four views remain usable; wide tables and charts scroll inside their own region and the page never scrolls horizontally.

### V10 — Origin restriction (FR-021)

From a page on a disallowed origin, call the API.

**Expect**: the browser blocks it — no CORS headers are returned. The same request via `curl` succeeds, confirming the restriction is the browser policy the requirement describes and not a server-side authorization claim.

---

## Automated checks

```bash
uv run pytest --cov=creditsentinel --cov-report=term-missing   # service, ≥80% floor on core
uv run ruff check .
cd web && npm test && npm run lint && npm run build
```

## Definition of done for this slice

- V1–V10 pass.
- Service and console suites green; lint clean on both; coverage floor held.
- `docker compose up --build` brings up all four services and the console is usable with zero manual steps (SC-009).
- README documents the console's address and purpose (FR-024).
