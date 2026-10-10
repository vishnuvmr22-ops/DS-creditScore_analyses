# Project Context — CreditSentinel

> Conventions and standing facts for any agent (BMAD / Spec Kit / dev) working in this repo.
> Authored in Phase A (BMAD). Governing rules live in `constitution.md`; the *what/why* in `PRD.md`; the *how* invariants in `architecture.md`.

## What this is
A real-time credit-risk decisioning service: PD scoring + approve/decline/review policy + **grounded** adverse-action reason codes (SHAP drivers + RAG policy) + MLOps governance (MLflow registry, model card, calibration, fairness, PSI drift). Portfolio artifact — must be interview-defensible; synthetic/public data only, honestly labeled.

## Non-negotiables (see constitution.md)
1. Test-first, ≥80% coverage on core scoring + explanation logic.
2. Determinism where it matters — versioned feature pipeline + pinned model version, echoed on every response.
3. Model governance is first-class — ungoverned models cannot be registered.
4. Explainability mandatory — no decline without SHAP drivers + a grounded reason code.
5. PII discipline — redact/pseudonymize before any external LLM call or log write.
6. Business framing over vanity metrics.
7. Honest data provenance — synthetic/public labeled everywhere.

## Architecture invariants (see architecture.md)
- **Paradigm:** hexagonal — pure decisioning core, vendor SDKs only in adapters (AD-6).
- **Two planes:** offline pipeline writes the MLflow registry; online API is read-only, never trains (AD-1).
- **Determinism:** `feature_pipeline_version` + `model_version` pinned and echoed (AD-2).
- **Grounding:** reason code cites actual SHAP drivers; Anthropic and template adapters share one `ReasonCodePort` contract (AD-3).
- **Redaction before egress** (AD-4). **Governed-registration gate** (AD-5).

## Conventions
- Language: Python 3.12 (pinned via `uv`; local 3.14 lacks some ML wheels). Package root `src/creditsentinel/`.
- Ports named `*Port` (typing.Protocol); adapters `*Adapter`. Pydantic v2 models PascalCase.
- Config via env / pydantic-settings `Settings` (thresholds, top_n, psi_cutoff, model name, ANTHROPIC_API_KEY). No magic numbers in core.
- Timestamps ISO-8601 UTC. PD ∈ [0,1]. Validation errors → HTTP 422.
- Missing `ANTHROPIC_API_KEY` is NOT an error → selects deterministic template reason adapter. Missing governed model at startup IS a hard error.
- Tests in `tests/`; must include: driver-reference test, governance-gate test, PSI drift test.

## Toolchain
- Dependency & venv: `uv` (`pyproject.toml` + `uv.lock`).
- Lint: `ruff`. Test: `pytest` + `pytest-cov`. CI: GitHub Actions (ruff + pytest).
- Local run: `docker-compose up` brings up api + mlflow + persisted Chroma.

## Build order (one specify→implement cycle each; gate between slices)
1. Training & governance pipeline
2. Scoring API core
3. RAG policy store + LLM reason-code layer
4. Drift-monitoring job
5. Docker/compose + CI + README

## Phase A artifacts
- `PRD.md` — FR-1..FR-20, MVP boundary, success metrics + counter-metrics.
- `architecture.md` — hexagonal spine, AD-1..AD-6, API contract, capability→architecture map.
- `constitution.md` — the 7 governing principles (also fed to Spec Kit).
- BMAD run memlogs under `_bmad-output/planning-artifacts/`.
