# Phase 0 Research — Real-Time Scoring API

No NEEDS CLARIFICATION remain.

## Decision: FastAPI + Pydantic v2
- **Rationale**: Async-capable, first-class validation (422 on bad input) and OpenAPI docs for free; matches the project stack.
- **Alternatives**: Flask (weaker validation story), gRPC (overkill for a demo origination endpoint).

## Decision: SHAP TreeExplainer for driver attribution
- **Rationale**: Exact, fast per-prediction attributions for tree models; positive SHAP → higher default log-odds = increases risk, which maps directly to adverse-action factors.
- **Alternatives**: Permutation importance (global, not per-decision), LIME (approximate, less stable).

## Decision: Grounding enforced in the core (`assert_grounded`)
- **Rationale**: Constitution IV — the reason must reference actual top drivers regardless of which adapter produced it. Enforcing in the core makes the invariant adapter-agnostic and testable.
- **Alternatives**: Trusting the generator (rejected: cannot guarantee faithfulness).

## Decision: Pseudonymize id via salted one-way hash before audit
- **Rationale**: Constitution V — no raw PII in logs; deterministic pseudonym allows correlation without exposing the id.
- **Alternatives**: Storing raw id (rejected), dropping id entirely (loses auditability).

## Decision: Reason/policy behind ports with a Null/template default
- **Rationale**: Lets this feature ship and be tested standalone while the RAG + LLM feature layers on top without touching the decision path.
- **Alternatives**: Building RAG+LLM into this feature (rejected: violates the slice boundary).
