# Contract — Console UI

What each view must render, and what must be true of it. Verified by the Vitest suite (per-view states, scaling maths, formatting) and by `quickstart.md` (end-to-end).

## Shell (present on every view)

| Element | Contract |
|---|---|
| Provenance statement | Synthetic data, not a real lending decision. Visible without scrolling on every view (FR-011, SC-007). |
| Service status | Health, served `model_version`, `feature_pipeline_version`. Healthy and degraded are visually and textually distinct (FR-010). |
| Navigation | Four destinations: Decisioning, Governance, Drift, Audit. Active destination is unambiguous. |
| Appearance switch | Light / dark, light by default, remembered across visits (FR-014a). |

**States**: when `/health` is unreachable the shell shows a disconnected state naming the service address it tried and offering retry; when `status` is degraded it says a governed model must be trained and registered, and the scoring action is disabled (spec Edge Cases).

## Decisioning view

Renders **every** field of the scoring response — nothing dropped (SC-002):

- Probability of default, and the decision as a labelled outcome.
- A threshold meter placing the probability against `approve_below` and `decline_at_or_above` read from `/decision-policy` (FR-002, FR-018).
- Drivers as comparable bars: magnitude relative to the largest driver in the set, risk direction distinguished by more than colour (FR-003, FR-014b).
- The reason text, its `grounded_in` drivers, its `policy_refs` as their source passages, and its authoring generator labelled plainly (FR-002; template-authored is a labelled legitimate state, never presented as model-authored).
- `model_version`, `feature_pipeline_version`, `audit_id`, and the pseudonymized reference (FR-002, FR-005).

**Form**: all twelve attributes, constraints mirroring the service exactly, inline per-field messages, and server 422 detail mapped back onto the offending field (FR-001). Preset profiles populate a profile per outcome (FR-004).

**Invariant**: every driver named in the reason text appears in the rendered driver list (SC-003).

## Governance view

- Discrimination and probability-accuracy metrics as labelled figures, each named in full — not bare acronyms.
- Calibration: predicted versus observed per bin against the perfect-calibration reference, plus the overall calibration error (FR-006).
- Fairness: approval rate per group, parity gap, disparate-impact ratio, with the note that the disparity is deliberately injected into the synthetic data (US2 scenario 3).
- The model card, rendered readable in full (FR-007).
- The version these figures belong to, stated explicitly.

**States**: 404 ⇒ "no governed model registered" with the remedy from the response (FR-013).

## Drift view

- Overall verdict, prominent, plus when the evaluation ran and which scenario it evaluated.
- Per-feature magnitude against the threshold, ordered worst-first, breaching features distinguished by label as well as colour (FR-008, FR-014b).
- Score drift shown when present, omitted without apology when absent.

**States**: 404 ⇒ "no evaluation recorded yet" with the command that produces one (US3 scenario 3).

## Audit view

- Newest-first table: timestamp, pseudonymized reference, probability, decision, both versions, recorded drivers, reason generator (FR-009).
- Filter by outcome; bounded request (FR-009, FR-017).

**States**: `count: 0` ⇒ "no decisions match" (a normal empty result); 404 ⇒ "no decisions recorded yet".

**Invariant**: no raw applicant identifier or attribute value appears anywhere in this view (FR-005, SC-005).

## Cross-cutting

- Every view has three distinct rendered states — loading, failed (naming what failed and offering retry), loaded — plus an empty state where the data source may be absent (FR-013, SC-006).
- Both appearances render every view completely and legibly; body and label text meet standard contrast guidance in each (FR-014a, SC-011).
- Usable from tablet width upward; wide tables and charts scroll within their own region, never the page (FR-014, SC-010).
- The console issues no request other than to the scoring service, and holds applicant values only in transient component state (FR-012).
