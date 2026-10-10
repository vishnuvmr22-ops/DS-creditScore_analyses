# Quickstart — RAG Policy Store + LLM Reason Codes

## Prerequisites
- `uv sync --extra dev`; a governed model registered.

## Build the store & score
```bash
uv run creditsentinel-ingest-policy      # builds Chroma from policies/*.md
# then score a decline (via the API or service); reason_code.policy_refs is non-empty
```

## Validate
```bash
uv run pytest tests/test_rag.py tests/test_llm_reason.py -q
```
Expected: pass, including embedding determinism, ingest/retrieve, `test_prompt_has_no_pii`, `test_fallback_used_when_llm_ungrounded`, `test_fallback_used_when_llm_raises`, and `test_score_with_rag_attaches_policy_refs`.

## Enable the LLM
```bash
export ANTHROPIC_API_KEY=sk-...   # then reason_code.generator == "anthropic"
```

## Success signals
- Decline reason cites drivers + policy refs (SC-001); works with no key via template (SC-002); no PII in prompt (SC-003); deterministic rebuild (SC-004).
