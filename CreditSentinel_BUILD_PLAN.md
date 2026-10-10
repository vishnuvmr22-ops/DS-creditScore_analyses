# CreditSentinel — Build Plan for Claude Code

> **Working name:** CreditSentinel (rename freely).
> **What it is:** A real-time credit-risk decisioning service with a governed ML model and an LLM explainability layer (adverse-action reason codes + a RAG risk-policy assistant), wrapped in a full MLOps pipeline.
> **Why it exists:** Flagship portfolio project for an **AI/ML Engineer positioned in Financial Risk & Credit**. Every design choice must be defensible in a technical interview by someone who has actually shipped credit-risk models.
> **How it's built:** Spec-Driven Development using **BMAD** (agentic planning) + **GitHub Spec Kit** (governed implementation). See "Framework Workflow" below.

---

## 0. Non-negotiable framing (read first)

This is a **portfolio artifact**, not a research playground. Two rules govern everything:

1. **MVP is the deliverable.** Section 4 defines a hard MVP boundary. Do not build anything in the "Stretch" list until the MVP is deployed and demonstrably working end-to-end. Scope creep is the primary failure mode of this project.
2. **Everything must be interview-defensible.** No inflated claims. If a metric is on synthetic data, say so in the README. The value is a *credible* system, not a fake-impressive one.

The LLM layer must solve a **real** problem (regulatory explainability), not be a bolted-on chatbot. If a feature can't be justified in risk/business terms (expected loss, regulatory reason codes, model governance), it doesn't belong in the MVP.

---

## 1. Problem statement & domain rationale

Lenders must (a) decide whether to extend credit, (b) do it fast enough for real-time origination, (c) **explain** every decline with regulator-acceptable reason codes (e.g., adverse-action notices under fair-lending rules), and (d) prove the model isn't drifting or discriminating. Most ML portfolios show a scoring model and stop. This project shows the *production* concerns that actually matter in a regulated lending context:

