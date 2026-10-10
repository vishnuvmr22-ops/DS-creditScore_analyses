# CreditSentinel

📖 **English** · [Español](README.es.md)

**A real-time credit-risk decisioning service with a governed ML model and a grounded LLM explainability layer, wrapped in a full MLOps pipeline.**

CreditSentinel scores an applicant's probability of default (PD), turns that score into an **approve / decline / review** decision, and — the point of the whole project — explains every decision with **regulator-style adverse-action reason codes that are grounded in the model's own SHAP drivers plus retrieved risk policy** (never free-hallucinated). Around that sits the production machinery that actually matters in regulated lending: a versioned model registry, an auto-generated model card, calibration + fairness metrics, and PSI drift monitoring.

> ⚠️ **Data provenance (read first).** All data is **synthetic**, generated from a pinned seed with **no real people and no real PII**. Metric values reflect the synthetic generator, not real-world performance. A small group disparity is *deliberately injected* into the synthetic data purely to make the fairness check non-trivial. Nothing here should be used for real lending decisions. This honesty is a design principle, not a disclaimer — see `constitution.md`.

---

## Architecture

```
Client ──POST /score──►  FastAPI service
                         1. Validate (Pydantic v2)                → 422 on bad input
                         2. Feature pipeline (deterministic, versioned)
                         3. PD inference  ◄──── pinned model version from Model Registry (MLflow)
                         4. Decision policy (thresholds → approve/decline/review)
                         5. Explanation:  SHAP top drivers ─┐
                                          LLM reason code ◄─┘  grounded in drivers
                                          + retrieved policy (Chroma RAG)
                         6. Structured response + PII-safe audit log

Offline pipeline:  synthetic data → features → train PD model → evaluate
                   → log+register to MLflow (metrics, calibration, fairness, model card)
                   → governed-registration gate (ungoverned cannot register)
                   → PSI baseline written for drift monitoring
```

The codebase is **hexagonal (ports & adapters)**: a pure decisioning core (features, decision policy, SHAP, grounding) with MLflow / Chroma / Anthropic / FastAPI as swappable adapters. Full design in [`architecture.md`](architecture.md); requirements in [`PRD.md`](PRD.md); governing principles in [`constitution.md`](constitution.md).

**Stack:** Python 3.12 · FastAPI + Pydantic v2 · scikit-learn / XGBoost + SHAP · MLflow · Chroma · Anthropic (with deterministic fallback) · Docker Compose · Pytest · Ruff · GitHub Actions.

---

## Run it in under 10 minutes

### Option A — Docker Compose (API + Chroma + MLflow, zero manual steps)

```bash
docker compose up --build
```

On first boot the API container trains a governed model, registers it to MLflow, and ingests the policy store — then serves. When it prints `Uvicorn running`, in another terminal:

```bash
# Health
curl http://localhost:8080/health

# Score a high-risk applicant → decline with grounded reason code
curl -X POST http://localhost:8080/score -H "Content-Type: application/json" -d '{
  "applicant_id":"APP-1","age":24,"annual_income":21000,"employment_length":0.5,
  "debt_to_income":0.95,"credit_utilization":1.4,"num_delinquencies":6,
  "num_open_accounts":14,"loan_amount":42000,"interest_rate":28.0,
  "home_ownership":"RENT","purpose":"debt_consolidation"}'
```

- **Operator console: http://localhost:3000** — the visual front door (see below)
- API: http://localhost:8080  (Swagger UI at `/docs`)
- MLflow tracking UI: http://localhost:5000
- Set `ANTHROPIC_API_KEY` in your environment before `up` to enable LLM-authored reason codes; without it the service returns the **deterministic template** reason (still grounded).

### Option B — Local (uv)

```bash
uv sync --extra dev              # Python 3.12
uv run creditsentinel-train      # train + govern + register to ./mlflow, write PSI baseline
uv run creditsentinel-ingest-policy   # build the Chroma policy store from ./policies
uv run uvicorn creditsentinel.api.app:app --reload   # serve on :8000
```

### Using the API

`POST /score` takes a JSON body of applicant attributes (see the `curl` example above) and returns the full determination in one request. Interactive docs live at `http://localhost:8080/docs` (Swagger UI), where you can try every endpoint from the browser. Main endpoints:

- `GET /health` — service status and the model version currently serving.
- `POST /score` — score an applicant; returns PD, decision, thresholds, SHAP drivers, the grounded reason code, and an `audit_id`.

The console also consumes a **read-only** surface on the same service (`/decision-policy`, `/governance`, `/governance/model-card`, `/drift`, `/audit`) — all GET, no mutation verbs.

### Operator console

A four-view web console — **Decisioning, Model Governance, Drift, Audit** — served as its own app at **http://localhost:3000**. Compose starts it alongside the rest; nothing else to do. To run it on its own against a local API:

```bash
cd web
npm install
CS_API_BASE_URL=http://localhost:8080 npm run dev   # http://localhost:3000
```

