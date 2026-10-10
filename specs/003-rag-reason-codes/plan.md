# Implementation Plan: RAG Policy Store + LLM Reason Codes

**Branch**: `003-rag-reason-codes` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-rag-reason-codes/spec.md`

## Summary

Adds a Chroma-backed policy store and an LLM reason-code adapter to the scoring path. Policy/model-card docs are ingested and retrieved to enrich the reason; the Anthropic adapter authors the text when a key is set, otherwise the deterministic template runs — both satisfy the same grounding contract. Prompts carry only driver labels + policy text (AD-4). Retrieval uses a deterministic offline embedder so the store is reproducible.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: chromadb, anthropic SDK, numpy; reuses `explain/reason.py` and `rag/retriever.py` ports from feature 002
**Storage**: Chroma (embedded PersistentClient locally; HTTP client in compose) over `policies/*.md`
**Testing**: pytest with a fake Anthropic client; a temp Chroma path
**Target Platform**: Linux container / local dev
**Project Type**: Web service extension (adapters behind existing ports)
**Performance Goals**: Retrieval over a small corpus is sub-ms; one LLM call per decline when enabled
**Constraints**: Deterministic embeddings + offline (FR-006); no PII in prompts (AD-4/FR-005); grounded reason always (AD-3/FR-004)
**Scale/Scope**: ~14 policy passages; one LLM provider

## Constitution Check

- **I. Test-first**: PASS — `tests/test_rag.py`, `tests/test_llm_reason.py` (embedding determinism, ingest/retrieve, PII-free prompt, fallback).
- **II. Determinism**: PASS — deterministic embedder; rebuild reproducible (FR-006/SC-004).
- **III. Governance-first**: N/A (no model registration here).
- **IV. Explainability**: PASS — reason references actual drivers + policy; ungrounded LLM output discarded (FR-003/FR-004).
- **V. PII discipline**: PASS — prompt has only labels + policy; no id/raw values (FR-005/SC-003).

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-rag-reason-codes/
├── plan.md · research.md · data-model.md · quickstart.md
├── contracts/reason-and-retrieval.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
policies/                      # source risk-policy + model-card docs (RAG corpus)
src/creditsentinel/
├── rag/
│   ├── embedding.py           # deterministic offline HashingEmbedder
│   ├── store.py               # build_policy_store + ChromaPolicyRetriever (PolicyRetrieverPort)
│   └── ingest.py              # CLI: creditsentinel-ingest-policy
├── explain/
│   ├── reason.py              # PolicyPassage + grounding contract (from feature 002)
│   └── llm_reason.py          # AnthropicReasonAdapter + LLMWithTemplateFallback
└── api/service.py             # selects retriever + reason adapter from settings

tests/
├── test_rag.py                # embedding determinism, ingest/retrieve, service+RAG
└── test_llm_reason.py         # PII-free prompt, adapter grounding, fallback paths
```

**Structure Decision**: The new adapters slot behind the ports defined in feature 002 (`PolicyRetrieverPort`, `ReasonCodePort`). `service.from_settings` chooses the Chroma retriever if the store is built (else Null) and the Anthropic-with-fallback adapter if a key is set (else template) — so the scoring path is unchanged and still fully testable.

## Complexity Tracking

No constitution violations — section intentionally empty.
