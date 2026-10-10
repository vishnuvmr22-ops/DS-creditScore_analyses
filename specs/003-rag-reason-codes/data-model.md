# Phase 1 Data Model — RAG Policy Store + LLM Reason Codes

## Policy passage
`ref` (stable anchor id, e.g. `adverse-action#debt-to-income`), `text` (section body), `source` (doc filename).
- **Derivation**: policy markdown split by `## anchor` headers; each non-empty section → one passage.

## Policy store (Chroma collection)
Passages embedded with the deterministic `HashingEmbedder`; queried by a decision/driver-derived query string.
- **Rule (FR-006)**: rebuild from the same docs ⇒ identical retrievable passages.

## Reason code (extends feature 002)
`text`, `grounded_in[]`, `policy_refs[]` (from retrieved passages), `generator` ∈ {template, anthropic}.
- **Rule (FR-003/FR-004)**: references actual drivers + policy refs; on ungrounded LLM output or error → template.

## LLM prompt (transient, not persisted)
System instruction + user content = decision + cited driver labels/directions + policy excerpts.
- **Rule (FR-005)**: contains no applicant id and no raw feature values.
