# Phase 1 Data Model — Real-Time Scoring API

## ScoreRequest
`applicant_id` (string, ≥1 char) + the applicant feature fields (numeric with range bounds; categoricals constrained to fixed vocabularies).
- **Validation**: out-of-range/invalid category/missing field → 422. `features_dict()` excludes the id.

## ScoreResponse
`applicant_id` (pseudonymized), `pd` ∈ [0,1], `decision` ∈ {approve,decline,review}, `thresholds` {approve_below, decline_at_or_above}, `model_version`, `feature_pipeline_version`, `drivers[]`, `reason_code`, `audit_id`.

## Driver
`feature`, `label`, `shap` (signed), `direction` ∈ {increases_risk, decreases_risk}.

## ReasonCode
`text`, `grounded_in[]` (feature names actually cited), `policy_refs[]`, `generator` ∈ {template, anthropic}.
- **Rule**: `assert_grounded` requires the text to reference ≥1 actual driver label and every `grounded_in` entry to be a real driver.

## Audit entry
`audit_id`, `ts`, `applicant_id` (pseudonymized), `pd`, `decision`, `model_version`, `feature_pipeline_version`, `drivers[]`, `reason_generator`.
- **Rule**: raw applicant id never present (SC-004).
