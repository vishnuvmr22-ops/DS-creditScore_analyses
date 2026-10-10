# Data Model — Web Operator Console

No database. Every entity below is either read from an existing store (MLflow, the audit log) or appended to a new append-only file. **The console owns no persistent state**, and this slice adds no field that carries a raw applicant identifier or a raw applicant attribute value (FR-019).

---

## 1. GovernanceRecord (read-only projection)

Resolved for the model version **currently being served**, from the MLflow run that registered it.

| Field | Type | Source | Notes |
|---|---|---|---|
| `model_version` | str | registry | The served version — not "latest in registry", the one loaded by the scoring service |
| `feature_pipeline_version` | str | model version tag | Echoed so governance and decisions can be tied together (Constitution II) |
| `metrics.auc_roc` | float | `metrics.json` | Discrimination |
| `metrics.ks` | float | `metrics.json` | Discrimination |
| `metrics.brier` | float | `metrics.json` | Accuracy of probability |
| `metrics.calibration.expected_calibration_error` | float | `metrics.json` | |
| `metrics.calibration.bins[]` | list | `metrics.json` | `{bin:int, n:int, mean_pred:float, observed:float}`, ascending by `bin` |
| `fairness.approval_rate_by_group` | map[str,float] | `fairness.json` | Synthetic protected attribute; group labels only, never a person |
| `fairness.parity_gap` | float | `fairness.json` | |
| `fairness.disparate_impact_ratio` | float | `fairness.json` | |

**Rules**
- Read-only. Nothing in this slice writes governance data; it is produced solely by the governed registration path (Constitution III).
- All three artifacts (`metrics.json`, `fairness.json`, `model_card.md`) exist for any registered version — the governance gate refuses registration otherwise — so a *registered but ungoverned* state is unreachable by construction. A missing artifact therefore means the registry itself is unreachable or empty, which surfaces as "not produced".
- `bins` may be shorter than the nominal bin count when high-probability bins are empty; consumers must not assume a fixed length.
- `n` per bin is a count of synthetic records, never of people.

## 2. ModelCard (read-only)

| Field | Type | Notes |
|---|---|---|
| `model_version` | str | The served version |
| `content` | str | The full generated model card, Markdown, verbatim |

**Rules**: served as text; the console renders it without editing or summarising it.

---

## 3. DriftRun (new durable record)

One JSON object per line in `data/drift_runs.jsonl`, appended by the drift job.

| Field | Type | Notes |
|---|---|---|
| `run_id` | str (uuid4) | Identifies the evaluation |
| `ts` | str (ISO-8601, UTC) | When the evaluation ran |
| `scenario` | str | `stable` \| `drift` — which batch was evaluated; recorded so a reviewer knows whether drift was deliberately injected |
| `cutoff` | float | The PSI alert threshold in force for that run |
| `features` | map[str, {psi: float, breach: bool}] | Per monitored feature |
| `score` | {psi: float, breach: bool} \| absent | Present only when a model was loadable at run time |
| `breached_features` | list[str] | Features at or above `cutoff` |
| `any_breach` | bool | Overall verdict |

**Rules**
- **Append-only.** Records are never updated or deleted; history is the point of a monitoring artifact.
- "Latest" is the last line in the file. Records are written in run order.
- Carries no applicant-level data — only distributional statistics over a synthetic monitoring batch.
- The shape from `cutoff` down is exactly the report `run_drift()` already returns; this slice wraps it with identity and provenance fields rather than changing it, so slice 004's printed output and exit-code contract are untouched.

**Lifecycle**: `drift job runs` → report computed → record appended → printed and exit code set (unchanged) → served by the read endpoint as "latest" until a newer run appends.

---

## 4. AuditEntry (read-only projection of an existing record)

Existing records in `data/audit_log.jsonl`, written by the scoring path only.

| Field | Type | Notes |
|---|---|---|
| `audit_id` | str (uuid4) | |
| `ts` | str (ISO-8601, UTC) | |
| `applicant_id` | str | **Pseudonymized** (`pseudo_…`) — the raw identifier is never written and therefore cannot be read |
| `pd` | float | |
| `decision` | str | `approve` \| `review` \| `decline` |
| `model_version` | str | |
| `feature_pipeline_version` | str | |
| `drivers[]` | list | `{feature, label, shap, direction}` as recorded at decision time |
| `reason_generator` | str | Which adapter authored the reason |

**Rules**
- Read-only; the reader never writes, rotates or truncates the log.
- Returned newest-first, bounded by `limit` (default 50, maximum 200).
- Filtering by decision is applied **before** truncation, so "the 50 most recent declines" means what it says.
- Malformed lines are skipped rather than failing the whole read — a partially written last line must not take the view down.
- Applicant attribute values were never recorded, so no redaction step is required on read; the guarantee comes from what the writer omits, not from filtering on the way out.

---

## 5. DecisionPolicy (read-only projection of configuration)

| Field | Type | Notes |
|---|---|---|
| `approve_below` | float | PD strictly below ⇒ approve |
| `decline_at_or_above` | float | PD at or above ⇒ decline; between the two ⇒ review |
| `top_n_drivers` | int | How many drivers the service returns |
| `psi_cutoff` | float | Drift alert threshold, so the drift view does not hard-code it |

**Rules**: read-only. Exposing these lets the console render the threshold meter and the drift threshold line from the service's actual configuration (FR-018) instead of duplicating constants.

---

## 6. ServiceStatus (existing `/health`, unchanged)

`status`, `model_loaded`, `model_version`, `feature_pipeline_version`. Consumed by the console shell to show health continuously (FR-010) and to disable scoring when degraded.

---

## 7. ApplicantDraft (console-only, transient)

The twelve applicant attributes plus an identifier, held in component state only for the duration of composing one scoring request.

**Rules**
- Never written to storage of any kind and never sent anywhere but `POST /score` (FR-012).
- Discarded on reload. The only thing the console persists between visits is the appearance preference.
- Field constraints mirror the service contract exactly and live in one shared specification table (research R4):

| Field | Type | Constraint |
|---|---|---|
| `applicant_id` | str | non-empty |
| `age` | float | 18 … 120 |
| `annual_income` | float | ≥ 0 |
| `employment_length` | float | 0 … 60 |
| `debt_to_income` | float | 0 … 2 |
| `credit_utilization` | float | 0 … 3 |
| `num_delinquencies` | float | ≥ 0 |
| `num_open_accounts` | float | ≥ 0 |
| `loan_amount` | float | > 0 |
| `interest_rate` | float | 0 … 100 |
| `home_ownership` | enum | `RENT` \| `OWN` \| `MORTGAGE` |
| `purpose` | enum | `debt_consolidation` \| `credit_card` \| `home_improvement` \| `major_purchase` \| `other` |

---

## 8. AppearancePreference (console-only, persisted locally)

| Field | Type | Notes |
|---|---|---|
| `theme` | `light` \| `dark` \| `system` | The viewer's choice; light is the default when unset |

**Rules**: the only value the console persists (FR-014a). Contains nothing about applicants, decisions or the service.

---

## Relationships

```text
DecisionPolicy ──shapes──► decision boundaries shown on ScoreResult and DriftRun
ServiceStatus  ──pins────► model_version ──identifies──► GovernanceRecord + ModelCard
ApplicantDraft ──POST────► ScoreResult ──writes──► AuditEntry (pseudonymized)
DriftRun       ──compares current population against──► training baseline
```

Every arrow crossing into persistence is one-way and already exists, except the drift job's new append. The console appears in none of them as a writer.
