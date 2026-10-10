# CreditSentinel Project Notes

## 1. Codebase Architecture & Folder Map

CreditSentinel implements a **Hexagonal (Ports & Adapters)** architecture where the pure credit decisioning logic is kept independent of external I/O frameworks (FastAPI, MLflow, Chroma, Anthropic).

```text
CreditSentinel/
├── src/creditsentinel/
│   ├── api/                     # Driving adapter: FastAPI HTTP interfaces
│   │   ├── app.py               # Application factory, CORS middleware, /health, /score routes
│   │   ├── audit.py             # JsonlAuditSink (append-only) and JsonlAuditReader
│   │   ├── reads.py             # Read-only console projection endpoints (/governance, /drift, /audit)
│   │   ├── redact.py            # HashRedactor (SHA-256 salted pseudonymization)
│   │   ├── schemas.py           # Pydantic v2 data contracts (ScoreRequest, ScoreResponse, etc.)
│   │   └── service.py           # Composition root orchestrating scoring workflow
│   ├── explain/                 # Explainability subsystem
│   │   ├── drivers.py           # ShapDriverExtractor wrapping shap.TreeExplainer
│   │   ├── llm_reason.py        # AnthropicReasonAdapter + LLMWithTemplateFallback
│   │   └── reason.py            # TemplateReasonAdapter & assert_grounded() verification
│   ├── features/                # Feature engineering & schema definitions
│   │   ├── pipeline.py          # Deterministic transform() function (v1.0.0)
│   │   └── schema.py            # NUMERIC_FIELDS, CATEGORICAL_FIELDS, FEATURE_LABELS
│   ├── governance/              # Model validation & registration gate
│   │   ├── fairness.py          # approval_rate_parity() calculating parity gap and disparate impact
│   │   ├── gate.py              # assert_governed() checking required metrics before MLflow registration
│   │   ├── metrics.py           # ks_statistic(), calibration_summary(), core_metrics() (AUC, KS, Brier)
│   │   └── model_card.py        # build_model_card() markdown renderer
│   ├── models/                  # Training & MLflow storage
│   │   ├── registry.py          # MlflowRegistry adapter for loading and registering models
│   │   └── train.py             # Offline training pipeline (creditsentinel-train entrypoint)
│   ├── monitoring/              # Production drift monitoring
│   │   ├── baseline.py          # build_baseline() creating quantile bin statistics
│   │   ├── drift.py             # run_drift() calculating Population Stability Index (PSI)
│   │   └── runs.py              # JsonlDriftRunStore recording drift evaluations
│   ├── rag/                     # Vector store policy retrieval
│   │   ├── embedding.py         # HashingEmbedder (512-dim MD5 bag-of-words)
│   │   ├── ingest.py            # CLI script to parse markdown and load into Chroma
│   │   ├── retriever.py         # PolicyRetrieverPort & NullPolicyRetriever
│   │   └── store.py             # ChromaPolicyRetriever client
│   ├── config.py                # Central Pydantic Settings resolving CS_* environment variables
│   ├── dataset.py               # Synthetic data generator (generate(), write_dataset())
│   └── decision.py              # Pure function decide() mapping PD to approve/review/decline
├── policies/                    # Regulatory policy documentation indexed into ChromaDB
├── tests/                       # 17 test modules with 106 automated pytest cases
└── web/                         # Next.js / React operator console dashboard
```

---

## 2. Request Flow: `POST /score`

When a request arrives at `POST /score`, the execution sequence is as follows:

1. **Validation** (`api/app.py` -> `api/schemas.py`):
   - `app.py:score()` receives incoming JSON and parses it into `ScoreRequest`.
   - Pydantic validates data types, non-null requirements, and numerical constraints.
2. **Feature Transformation** (`features/pipeline.py`):
   - `fp.transform(request.features_dict())` converts raw applicant inputs into a ordered numerical feature DataFrame.
   - Computes engineered ratios: `income_to_loan` and `delinquency_flag`.
   - Performs fixed one-hot encoding on `home_ownership` and `purpose`.
3. **Model Inference** (`models/registry.py`):
   - `LoadedModel.predict_pd(features)` invokes `model.predict_proba()` to compute probability of default ($\text{PD} \in [0, 1]$).
4. **Decision Policy** (`decision.py`):
   - `decide(pd_value, approve_below, decline_at_or_above)` applies configured bands:
     - $\text{PD} < 0.15 \implies \text{"approve"}$
     - $\text{PD} \ge 0.45 \implies \text{"decline"}$
     - $\text{otherwise} \implies \text{"review"}$
5. **SHAP Driver Extraction** (`explain/drivers.py`):
   - `ShapDriverExtractor.top_drivers(features, top_n)` executes `TreeExplainer` on the single applicant row.
   - Ranks features by absolute SHAP values and classifies them as `increases_risk` or `decreases_risk`.
6. **Policy Retrieval** (`rag/store.py`):
   - Constructs a query string based on the decision and top risk drivers.
   - `ChromaPolicyRetriever.retrieve()` queries ChromaDB for relevant policy clauses. Falls back to `NullPolicyRetriever` if unbuilt.
7. **Reason Code Generation** (`explain/llm_reason.py` or `explain/reason.py`):
   - If `ANTHROPIC_API_KEY` is set, `AnthropicReasonAdapter` creates a prompt with driver labels and policy passages.
   - Otherwise, `TemplateReasonAdapter` formats the top driver labels into regulatory reason text.
8. **Grounding Assertion** (`explain/reason.py`):
   - `assert_grounded(reason, drivers)` guarantees the generated reason cites at least one true top driver and no extraneous features.
9. **Pseudonymization** (`api/redact.py`):
   - `HashRedactor.pseudonymize(applicant_id)` generates a salted SHA-256 hash prefix (`pseudo_<12-chars>`).
10. **Audit Logging** (`api/audit.py`):
    - `JsonlAuditSink.append()` records the pseudonymized ID, PD, decision, model version, driver attributes, and timestamp to `data/audit_log.jsonl`.
11. **Response Delivery** (`api/schemas.py`):
    - Returns structured `ScoreResponse` containing PD, decision, drivers, grounded reason code, and audit UUID.
