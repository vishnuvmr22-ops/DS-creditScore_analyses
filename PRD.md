---
title: CreditSentinel
created: 2026-07-17
updated: 2026-07-17
status: final
source: CreditSentinel_BUILD_PLAN.md (Sections 1–4)
authored_with: BMAD bmm/bmad-prd (headless Create) v6.10.0
---

# PRD: CreditSentinel
*Working title — confirm.*

## 0. Document Purpose
This PRD is for the builder (as portfolio author) and any interviewer/reviewer assessing the system, and it is the upstream input to the BMAD architecture workflow and the GitHub Spec Kit `specify` step. It is derived from `CreditSentinel_BUILD_PLAN.md` Sections 1–4; where the build plan already fixes a decision (stack, MVP boundary, constitution), this PRD restates it as a requirement rather than re-opening it. Vocabulary is Glossary-anchored (§3); features are grouped with globally-numbered FRs nested; inferred decisions are tagged `[ASSUMPTION]` inline and indexed in §9. The governing non-negotiables (test-first, determinism, governance, grounded explainability, PII discipline) live in `constitution.md` and are treated here as cross-cutting NFRs, not re-derived.

## 1. Vision
CreditSentinel is a real-time credit-risk decisioning service that scores a loan applicant's probability of default (PD), turns that score into an approve / decline / review decision, and — critically — **explains every decision with regulator-acceptable, policy-grounded reason codes**. It is wrapped in a full MLOps envelope: versioned model registry, auto-generated model card, calibration and fairness metrics, and drift monitoring.

Most ML portfolios stop at a scoring model. CreditSentinel exists to demonstrate the *production* concerns that actually matter in regulated lending: real-time serving, governed model lifecycle, and defensible explainability. The LLM layer is not a bolted-on chatbot — it solves a real regulatory problem (adverse-action reason codes under fair-lending rules) by generating plain-language declines that are grounded in the model's own SHAP drivers plus retrieved risk policy, never free-hallucinated.

It matters because it mirrors the real work of migrating credit-risk models into production Python services. Every design choice is meant to be defensible in a technical interview by someone who has shipped credit-risk models. The value is a *credible* system on honestly-labeled synthetic/public data, not a fake-impressive one.

## 2. Target User

### 2.1 Jobs To Be Done
- **As the builder:** ship a flagship portfolio artifact that proves AI/ML engineering competence *positioned in financial risk & credit*, defensible under deep questioning.
- **As an interviewer/reviewer (secondary consumer of the artifact):** verify, from real code, that the candidate can serve, govern, and explain a credit model in production.
- **As the simulated lender/risk function (the domain role the system serves):** decide credit fast enough for real-time origination; explain every decline with a regulator-acceptable reason; prove the model isn't drifting or discriminating.

### 2.2 Non-Users (v1)
- Real borrowers / real production traffic — the system runs on synthetic/public data only; no real PII, no real lending decisions.
- Loan officers needing a full case-management UI — out of scope; a demo UI is stretch only.
- Downstream regulators as literal integrators — the system *demonstrates* regulator-acceptable outputs, it does not file notices.

### 2.3 Key User Journeys

- **UJ-1. Dana, a risk engineer, scores an applicant in real time and gets a governed, explainable decision.**
  - **Persona + context:** Dana operates the origination service; she needs a decision plus an audit-ready explanation in one round trip.
  - **Entry state:** service running (`docker-compose up`), a registered, governed PD model loaded from the registry.
  - **Path:** POST applicant features to `/score` → request is validated → deterministic feature transform → PD inference at the pinned model version → decision policy maps PD to approve/decline/review → SHAP top drivers computed → on a decline, an LLM reason code is generated grounded in those drivers + retrieved policy.
  - **Climax:** one JSON response returns PD, decision, SHAP top drivers, and (for declines) a grounded plain-language reason code; an audit-log entry is written.
  - **Resolution:** Dana has a decision she can act on and defend, with a traceable record.
  - **Edge case:** if no LLM API key is configured, the reason code degrades to a deterministic template built from the same SHAP drivers + retrieved policy, so the response is still grounded and the endpoint still works.

- **UJ-2. Morgan, a model-risk reviewer, audits a registered model version.**
  - Morgan opens the model card for a registered version and finds logged core metrics (AUC-ROC, KS, Brier), a calibration summary, and a fairness parity metric across a protected attribute — enough to confirm the model was governed before it could be registered.

