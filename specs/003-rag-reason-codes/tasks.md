# Tasks: RAG Policy Store + LLM Reason Codes

**Feature**: `003-rag-reason-codes` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Tests REQUIRED (Constitution I). Depends on feature 002 (ports). Paths repo-relative.

## Phase 1: Setup

- [x] T001 Add deps (chromadb, anthropic) in `pyproject.toml`
- [x] T002 [P] Author policy corpus (adverse-action, credit-risk, model-card) in `policies/*.md`
- [x] T003 Add `creditsentinel-ingest-policy` console entrypoint in `pyproject.toml`

## Phase 2: Foundational

- [x] T004 [P] Deterministic offline `HashingEmbedder` (chromadb EF interface, numpy embeddings) in `src/creditsentinel/rag/embedding.py`

## Phase 3: User Story 1 — Policy-grounded adverse-action reason (P1, MVP)

**Goal**: Retrieve policy and cite it + actual drivers in the reason.
**Independent test**: decline through the service with store built → reason cites drivers + ≥1 policy ref.

- [x] T005 [US1] `parse_sections` + `build_policy_store` + `ChromaPolicyRetriever` in `src/creditsentinel/rag/store.py`
- [x] T006 [US1] Ingest CLI in `src/creditsentinel/rag/ingest.py`
- [x] T007 [US1] Wire retriever into `service.from_settings` (try_load Chroma else Null) in `src/creditsentinel/api/service.py`
- [x] T008 [US1] Tests: embedding determinism, ingest/retrieve, service+RAG policy refs in `tests/test_rag.py`

## Phase 4: User Story 2 — Works with or without an LLM (P2)

**Goal**: LLM when key set; deterministic template otherwise / on failure / when ungrounded.
**Independent test**: no key → grounded reason via template generator.

- [x] T009 [US2] `AnthropicReasonAdapter` + `LLMWithTemplateFallback` in `src/creditsentinel/explain/llm_reason.py`
- [x] T010 [US2] Select reason adapter from `anthropic_api_key` in `src/creditsentinel/api/service.py`
- [x] T011 [US2] Tests: fallback on ungrounded output, fallback on error in `tests/test_llm_reason.py`

## Phase 5: User Story 3 — No PII to the LLM (P3)

**Goal**: Prompt carries only driver labels + policy text.
**Independent test**: inspect built prompt → no id, no raw values.

- [x] T012 [US3] `_build_user_prompt` uses only labels/direction + policy in `src/creditsentinel/explain/llm_reason.py`
- [x] T013 [US3] Test: `test_prompt_has_no_pii` in `tests/test_llm_reason.py`

## Phase 6: Polish & Cross-Cutting

- [x] T014 [P] Config: `chroma_host`/`chroma_port` (server mode) + `ANTHROPIC_API_KEY` alias in `src/creditsentinel/config.py`
- [x] T015 [P] Ruff clean + coverage maintained (verify)

## Dependencies

- Setup (T001–T003) → Foundational (T004) → US1 (T005–T008) → US2 (T009–T011) → US3 (T012–T013) → Polish (T014–T015).
- US1/US2/US3 all reuse feature 002 ports; no change to the decision path.

## Parallel opportunities

- T002 ∥ T004; T009 ∥ (US1 store work is done); T014 ∥ T015.

## Implementation strategy

MVP = US1 (policy-grounded reason). US2 adds LLM+fallback resilience; US3 enforces PII discipline. Config toggles in polish.
