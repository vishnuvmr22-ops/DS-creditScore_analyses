# CreditSentinel Model Evaluation & Benchmark Report

_Generated 2026-10-09T21:38:31_

## 1. Candidate Model Benchmark

| Model Architecture | AUC-ROC | KS Statistic | Brier Score | PR-AUC | ECE |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bureau-Only Baseline** | 0.6724 | 0.2689 | 0.1730 | 0.3943 | 0.1483 |
| **Logistic Regression** | 0.7053 | 0.3127 | 0.2210 | 0.4445 | 0.1963 |
| **LightGBM** | 0.6707 | 0.2660 | 0.2149 | 0.3932 | 0.2163 |
| **XGBoost (Primary)** | **0.6734** | **0.2740** | **0.2126** | **0.3822** | **0.2286** |

---

## 2. Bureau-Only Uplift Analysis

- **Baseline Model AUC**: `0.6724`
- **Full Model AUC**: `0.6734`
- **Delta AUC Uplift**: `+0.0011`
- **Delta KS Uplift**: `+0.0051`

---

## 3. Probability Calibration (Isotonic)

- **Uncalibrated Brier Score**: `0.2126`
- **Calibrated Brier Score**: `0.1729`
- **Uncalibrated ECE**: `0.2286`
- **Calibrated ECE**: `0.0447`

---

## 4. Governed Model Fairness Gate

- **Approval Rate (Group A)**: `0.5532`
- **Approval Rate (Group B)**: `0.5774`
- **Parity Gap**: `0.0242`
- **Disparate Impact Ratio**: `0.9581`