- **UJ-3. Sam, an ops engineer, catches drift.**
  - Sam runs the drift job against a batch of incoming feature/score distributions; the job computes PSI versus the training baseline and flags threshold breaches, including a deliberately-injected synthetic drift scenario.

## 3. Glossary
Downstream workflows and readers must use these terms exactly. FRs, UJs, and SMs use these terms verbatim.

- **PD (Probability of Default)** — model-estimated probability in [0,1] that an applicant defaults; the model's raw output before policy.
- **Decision** — one of `approve` / `decline` / `review`, produced by the Decision Policy from the PD.
- **Decision Policy** — the deterministic threshold logic mapping a PD to a Decision (approve below a low cutoff, decline above a high cutoff, review in between). Thresholds are configuration, versioned with the response.
- **Feature Pipeline** — the deterministic, versioned set of transforms turning raw applicant input into model features. Same input + same pipeline version ⇒ same features.
- **SHAP Drivers** — the top-N per-feature SHAP attributions explaining a single PD prediction; the factual basis for any explanation.
- **Reason Code** — the plain-language adverse-action explanation returned on a Decline, grounded in SHAP Drivers + retrieved Policy.
- **Policy Store (RAG)** — vector index over risk-policy and model-card documents; retrieval feeds the Reason Code generator.
- **Model Registry** — MLflow registry holding versioned PD models with their logged params/metrics; a response pins the exact model version used.
- **Model Card** — auto-generated governance document for a registered model version (intended use, data provenance, metrics, fairness, limitations).
- **Fairness Parity Metric** — approval-rate parity (or equivalent) across a protected attribute in the synthetic data.
- **PSI (Population Stability Index)** — drift statistic comparing an incoming distribution to the training baseline.
- **Audit Log** — structured, PII-safe record of each scoring decision (inputs redacted/pseudonymized, PD, decision, model version, drivers, reason).
- **Protected Attribute** — a synthetic attribute (e.g. a group label) used only to compute fairness metrics; never a model feature.

## 4. Features

### 4.1 Training & Governance Pipeline
**Description:** Offline pipeline that ingests a public/synthetic credit dataset with clear provenance, applies the versioned Feature Pipeline, trains a PD model, evaluates it, and logs everything to MLflow. A model version cannot be registered unless it is governed: metrics logged, model card generated, fairness computed. Realizes UJ-2.

**Functional Requirements:**

#### FR-1: Ingest labeled credit dataset with provenance
The pipeline can load a public or synthetic credit/default dataset. Realizes UJ-2.
**Consequences (testable):**
- The dataset source and synthetic/public status are recorded in a provenance note shipped with the data.
- Loading is reproducible (pinned seed for any synthetic generation).

#### FR-2: Deterministic, versioned feature transforms
The Feature Pipeline can transform raw input into model features deterministically and carries a version identifier.
**Consequences (testable):**
- Same input + same pipeline version produces byte-identical features (test-asserted).
- The pipeline version is retrievable and is recorded on every scoring response.

#### FR-3: Train PD model and log to MLflow
The pipeline can train a PD model (scikit-learn / XGBoost) and log params, metrics, and the model artifact to MLflow.
**Consequences (testable):**
- A run appears in MLflow with logged params, metrics, and a loadable model artifact.
- Training uses a pinned seed; re-running yields the same registered metrics within tolerance.

#### FR-4: Compute and store core metrics + calibration
The pipeline can compute AUC-ROC, KS, and Brier score, plus a calibration summary, and store them with the model version.
**Consequences (testable):**
- All three core metrics and a calibration artifact exist for the registered version.

#### FR-5: Compute fairness parity metric
The pipeline can compute a Fairness Parity Metric across a Protected Attribute in the synthetic data.
**Consequences (testable):**
- A reported parity metric exists for the registered version; the Protected Attribute is not among model features.

#### FR-6: Governed registration gate
The pipeline can register the best model version only when metrics, model card, and fairness are present.
**Consequences (testable):**
- Attempting to register a model lacking any governance artifact fails (test-asserted "ungoverned models cannot be registered").

#### FR-7: Auto-generate model card
The pipeline can generate a Model Card for the registered version.
**Consequences (testable):**
- A model card document is produced containing intended use, data provenance (labeled synthetic/public), metrics, fairness, and limitations.