Score an applicant and read the determination — probability against the policy thresholds, the SHAP drivers behind it, and the grounded adverse-action reason with its policy passages — then inspect the served model's governance (AUC/KS/Brier, calibration curve, fairness), the latest recorded drift evaluation, and the pseudonymized decision audit trail. It is **read-and-score only**: the console has no path to mutate models, policies, thresholds or audit records (constitution v1.1.0).

- **Appearance:** dark by default, with a `light` / `dark` toggle in the header (remembered per browser).
- **Language:** the interface ships in **English and Spanish**, switchable via the `EN` / `ES` toggle beside the appearance one (remembered per browser). The chrome is fully translated; service-authored content — the reason text, the model card, retrieved policy passages — is shown verbatim as the API returned it.

The console reaches the service from the browser, so the API allows its origin explicitly via `CS_CORS_ALLOW_ORIGINS`. Details in [`specs/006-web-console/`](specs/006-web-console/).

### Drift job

```bash
uv run creditsentinel-drift --scenario stable   # PSI vs baseline; exit 0, records the run
uv run creditsentinel-drift --scenario drift    # injected covariate shift → flagged, exit 1
```

Each run is now also recorded to `data/drift_runs.jsonl`; the console's Drift view shows the most recent one.

### Tests & lint

```bash
# Service (Python)
uv run ruff check src tests
uv run pytest --cov=creditsentinel

# Console (TypeScript)
cd web && npm run lint && npm test && npm run build
```

---

## What each response contains

`POST /score` returns, in one request: the `pd`, the `decision`, the `thresholds` used, the `model_version` + `feature_pipeline_version` (determinism), the top **SHAP drivers** with signed contributions, a **grounded reason code** (`text`, the `grounded_in` driver features, `policy_refs`, and which `generator` produced it), and an `audit_id`. The applicant id is pseudonymized; no raw PII is logged or sent to the LLM.

---

## Interview talking points (each backed by real code here)

1. **"Walk me through serving a credit-risk model in real time."** → `src/creditsentinel/api/` — validate → versioned feature pipeline → PD inference at a pinned registry model version → decision policy → SHAP → grounded reason → audit, all in one `/score` call.
2. **"How do you keep a production model governed?"** → `governance/` + `models/registry.py`: MLflow registry, auto model card, AUC-ROC / KS / Brier + calibration, an approval-rate fairness parity metric, and a **governed-registration gate** that refuses ungoverned versions (`test_governance.py`, `test_registry.py`).
3. **"Where does the LLM actually add value — isn't it hype?"** → `explain/` + `rag/`: it produces adverse-action reason codes grounded in the model's own SHAP drivers + retrieved policy, not free-form chat.
4. **"How do you stop the LLM hallucinating a reason?"** → `explain/reason.py::assert_grounded` enforces that the reason references the *actual* top drivers; ungrounded LLM output is discarded in favor of the template (`test_llm_reason.py`, `test_api.py::test_high_risk_declines_with_grounded_reason`).
5. **"How do you handle PII when calling an external LLM?"** → `api/redact.py` pseudonymizes the applicant id before logging, and the LLM prompt (`explain/llm_reason.py`) contains only driver *labels* and policy text — never the id or raw feature values (`test_llm_reason.py::test_prompt_has_no_pii`).
6. **"How do you detect model drift?"** → `monitoring/drift.py`: PSI on incoming feature/score distributions vs. the training baseline, with a demonstrable synthetic drift scenario (`test_drift.py`).
7. **"Test strategy for an ML + LLM system?"** → deterministic core tests (features, decision, drivers) + a faithfulness/driver-reference assertion + a governance gate test + a drift test, all gated in CI at ≥80% core coverage.

---

## Business framing

Decisions are calibrated on an **expected-loss** view, not raw accuracy: the approve / decline / review thresholds trade approval rate against default rate. On the synthetic portfolio (base default rate ≈ 23%) the default policy approves the lowest-PD ~34%, declines the highest-PD ~10%, and routes the rest to manual review — the band where a human underwriter adds the most value. Thresholds are configuration (`CS_APPROVE_BELOW`, `CS_DECLINE_AT_OR_ABOVE`), so the loss trade-off is tunable without code changes.

---

## How this was built (Spec-Driven Development)

Planned with **BMAD** (multi-persona agentic planning → `PRD.md`, `architecture.md`, `project-context.md`) and implemented under **GitHub Spec Kit** governance (`constitution.md` + per-slice specs in `specs/`), one governed slice at a time: training/governance → scoring API → RAG + reason codes → drift → packaging/CI.

## Repository layout

```
src/creditsentinel/  features/ models/ governance/ explain/ rag/ monitoring/ api/  config.py
policies/            risk-policy + model-card docs (RAG corpus)
tests/               pytest suite (core logic, grounding, governance gate, drift)
specs/               Spec Kit feature specs (one per slice)
Dockerfile · docker-compose.yml · .github/workflows/ci.yml
PRD.md · architecture.md · constitution.md · project-context.md
```
