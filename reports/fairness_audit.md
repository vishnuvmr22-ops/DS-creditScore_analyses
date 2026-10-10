# CreditSentinel Multidimensional Fairness & Bias Audit Report

_Generated 2026-10-09T21:38:31_

## 1. Executive Summary & Audit Scope

Audited using **Fairlearn `MetricFrame`** across 3 distinct demographic dimensions:
- **Gender**: Female (`F`) vs. Male (`M`)
- **Age Band**: `<25`, `25-34`, `35-49`, `50-64`, `65+`
- **Region Rating**: Client regional rating tier (`1`, `2`, `3`)

### Key Audit Findings
- **Largest Selection (Approval) Rate Gap**: `0.3068`
- **Largest False Positive Rate (FPR) Gap**: `0.2876` (creditworthy applicants declined)
- **Largest False Negative Rate (FNR) Gap**: `0.2810` (defaulting applicants approved)

---

## 2. Granular Demographic Metric Breakdown

### Dimension: `gender`
- **Selection Rate Gap**: `0.0242`
- **FPR Gap**: `0.0418` | **FNR Gap**: `0.0270`

| Subgroup | Approval (Selection) Rate | False Positive Rate (FPR) | False Negative Rate (FNR) |
| :--- | :---: | :---: | :---: |
| **F** | 0.5532 | 0.3878 | 0.3720 |
| **M** | 0.5774 | 0.3460 | 0.3450 |

### Dimension: `age_group`
- **Selection Rate Gap**: `0.3068`
- **FPR Gap**: `0.2876` | **FNR Gap**: `0.2810`

| Subgroup | Approval (Selection) Rate | False Positive Rate (FPR) | False Negative Rate (FNR) |
| :--- | :---: | :---: | :---: |
| **25-34** | 0.5126 | 0.3924 | 0.2605 |
| **35-49** | 0.5298 | 0.4196 | 0.3465 |
| **50-64** | 0.6313 | 0.3112 | 0.4490 |
| **65+** | 0.7020 | 0.2434 | 0.5217 |
| **<25** | 0.3952 | 0.5310 | 0.2407 |

### Dimension: `region_rating`
- **Selection Rate Gap**: `0.0000`
- **FPR Gap**: `0.0000` | **FNR Gap**: `0.0000`

| Subgroup | Approval (Selection) Rate | False Positive Rate (FPR) | False Negative Rate (FNR) |
| :--- | :---: | :---: | :---: |
| **2** | 0.5630 | 0.3709 | 0.3611 |

---

## 3. Offline Fairness Mitigation Experiment

> **GOVERNANCE NOTICE**: This experiment evaluates post-processing threshold optimization to equalize approval rates.
> This is strictly an **offline simulation report** and does **NOT** alter online production scoring logic.

- **Unmitigated Uniform Threshold**: `0.4500`
- **Optimized Per-Group Thresholds**: `{"F": 0.4554, "M": 0.4398}`
- **Disparity Gap Before**: `0.0242`
- **Disparity Gap After**: `0.0007`
- **Disparity Reduction**: `+97.1%`

### Before vs. After Mitigation Comparison
| Subgroup | Unmitigated Approval Rate | Mitigated Approval Rate | Unmitigated FPR | Mitigated FPR |
| :--- | :---: | :---: | :---: | :---: |
| **F** | 0.5532 | 0.5633 | 0.3878 | 0.3778 |
| **M** | 0.5774 | 0.5626 | 0.3460 | 0.3608 |

---

## 4. Remaining Disparities & Ethical Assessment

- **Trade-offs**: Equalizing demographic selection rates via threshold optimization creates slight shifts in per-group False Positive Rates.
- **Compliance**: In many jurisdictions (e.g., US ECOA / Regulation B), utilizing protected class status at decision time to apply disparate thresholds requires rigorous fair lending legal validation.
- **Recommendation**: Maintain a single uniform score threshold for live scoring, while monitoring demographic metric slices continuously in the governance registry.
