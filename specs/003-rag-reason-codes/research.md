# Phase 0 Research — RAG Policy Store + LLM Reason Codes

No NEEDS CLARIFICATION remain.

## Decision: Chroma as the vector store
- **Rationale**: Zero-infra embedded mode for local/tests; a server mode for compose. Simple collection API fits a tiny corpus.
- **Alternatives**: pgvector (needs Postgres), FAISS (no metadata/store abstraction). Kept swappable behind `PolicyRetrieverPort`.

## Decision: Deterministic offline hashing embedder
- **Rationale**: FR-006 requires reproducible, network-free retrieval. A bag-of-words hashing embedder is deterministic and retrieves well on a small lexical corpus.
- **Alternatives**: Downloaded transformer embeddings (network dependency, non-deterministic across versions) — rejected for the demo; swappable later.

## Decision: Anthropic adapter wrapped by a template fallback
- **Rationale**: FR-004 — the endpoint must always return a grounded reason. The wrapper validates the LLM output against the grounding contract and falls back to the template on missing key, error, or ungrounded output.
- **Alternatives**: LLM-only (fails without a key), template-only (loses the LLM value). The wrapper gets both.

## Decision: Prompt carries only driver labels + policy text
- **Rationale**: FR-005 / AD-4 — no PII to the external service. Driver labels and policy passages are sufficient to author an adverse-action reason.
- **Alternatives**: Sending the full applicant record (rejected — PII leak).

## Decision: Section-anchored policy chunking
- **Rationale**: Each `## anchor` becomes a passage whose ref (e.g. `adverse-action#debt-to-income`) is a stable, human-meaningful citation.
- **Alternatives**: Fixed-size chunking (loses the citable anchor semantics).