- Real-time probability-of-default (PD) scoring via API.
- Human-readable, policy-grounded **explanations** for each decision (the LLM layer's real job).
- **Model governance**: monitoring, drift detection, fairness metrics, a model card.

This mirrors the real work of migrating credit-risk models to production Python services — the candidate's actual experience — so it is defensible under deep questioning.

---

## 2. Target architecture (MVP)

```
                       ┌────────────────────────────────────────────┐
                       │                  Client                     │
                       └───────────────────┬────────────────────────┘
                                           │ POST /score  (applicant features)
                                           ▼
             ┌─────────────────────────────────────────────────────────────┐
             │                     FastAPI service                          │
             │                                                             │
             │  1. Validation (Pydantic v2)                                │
             │  2. Feature pipeline (deterministic, versioned)             │
             │  3. PD model inference  ── loads from Model Registry        │
             │  4. Decision policy (threshold → approve / decline / review)│
             │  5. Explanation layer:                                      │
             │        - SHAP top drivers  ─────────┐                       │
             │        - LLM reason-code generator ◄┘ (grounded in drivers  │
             │          + policy docs via RAG)                             │
             │  6. Structured response + audit log                         │
             └───────────────┬───────────────────────────┬────────────────┘
                             │                           │
                             ▼                           ▼
                 ┌───────────────────┐        ┌────────────────────────┐
                 │  Model Registry    │        │  Risk-Policy RAG store  │
                 │  (MLflow)          │        │  (vector DB: Chroma/    │
                 │  - versioned PD    │        │   pgvector) over policy │
                 │    model + metrics │        │   & model-card docs     │
                 └───────────────────┘        └────────────────────────┘

   Offline (training & governance pipeline):
   raw data → feature engineering → train PD model → evaluate
   → log to MLflow (metrics, params, model) → register model
   → generate model card → compute fairness + calibration
   → monitoring job: PSI / drift on incoming score distributions
```

**Core stack (must match the candidate's defensible skillset):**
- Python 3.11+, FastAPI, Pydantic v2
- scikit-learn / XGBoost for the PD model; SHAP for driver attribution
- MLflow for experiment tracking + model registry
- Chroma **or** pgvector for the RAG policy store
- Anthropic (or OpenAI) API for the reason-code / assistant LLM
- Docker + docker-compose; Pytest; GitHub Actions CI
- Optional: Streamlit or a minimal Next.js page for a demo UI (stretch)

---

## 3. Constitution (non-negotiable principles → goes into spec-kit `constitution.md`)

These become the project's governing rules. Every plan and task must comply.

1. **Test-first.** Every module ships with tests. Target ≥80% coverage on core scoring + explanation logic. No feature is "done" without tests.
2. **Determinism where it matters.** Feature pipeline and model inference are reproducible: pinned seeds, versioned feature transforms, pinned model version per response.
3. **Model governance is first-class.** Every model version has: logged metrics (AUC-ROC, KS, Brier, calibration), a generated model card, and recorded fairness metrics (e.g., approval-rate parity across a protected attribute in synthetic data). Ungoverned models cannot be registered.
4. **Explainability is mandatory.** No decline is returned without (a) SHAP-based top drivers and (b) a plain-language reason code. The LLM reason text must be grounded in the actual SHAP drivers + retrieved policy — never free-hallucinated.
5. **PII discipline.** No raw PII in logs or in LLM prompts. Redact/pseudonymize before any external API call. Document this in the README.
6. **Business metrics over vanity metrics.** README reports decisioning in risk terms (expected-loss framing, approval rate vs. default rate trade-off), not only accuracy.
7. **Honest data provenance.** Synthetic or public data is clearly labeled as such everywhere.

---

## 4. Scope: MVP vs Stretch (HARD boundary)

### MVP — must be complete and deployed before anything else
- [ ] Ingest a public/synthetic credit dataset (e.g., a lending/default dataset) with clear provenance.
- [ ] Reproducible feature pipeline (versioned transforms).
- [ ] Train a PD model; log params/metrics/model to MLflow; register best version.
- [ ] Model card auto-generated for the registered version.
- [ ] Calibration + core metrics (AUC-ROC, KS, Brier) computed and stored.
- [ ] Fairness check on a protected attribute (synthetic) with reported parity metric.
- [ ] FastAPI `/score` endpoint: validate → feature transform → PD inference → decision policy → SHAP drivers → **LLM reason code grounded in drivers + retrieved policy** → structured response + audit log.
- [ ] RAG policy store built over a small set of policy/model-card docs; retrieval feeds the reason-code generator.
- [ ] Drift-monitoring job: compute PSI on incoming feature/score distributions vs. training baseline; flag threshold breaches.
- [ ] Pytest suite (≥80% on core logic), including a test that the LLM reason text references the actual top drivers.
- [ ] Dockerized; docker-compose brings up API + vector store + MLflow.
- [ ] GitHub Actions CI: lint (ruff) + tests on push.
- [ ] README: architecture diagram, how-to-run, **interview talking points**, honest data/metrics provenance.

### Stretch — only after MVP is live
- [ ] Risk-analyst RAG chat endpoint (`/ask`) answering policy/model questions with citations.
- [ ] Streamlit or Next.js demo UI + live deploy (Vercel/Render/Fly).
- [ ] LLM-as-judge eval of reason-code quality (faithfulness to drivers) with RAGAS/DeepEval.
- [ ] Champion/challenger model comparison in MLflow.
- [ ] Prometheus/OpenTelemetry latency + cost instrumentation.
- [ ] Simple retraining trigger on drift breach.

---

## 5. Framework Workflow — how to actually run this in Claude Code

> **Important:** Both BMAD (v6.x) and Spec Kit (v0.10+) evolve fast (near-daily commits). The commands below are current as of mid-2026 — **verify exact command names** with `specify integration list` and the BMAD docs (`docs.bmad-method.org`) before running, and adjust if they've shifted. Do not assume; check.

### Phase A — Planning with **BMAD** (its strength: multi-persona agentic planning)
Goal: produce a rich, domain-aware **PRD** and **architecture** document that later drive implementation.

1. Install: `npx bmad-method install` (in the project repo).
2. Load the **Analyst / PM** agent → run the create-PRD workflow (e.g. `/bmad-bmm-create-prd`). Feed it Sections 1–4 of this document. Output: `PRD.md`.
3. Load the **Architect** agent → run the create-architecture workflow (e.g. `/bmad-bmm-create-architecture`). Feed it the target architecture in Section 2 + the constitution in Section 3. Output: `architecture.md` (+ `db-schema` / API contracts where relevant).
4. Generate BMAD's `project-context.md` to capture conventions.
5. **Gate:** Do not proceed until PRD + architecture reflect the MVP boundary in Section 4. If BMAD tries to expand scope, pull it back to the MVP list.

**Deliverables of Phase A:** `PRD.md`, `architecture.md`, `project-context.md`.

### Phase B — Governed implementation with **Spec Kit** (its strength: constitution + specify→plan→tasks→implement with gates)
Goal: turn the BMAD artifacts into governed, test-first, incremental implementation.

1. Init: `uvx --from git+https://github.com/github/spec-kit.git specify init .` (select Claude Code as the agent). Requires Python 3.11+ and `uv`.
2. `/speckit.constitution` → paste Section 3 of this document as the non-negotiable principles.
3. For each MVP slice (implement in this order — each is one specify→implement cycle):
   1. **Training & governance pipeline** (data → features → train → MLflow → model card → fairness/calibration)
   2. **Scoring API core** (validate → features → PD inference → decision policy → SHAP drivers → response + audit log)
   3. **RAG policy store + LLM reason-code layer** (grounded in drivers + retrieved policy)
   4. **Drift-monitoring job** (PSI vs. baseline)
   5. **Docker/compose + CI**
   For each slice: `/speckit.specify` (feed the slice + relevant BMAD architecture section) → `/speckit.clarify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.analyze` (fix flagged issues) → `/speckit.implement`.
4. **Gate between slices:** tests green + slice demoable before starting the next. Never batch multiple slices into one implement run.

**Why this split:** BMAD's planning agents produce better domain-aware PRD/architecture; Spec Kit's constitution + analyze gate enforces production rigor during coding. Running BMAD's PRD/architecture *into* Spec Kit's specify step avoids the two frameworks generating competing spec artifacts — BMAD owns "what & why + architecture," Spec Kit owns "governed how."

---

## 6. Repo structure (target)

```
creditsentinel/
├── README.md                  # architecture, run steps, interview talking points, provenance
├── constitution.md            # spec-kit governing principles (Section 3)
├── PRD.md                     # from BMAD
├── architecture.md            # from BMAD
├── pyproject.toml             # uv-managed deps
├── docker-compose.yml
├── .github/workflows/ci.yml
├── data/                      # synthetic/public data + provenance note
├── src/creditsentinel/
│   ├── features/              # versioned, deterministic feature pipeline
│   ├── models/                # training, evaluation, calibration, fairness
│   ├── governance/            # model card generation, metrics logging
│   ├── monitoring/            # PSI / drift job
│   ├── api/                   # FastAPI app: /score (+ /ask stretch)
│   ├── explain/               # SHAP drivers + LLM reason-code (grounded)
│   └── rag/                   # policy store ingest + retrieval
├── tests/                     # pytest, ≥80% on core logic
└── mlflow/                    # tracking store (or external)
```

---

## 7. Definition of Done (MVP)

- `docker-compose up` brings up API + vector store + MLflow with no manual steps.
- `POST /score` returns: PD, decision (approve/decline/review), SHAP top drivers, and a grounded LLM reason code, with an audit log entry — in one request.
- A registered model has a model card, calibration + core metrics, and a reported fairness parity metric.
- Drift job runs and flags a synthetic drift scenario.
- CI passes: ruff + pytest (≥80% core coverage), including the "reason text references actual drivers" test.
- README lets a stranger run it in <10 minutes and gives an interviewer 5 concrete talking points.

---

## 8. Interview talking points this project must earn

By the end, the candidate should be able to answer, from real work in this repo:
1. *"Walk me through how you'd serve a credit-risk model in real time."* → the `/score` path.
2. *"How do you keep a production model governed?"* → MLflow registry, model card, calibration, fairness, PSI drift.
3. *"Where does the LLM actually add value here — isn't it just hype?"* → grounded adverse-action reason codes + policy RAG, not free-form chat.
4. *"How do you stop the LLM from hallucinating a reason?"* → grounding in SHAP drivers + retrieved policy, plus the test asserting driver-reference.
5. *"How do you handle PII when calling an external LLM?"* → redaction/pseudonymization before the call.
6. *"What's your test strategy for an ML + LLM system?"* → deterministic core tests + faithfulness assertion + CI gates.

If any talking point can't be backed by real code in the repo, that part isn't done.