### 4.2 Scoring API Core
**Description:** FastAPI service exposing `POST /score`. It validates the request (Pydantic v2), runs the Feature Pipeline, performs PD inference at the pinned model version, applies the Decision Policy, computes SHAP Drivers, and returns a structured response while writing an Audit Log entry. Realizes UJ-1.

**Functional Requirements:**

#### FR-8: Validate scoring request
`/score` can reject malformed/invalid applicant payloads with a structured validation error. Realizes UJ-1.
**Consequences (testable):**
- Invalid payloads return HTTP 422 with field-level detail; valid payloads proceed.

#### FR-9: PD inference at pinned model version
`/score` can load the registered PD model from the Model Registry and return a PD, recording the exact model version used. Realizes UJ-1.
**Consequences (testable):**
- Response includes the model version; the same input + same version yields the same PD (determinism).

#### FR-10: Decision Policy
`/score` can map PD to a Decision via versioned thresholds. Realizes UJ-1.
**Consequences (testable):**
- PD below low cutoff ⇒ approve; above high cutoff ⇒ decline; between ⇒ review; thresholds are reported.

#### FR-11: SHAP Drivers on every decision
`/score` can return the top-N SHAP Drivers for the prediction. Realizes UJ-1.
**Consequences (testable):**
- Response includes ranked drivers with signed contributions; a Decline always carries drivers.

#### FR-12: Audit Log entry per decision
`/score` can write one PII-safe Audit Log entry per request. Realizes UJ-1.
**Consequences (testable):**
- Each scored request produces a log entry with pseudonymized/redacted inputs, PD, decision, model version, drivers, and (if any) reason code.

### 4.3 RAG Policy Store + LLM Reason-Code Layer
**Description:** A small corpus of risk-policy and model-card documents is ingested into a vector Policy Store. On a Decline, the Reason Code generator retrieves relevant policy and produces a plain-language adverse-action explanation grounded in the SHAP Drivers + retrieved Policy. PII is redacted/pseudonymized before any external LLM call. If no LLM key is configured, generation degrades to a deterministic template over the same drivers + policy. Realizes UJ-1.

**Functional Requirements:**

#### FR-13: Build and query the Policy Store
The system can ingest policy/model-card docs into a vector store (Chroma) and retrieve relevant passages for a decision. Realizes UJ-1.
**Consequences (testable):**
- Retrieval returns relevant passages for a decline scenario; the store is rebuildable from source docs.

#### FR-14: Grounded Reason Code generation
The system can generate a Reason Code for a Decline that references the actual top SHAP Drivers and is grounded in retrieved Policy. Realizes UJ-1.
**Consequences (testable):**
- The reason text references the actual top drivers for that prediction (test-asserted driver-reference).
- No Decline is returned without both SHAP Drivers and a Reason Code.

#### FR-15: PII discipline before external calls
The system can redact/pseudonymize inputs before any external LLM API call. Realizes UJ-1.
**Consequences (testable):**
- No raw PII appears in prompts or logs (test-asserted); redaction is documented in the README.

#### FR-16: Graceful LLM fallback
The system can produce a grounded deterministic-template Reason Code when no LLM API key is configured. Realizes UJ-1.
**Consequences (testable):**
- With no API key set, `/score` still returns a grounded reason code and the endpoint succeeds end-to-end.

### 4.4 Drift Monitoring
**Description:** A batch job computes PSI on incoming feature/score distributions versus the training baseline and flags threshold breaches. Realizes UJ-3.

**Functional Requirements:**

#### FR-17: PSI drift job
The system can compute PSI for incoming distributions against the stored training baseline and flag breaches. Realizes UJ-3.
**Consequences (testable):**
- A deliberately-injected synthetic drift scenario is flagged; a stable scenario is not.

### 4.5 Packaging, CI & Documentation
**Description:** The system is reproducibly runnable and documented for a stranger and an interviewer.

**Functional Requirements:**

#### FR-18: One-command local bring-up
`docker-compose up` can bring up API + vector store + MLflow with no manual steps.
**Consequences (testable):**
- After compose up, `/score` responds successfully against a governed registered model.

#### FR-19: CI gate
GitHub Actions can run ruff lint + pytest on push.
**Consequences (testable):**
- CI fails on lint errors or test failures; passes on a clean tree including the driver-reference test.

