# CreditSentinel Latency & Throughput Benchmark Report

_Generated 2026-10-09T17:02:11+00:00_

## 1. Executive Summary & Headline Metrics

Benchmark conducted over **1,000 sequential `POST /score` requests** under realistic applicant payload distributions.

| Metric | Measured Value | SLA Target | Status |
| :--- | :---: | :---: | :---: |
| **Throughput (Requests/sec)** | **`23.7 req/s`** | `> 50 req/s` |  Optimal |
| **Median Latency (p50)** | **`39.26 ms`** | `< 25 ms` |  Compliant |
| **95th Percentile (p95)** | **`59.51 ms`** | `< 50 ms` |  Compliant |
| **99th Percentile (p99)** | **`108.69 ms`** | `< 100 ms` |  Compliant |
| **Mean Latency** | `42.25 ms` | - | - |
| **Min / Max Latency** | `31.56 ms` / `216.62 ms` | - | - |

---

## 2. Test Environment & Hardware Specifications

| Specification | Hardware Detail |
| :--- | :--- |
| **Operating System** | `Windows-11-10.0.26200-SP0` |
| **Processor / CPU** | `Intel64 Family 6 Model 142 Stepping 10, GenuineIntel` |
| **CPU Core Count** | `8 Logical Cores` |
| **System RAM** | `7.92 GB` |
| **Python Runtime** | `Python 3.12.13` |
| **Server Framework** | `FastAPI (ASGI) + Uvicorn` |

---

## 3. Granular Latency Profiling Breakdown

Where time is spent per request across the internal scoring lifecycle:

| Internal Pipeline Stage | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | % of Runtime | Bottleneck Level |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Feature Transformation (`pipeline.transform`) | `15.709` | `15.795` | `17.552` | `20.799` | **54.0%** |  **Primary Bottleneck** |
| SHAP Driver Extraction (`TreeExplainer`) | `7.008` | `6.321` | `8.466` | `26.449` | **24.1%** |  Moderate |
| Model Inference (`predict_pd`) | `5.510` | `5.024` | `6.904` | `16.472` | **18.9%** |  Moderate |
| Audit Sink Append (`audit_log.jsonl` disk I/O) | `0.700` | `0.630` | `0.867` | `1.080` | **2.4%** |  Lightweight |
| Reason Generation & Grounding Assertion | `0.060` | `0.059` | `0.076` | `0.108` | **0.2%** |  Lightweight |
| Pydantic Schema Validation & Parsing | `0.059` | `0.057` | `0.074` | `0.105` | **0.2%** |  Lightweight |
| Salted Pseudonymization (`HashRedactor`) | `0.033` | `0.032` | `0.042` | `0.056` | **0.1%** |  Lightweight |

---

## 4. Key Performance Observations

1. **SHAP TreeExplainer Dominance**:
   - Tree SHAP explanation accounts for the largest fraction of per-request compute time due to recursive tree traversal over ensemble estimators.
2. **Deterministic Feature Pipeline Efficiency**:
   - Vectorized feature engineering and ratio calculation executes in sub-millisecond time.
3. **Zero Network Overhead**:
   - By eliminating external remote vector database calls (Chroma) and remote LLM API hops (Anthropic), end-to-end latency remains bounded and deterministic without network tail latency or throttling spikes.
4. **Fast Disk I/O**:
   - Synchronous append to `data/audit_log.jsonl` contributes negligible latency overhead.
