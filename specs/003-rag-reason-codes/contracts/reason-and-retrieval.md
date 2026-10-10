# Contract — Retrieval + Reason Generation

## PolicyRetrieverPort.retrieve(query, k) -> list[PolicyPassage]
- Returns up to `k` most relevant passages (ref + text). Empty list if the store is unbuilt (graceful).

## ReasonCodePort.generate(decision, drivers, policy) -> ReasonCode
- Returns `{text, grounded_in[], policy_refs[], generator}`.
- **Invariant**: `text` references ≥1 actual driver label; `grounded_in ⊆ driver features`; `policy_refs` = refs of passages used.

## Adapter selection (service.from_settings)
- Retriever: `ChromaPolicyRetriever.try_load(settings)` if store built, else `NullPolicyRetriever`.
- Reason: `LLMWithTemplateFallback(AnthropicReasonAdapter, TemplateReasonAdapter)` if `anthropic_api_key` set, else `TemplateReasonAdapter`.

## CLI: creditsentinel-ingest-policy
- (Re)builds the Chroma collection from `policies/*.md`; prints the passage count.

## LLM prompt contract (FR-005)
- Contains: decision, cited driver labels + risk direction, retrieved policy excerpts.
- Excludes: applicant id, raw feature values.