#### FR-20: README with provenance and talking points
The README can let a stranger run the system in <10 minutes and give an interviewer 5 concrete talking points, with honest data/metrics provenance.
**Consequences (testable):**
- README contains architecture diagram, run steps, interview talking points, and explicit synthetic/public data labeling.

## 5. Non-Goals (Explicit)
- Not a general chatbot or free-form LLM assistant; the LLM only produces grounded reason codes in the MVP.
- Not making real lending decisions or handling real applicant PII.
- Not a champion/challenger experimentation platform, an LLM-as-judge eval harness, or a live-deployed UI in the MVP (all stretch).
- Not a training-data marketplace or feature store beyond the versioned in-repo Feature Pipeline.

## 6. MVP Scope

### 6.1 In Scope
- Training & governance pipeline (FR-1…FR-7) with MLflow registry, model card, calibration, fairness.
- Scoring API core (FR-8…FR-12) with SHAP drivers and audit log.
- RAG policy store + grounded LLM reason-code layer with PII redaction and graceful fallback (FR-13…FR-16).
- Drift-monitoring job (FR-17).
- Dockerized bring-up, CI, README (FR-18…FR-20).
- Pytest suite ≥80% on core scoring + explanation logic, including the "reason text references actual drivers" test.

### 6.2 Out of Scope for MVP (deferred — stretch)
- `/ask` risk-analyst RAG chat endpoint with citations. `[NOTE FOR PM]` load-bearing for the "LLM adds real value" story; revisit right after MVP.
- Streamlit/Next.js demo UI + live deploy (Vercel/Render/Fly).
- LLM-as-judge faithfulness eval (RAGAS/DeepEval).
- Champion/challenger comparison in MLflow.
- Prometheus/OpenTelemetry latency + cost instrumentation.
- Automated retraining trigger on drift breach.

## 7. Success Metrics
Portfolio/utility framing — the artifact succeeds if it is credible and interview-defensible, on honestly-labeled data.

**Primary**
- **SM-1 (Definition of Done coverage):** every MVP item in §6.1 is complete, tested, and demoable end-to-end via `docker-compose up`. Validates FR-1…FR-20.
- **SM-2 (Grounded explainability):** 100% of Decline responses include SHAP Drivers and a Reason Code that references the actual top drivers (the CI driver-reference test passes). Validates FR-11, FR-14.

**Secondary**
- **SM-3 (Governance completeness):** the registered model version has a model card, core metrics (AUC-ROC, KS, Brier), calibration, and a fairness parity metric. Validates FR-4…FR-7.
- **SM-4 (Interview readiness):** all six talking points in build-plan §8 are backed by real code in the repo. Validates FR-20.

**Counter-metrics (do not optimize)**
- **SM-C1 (No metric inflation):** model performance numbers are never presented as better than the synthetic/public data honestly supports. Counterbalances SM-3 — governance completeness must not become a push to report impressive-but-unearned metrics.
- **SM-C2 (No scope creep):** stretch features (§6.2) count against, not for, the MVP until §6.1 is fully live. Counterbalances SM-1.

## 8. Open Questions
1. Which specific public/synthetic dataset (e.g. a lending/default dataset) to standardize on for provenance? `[ASSUMPTION]` a synthetic generator with pinned seed is acceptable and clearly labeled if a public dataset adds licensing friction.
2. Anthropic model id and exact prompt contract for the reason-code generator (to be fixed in architecture).
3. Exact Decision Policy thresholds and how they trade approval rate vs. default rate (expected-loss framing) — to be calibrated during Slice 1/2.
4. N for "top-N" SHAP drivers surfaced in responses (default assumed 3–5).

## 9. Assumptions Index
- §2.1 / §8.1 — synthetic dataset with pinned seed, clearly labeled, is an acceptable data source given honest-provenance constitution principle.
- §4.3 — Chroma is the vector store (build plan lists Chroma **or** pgvector; Chroma chosen for zero-infra local dev). To confirm in architecture.
- §4.3 / UJ-1 — Anthropic is the LLM provider with a deterministic-template fallback when no key is set (per build decision).
- §3 / FR-10 — Decision Policy is a two-threshold band (approve/review/decline); exact cutoffs deferred.
- §4.2 — top-N SHAP drivers defaults to 3–5, tunable.
