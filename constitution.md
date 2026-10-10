<!--
Sync Impact Report
- Version change: 1.0.1 → 1.1.0 (MINOR: declared stack extended to admit the operator console)
- Modified principles: none (titles I–V unchanged; no principle weakened)
- Added sections: none
- Modified sections: Additional Constraints (Stack & Scope) — the declared stack now names the
  web operator console's technology and bounds it; Development Workflow — build order extended
  with the console slice
- Rationale: slice 006 (web operator console) cannot be built with any listed technology.
  /speckit-analyze finding D1 established that justifying the extension in a plan does not amend
  the constitution, which requires an explicit note and a version bump. This is that amendment.
  Principle V (honest provenance) and Principle III (governed registration) are strengthened, not
  diluted: the console is declared read-only and may never mutate governed state.
- Templates alignment:
  - .specify/templates/plan-template.md → ✅ aligned (Constitution Check present)
  - .specify/templates/spec-template.md → ✅ aligned (no mandatory-section changes)
  - .specify/templates/tasks-template.md → ✅ aligned (test-first task types present)
- Deferred TODOs: none
-->

# CreditSentinel Constitution

> Non-negotiable governing principles for CreditSentinel (build-plan §3). Every spec, plan, task, and implementation MUST comply. Fed to Spec Kit `/speckit.plan` and `/speckit.analyze` gates.

## Core Principles

### I. Test-First (NON-NEGOTIABLE)
Every module ships with tests. Target **≥80% coverage** on core scoring + explanation logic. No feature is "done" without tests. Prefer writing the failing test first for core decision/explanation logic (Red → Green → Refactor). CI must run the suite and block on failure.

### II. Determinism Where It Matters
The Feature Pipeline and model inference are reproducible: pinned seeds, versioned feature transforms, and a pinned model version per response. The same input at the same `feature_pipeline_version` + `model_version` MUST produce identical features and PD. Every `/score` response echoes both versions.

### III. Model Governance Is First-Class
Every model version has: logged metrics (AUC-ROC, KS, Brier, calibration), a generated model card, and recorded fairness metrics (e.g., approval-rate parity across a protected attribute in synthetic data). **Ungoverned models cannot be registered** — the registration path MUST refuse a version missing any governance artifact.

### IV. Explainability Is Mandatory
No decline is returned without (a) SHAP-based top drivers and (b) a plain-language reason code. The LLM reason text MUST be grounded in the actual SHAP drivers + retrieved policy — never free-hallucinated. A test MUST assert that the reason text references the actual top drivers. The deterministic-template fallback obeys the same grounding contract.

### V. PII Discipline & Honest Provenance
No raw PII in logs or in LLM prompts — redact/pseudonymize before any external API call and before any audit-log write, enforced by a redaction step no adapter may bypass. Business metrics over vanity metrics: the README frames decisioning in risk terms (expected loss, approval vs. default rate), not only accuracy. Synthetic or public data is clearly labeled as such everywhere.

## Additional Constraints (Stack & Scope)

- **Stack (service):** Python 3.12 (via `uv`), FastAPI + Pydantic v2, scikit-learn/XGBoost + SHAP, MLflow (tracking + registry), Chroma (RAG store), Anthropic SDK (with deterministic fallback), Docker + docker-compose, pytest, ruff, GitHub Actions.
- **Stack (operator console):** TypeScript on Node LTS with Next.js + React, tested with Vitest, built and run as its own container. Confined to `web/`; HTTP against the service is its only coupling, so the hexagonal core and the service's stack stay untouched. **The console is read-only by construction:** it scores and reads, and MUST NOT expose or invoke any path that mutates models, policies, thresholds or audit records. Presentation logic MUST NOT leak into the service (AD-6).
- **Hard MVP boundary (PRD §6).** No stretch feature is built until the MVP is deployed and demonstrably working end-to-end. Scope creep is the primary failure mode. *(Satisfied as of slice 005: the MVP runs end-to-end under `docker compose up`.)*
- **Architecture compliance.** Every plan/task maps to a PRD FR and complies with the architecture spine's invariants AD-1..AD-6 (hexagonal core; two planes; determinism echoed; grounded explanation; redaction before egress; governed-registration gate).

## Development Workflow & Quality Gates

- Governed implementation proceeds slice by slice (PRD build order): training/governance → scoring API → RAG+reason-code → drift → docker/CI → operator console. Each slice runs the full Spec Kit command flow: `constitution → specify → clarify → plan → tasks → analyze → implement → checklist → converge`.
- **Gate between slices:** tests green + slice demoable before starting the next. Never batch multiple slices into one implement run.
- The `/speckit.analyze` cross-artifact check must pass (no unresolved constitution violations) before `/speckit.implement`.

## Governance

This constitution supersedes other practices. Amendments require an explicit note in the commit/memlog and a version bump here. All work verifies compliance at the `/speckit.analyze` gate before `/speckit.implement`. Runtime development guidance lives in `project-context.md`; the *what/why* in `PRD.md`; the *how* invariants in `architecture.md`.

**Version**: 1.1.0 | **Ratified**: 2026-07-17 | **Last Amended**: 2026-07-21
