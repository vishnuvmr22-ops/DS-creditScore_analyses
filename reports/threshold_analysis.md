# CreditSentinel Expected Loss & Cost-Based Threshold Optimization Report

_Generated 2026-10-09T21:44:38_

> **ECONOMIC ASSUMPTION DISCLAIMER**:
> All calculations in this report are based on assumed financial parameters:
> - **Loss Given Default (LGD)**: `0.65` (Assumes 65% loss on default after collection/recovery)
> - **Net Interest Margin**: `0.08` (Assumes 8% net margin over funding costs)
> - **Exposure at Default (EAD)**: Loan principal amount requested.

---

## 1. Executive Summary & Policy Comparison

| Metric | Baseline Policy (`approve < 0.15`) | Cost-Optimized Policy (`approve < 0.17`) | Impact / Uplift |
| :--- | :---: | :---: | :---: |
| **Decision Threshold** | `0.1500` | **`0.1684`** | `+0.0184` |
| **Portfolio Approval Rate** | `7.10%` | **`9.45%`** | `+2.35%` |
| **Default Rate in Approvals** | `7.04%` | **`5.82%`** | `-1.22%` |
| **Total Expected Loss** | `$161,446.59` | **`$227,886.89`** | **`+$66,440.30`** |
| **Net Portfolio Profit** | `$25,713.41` | **`$64,998.42`** | **`+$39,285.01` (`+152.78%`)** |

---

## 2. Theoretical Framework

1. **Expected Loss Formulation**:
   $$\text{EL} = \text{PD} \times \text{LGD} \times \text{Loan\_Amount}$$

2. **Portfolio P&L Objective Function**:
   $$\max_{T} \Pi(T) = \sum_{i: \text{PD}_i < T, y_i = 0} (\text{Margin} \times L_i) - \sum_{i: \text{PD}_i < T, y_i = 1} (\text{LGD} \times L_i)$$

3. **Marginal Approval Breakeven Condition**:
   At the marginal threshold $T^*$, the expected profit on an applicant is zero:
   $$T^* \times \text{LGD} = (1 - T^*) \times \text{Margin} \implies T^* = \frac{\text{Margin}}{\text{LGD} + \text{Margin}} = \frac{0.08}{0.65 + 0.08} \approx 0.1096$$

---

## 3. Threshold Sample Curve

| Threshold | Approval Rate | Default Rate in Approvals | Total Revenue ($) | Total Default Loss ($) | Net Profit ($) | Expected Loss ($) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `0.01` | 0.0% | 0.00% | $0.00 | $0.00 | **$0.00** | $0.00 |
| `0.12` | 4.0% | 5.00% | $97,799.24 | $69,631.15 | **$28,168.09** | $72,387.90 |
| `0.23` | 17.6% | 10.23% | $391,070.68 | $379,219.63 | **$11,851.04** | $548,290.29 |
| `0.34` | 35.2% | 12.77% | $757,487.80 | $876,041.03 | **$-118,553.23** | $1,534,883.38 |
| `0.45` | 55.5% | 15.87% | $1,129,038.05 | $1,611,065.63 | **$-482,027.58** | $2,988,605.84 |
| `0.55` | 72.3% | 18.81% | $1,419,816.91 | $2,579,906.28 | **$-1,160,089.38** | $4,656,035.31 |
| `0.66` | 86.1% | 21.60% | $1,637,963.45 | $3,513,989.44 | **$-1,876,025.99** | $6,302,571.17 |
| `0.77` | 96.0% | 23.75% | $1,782,707.16 | $4,298,857.87 | **$-2,516,150.71** | $7,700,932.19 |
| `0.88` | 99.5% | 24.52% | $1,835,149.31 | $4,610,959.12 | **$-2,775,809.81** | $8,295,709.95 |
| `0.99` | 100.0% | 24.65% | $1,842,665.84 | $4,658,834.08 | **$-2,816,168.24** | $8,393,485.20 |

---

## 4. Operational & Governance Guidelines

- **Live Scoring Safety**: Live decisioning defaults to band policy (`approve_below=0.15`, `decline_at_or_above=0.45`).
- **Activation**: To activate cost-optimized thresholds in production scoring, set `CS_DECISION_MODE=cost_based`.
- **Grounded Auditing**: Every scoring response includes `expected_loss` field for risk accounting without disrupting core decisioning.
