# Contract — Console Read-Only API

Four new endpoints on the existing scoring service. **All are `GET`. The slice adds no write verb** (FR-022): the only non-idempotent endpoint on the service remains `POST /score`.

## Cross-cutting

**CORS**: `CORSMiddleware` with `allow_origins` from `CS_CORS_ALLOW_ORIGINS` (comma-separated, default `http://localhost:3000`), `allow_methods=["GET","POST"]`, `allow_credentials=False`. A request from an unlisted origin gets no CORS headers and is blocked by the browser.

**"Not yet produced" — 404** (FR-020), distinguishable from a transport failure and from a 5xx:

```json
{"detail": {"status": "not_produced", "artifact": "drift_run", "remedy": "run `uv run creditsentinel-drift --scenario stable`"}}
```

**PII**: no response field carries a raw applicant identifier or a raw applicant attribute value (FR-019).

---

## GET /decision-policy

The active policy configuration, so the console never hard-codes thresholds (FR-018).

```json
{"approve_below": 0.15, "decline_at_or_above": 0.45, "top_n_drivers": 3, "psi_cutoff": 0.2}
```

**200 always** — configuration is always resolvable. `approve_below < decline_at_or_above` holds.

---

## GET /governance

Governance for the model version **being served** (not merely the newest in the registry).

```json
{
  "model_version": "1",
  "feature_pipeline_version": "1.0.0",
  "metrics": {
    "auc_roc": 0.683, "ks": 0.284, "brier": 0.173,
    "calibration": {
      "expected_calibration_error": 0.114,
      "bins": [{"bin": 0, "n": 317, "mean_pred": 0.0697, "observed": 0.0883}]
    }
  },
  "fairness": {
    "approval_rate_by_group": {"A": 0.879, "B": 0.897},
    "parity_gap": 0.0179,
    "disparate_impact_ratio": 0.98
  }
}
```

**404** `not_produced` / `artifact: "governance"` when no governed model is registered — remedy `run \`uv run creditsentinel-train\``.

**Invariants**: `model_version` equals the version reported by `/health` and echoed by `/score`. Values are served verbatim from the artifacts logged at registration — never recomputed (Constitution III).

---

## GET /governance/model-card

```json
{"model_version": "1", "content": "# Model Card — creditsentinel-pd\n..."}
```

**404** as above. Content is the generated card verbatim, Markdown.

---

## GET /drift

The most recently **recorded** evaluation. This endpoint never computes drift (FR-016a).

```json
{
  "run_id": "b1e…", "ts": "2026-07-21T10:12:03+00:00", "scenario": "stable",
  "cutoff": 0.2,
  "features": {"debt_to_income": {"psi": 0.013, "breach": false}},
  "score": {"psi": 0.021, "breach": false},
  "breached_features": [],
  "any_breach": false
}
```

`score` is absent when no model was loadable when the job ran.

**404** `not_produced` / `artifact: "drift_run"` when no evaluation has ever been recorded — remedy names the drift command.

**Invariants**: `any_breach == (breached_features non-empty OR score.breach)`. `breached_features` lists exactly the features whose `psi >= cutoff`. Two consecutive reads with no intervening job run return the identical record.

---

## GET /audit

Recent decisions, newest-first.

**Query**: `limit` (int, default 50, 1 ≤ limit ≤ 200 — out of range ⇒ **422**), `decision` (optional, one of `approve` \| `review` \| `decline` — anything else ⇒ **422**).

```json
{
  "count": 2,
  "entries": [{
    "audit_id": "d62b…", "ts": "2026-07-18T02:05:27+00:00",
    "applicant_id": "pseudo_e6cae956dbeb",
    "pd": 0.762275, "decision": "decline",
    "model_version": "1", "feature_pipeline_version": "1.0.0",
    "drivers": [{"feature": "debt_to_income", "label": "debt-to-income ratio", "shap": 1.190659, "direction": "increases_risk"}],
    "reason_generator": "template"
  }]
}
```

**200 with `count: 0`** when the log exists but nothing matches — an empty result is not a missing artifact.
**404** `not_produced` / `artifact: "audit_log"` only when no log file exists at all — remedy: score an applicant.

**Invariants**: `entries` is ordered by `ts` descending; `len(entries) == count <= limit`; every `applicant_id` matches `pseudo_*`; when `decision` is given, every entry matches it, and filtering is applied **before** truncation. Malformed lines are skipped, not fatal.

---

## Unchanged

`GET /health` and `POST /score` keep their slice-002 contracts exactly. The console consumes both as they are.
