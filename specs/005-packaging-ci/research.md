# Phase 0 Research — Packaging, CI & Documentation

No NEEDS CLARIFICATION remain. Findings reflect issues actually encountered and resolved during the live bring-up.

## Decision: One shared image for all three services
- **Rationale**: Guarantees the mlflow and chromadb versions match between client (API) and servers, avoiding client/server protocol mismatches.
- **Alternatives**: Official `mlflow`/`chromadb` images (version-skew risk vs. the pinned client).

## Decision: Self-sufficient API entrypoint (train + ingest on first boot)
- **Rationale**: FR-001/FR-002 "no manual steps". The entrypoint waits for MLflow, trains + registers if no model exists, rebuilds the policy store, then serves.
- **Alternatives**: A separate one-shot init job (more moving parts); requiring the user to run training (violates no-manual-steps).

## Decision: MLflow SQLite backend + server `--allowed-hosts "*"`
- **Rationale**: MLflow 3.x removed the file store; SQLite is the supported zero-infra backend. The server's DNS-rebinding protection rejects the `mlflow:5000` Host header, so allow-hosts is required on the private compose network.
- **Alternatives**: Postgres backend (extra service); disabling the server (loses the registry API + UI).

## Decision: Chroma runs via `chroma run` from the same image; numpy embeddings
- **Rationale**: Same-image server matches the client. The HTTP client path requires numpy-array embeddings (calls `.tolist()`), so the embedder returns numpy arrays.
- **Alternatives**: Official chroma image (version skew); embedded-only Chroma (doesn't present a distinct "vector store" service).

## Decision: CI = ruff + pytest with `--cov-fail-under=80`
- **Rationale**: Enforces the constitution's lint + ≥80% core-coverage gate on every push.
- **Alternatives**: Tests without a coverage floor (weaker guarantee).

## Decision: API host port 8080 (container 8000)
- **Rationale**: Avoids a common local 8000 conflict observed during bring-up.
- **Alternatives**: 8000:8000 (conflicted locally).
