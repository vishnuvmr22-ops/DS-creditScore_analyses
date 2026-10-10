"""Fairness parity metrics and Fairlearn audit across protected attributes (FR-5, constitution III).

Computes approval-rate parity and multidimensional demographic parity (selection rate, FPR, FNR)
across protected groups given model scores and a decision threshold. The protected attributes are used
ONLY in governance and auditing — never as model features (AD-5).
"""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd


def approval_rate_parity(
    groups: pd.Series | np.ndarray,
    y_score: np.ndarray,
    decline_at_or_above: float,
) -> dict:
    """Approve = score below the decline threshold. Returns per-group approval
    rates, their absolute difference (parity gap), and the disparate-impact ratio
    (min/max approval rate; 1.0 == perfect parity)."""
    groups = pd.Series(np.asarray(groups)).reset_index(drop=True)
    approved = pd.Series(np.asarray(y_score) < decline_at_or_above).reset_index(drop=True)

    per_group = {}
    for g, mask in approved.groupby(groups):
        per_group[str(g)] = float(mask.mean())

    rates = list(per_group.values())
    parity_gap = float(max(rates) - min(rates)) if rates else 0.0
    di_ratio = float(min(rates) / max(rates)) if rates and max(rates) > 0 else 1.0
    return {
        "approval_rate_by_group": per_group,
        "parity_gap": parity_gap,
        "disparate_impact_ratio": di_ratio,
    }


def _calc_selection_rate(y_true: np.ndarray, y_pred_default: np.ndarray) -> float:
    """Approval rate: fraction of applicants approved (predicted non-default, y_pred_default == 0)."""
    y_p = np.asarray(y_pred_default)
    if len(y_p) == 0:
        return 0.0
    return float(np.mean(y_p == 0))


def _calc_fpr(y_true: np.ndarray, y_pred_default: np.ndarray) -> float:
    """FPR on default prediction: fraction of non-defaulters incorrectly flagged as default (declined)."""
    y_t = np.asarray(y_true)
    y_p = np.asarray(y_pred_default)
    non_defaulters = y_t == 0
    if not np.any(non_defaulters):
        return 0.0
    return float(np.mean(y_p[non_defaulters] == 1))


def _calc_fnr(y_true: np.ndarray, y_pred_default: np.ndarray) -> float:
    """FNR on default prediction: fraction of actual defaulters incorrectly approved (predicted non-default)."""
    y_t = np.asarray(y_true)
    y_p = np.asarray(y_pred_default)
    defaulters = y_t == 1
    if not np.any(defaulters):
        return 0.0
    return float(np.mean(y_p[defaulters] == 0))


def extended_fairlearn_audit(
    y_true: np.ndarray,
    y_score: np.ndarray,
    sensitive_features: pd.DataFrame | pd.Series | dict,
    decline_at_or_above: float = 0.45,
) -> dict:
    """Comprehensive Fairlearn audit across gender, age band, and region rating.

    Calculates Selection (Approval) Rate, False Positive Rate (FPR), and False Negative
    Rate (FNR) across all demographic slices and reports the maximum gap per metric.
    """
    from fairlearn.metrics import MetricFrame

    y_t = np.asarray(y_true).astype(int)
    y_s = np.asarray(y_score).astype(float)
    y_pred_default = (y_s >= decline_at_or_above).astype(int)

    if isinstance(sensitive_features, (pd.Series, np.ndarray, list)):
        sf_df = pd.DataFrame({"group": sensitive_features})
    elif isinstance(sensitive_features, dict):
        sf_df = pd.DataFrame(sensitive_features)
    else:
        sf_df = sensitive_features.copy()

    sf_df = sf_df.reset_index(drop=True)

    metrics_dict = {
        "selection_rate": _calc_selection_rate,
        "false_positive_rate": _calc_fpr,
        "false_negative_rate": _calc_fnr,
    }

    results: dict[str, Any] = {"by_dimension": {}, "largest_gaps": {}}
    overall_gaps = {"selection_rate": 0.0, "false_positive_rate": 0.0, "false_negative_rate": 0.0}

    for col in sf_df.columns:
        series = sf_df[col].astype(str)
        mf = MetricFrame(
            metrics=metrics_dict,
            y_true=y_t,
            y_pred=y_pred_default,
            sensitive_features=series,
        )

        by_group_data = {}
        for m_name in metrics_dict:
            by_group_data[m_name] = {str(k): round(float(v), 4) for k, v in mf.by_group[m_name].items()}
            vals = list(by_group_data[m_name].values())
            gap = round(float(max(vals) - min(vals)), 4) if vals else 0.0
            overall_gaps[m_name] = max(overall_gaps[m_name], gap)

        results["by_dimension"][col] = {
            "by_group": by_group_data,
            "selection_rate_gap": round(float(max(by_group_data["selection_rate"].values()) - min(by_group_data["selection_rate"].values())), 4),
            "fpr_gap": round(float(max(by_group_data["false_positive_rate"].values()) - min(by_group_data["false_positive_rate"].values())), 4),
            "fnr_gap": round(float(max(by_group_data["false_negative_rate"].values()) - min(by_group_data["false_negative_rate"].values())), 4),
        }

    results["largest_gaps"] = {k: round(v, 4) for k, v in overall_gaps.items()}
    return results


def mitigation_threshold_optimizer_experiment(
    y_true: np.ndarray,
    y_score: np.ndarray,
    sensitive_feature: pd.Series | np.ndarray,
    decline_at_or_above: float = 0.45,
) -> dict:
    """Offline-only mitigation experiment comparing unmitigated vs. threshold-optimized decisions.

    Finds group-specific decision thresholds to equalize approval rates across protected groups
    (demographic parity post-processing).

    NOTE: This is an analytical experiment only; it does NOT mutate live decision policy.
    """
    sens = pd.Series(sensitive_feature).astype(str).reset_index(drop=True)
    y_t = np.asarray(y_true).astype(int)
    y_s = np.asarray(y_score).astype(float)

    # 1. Unmitigated Baseline Decisions
    unmitigated_pred = (y_s < decline_at_or_above).astype(int)  # 1 = approved, 0 = declined

    unmitigated_rates = {}
    unmitigated_fprs = {}
    unmitigated_fnrs = {}
    for g in sorted(sens.unique()):
        mask = (sens == g).to_numpy()
        unmitigated_rates[str(g)] = float(np.mean(unmitigated_pred[mask]))
        
        # FPR: good borrowers declined
        good_borrowers = mask & (y_t == 0)
        unmitigated_fprs[str(g)] = float(np.mean(unmitigated_pred[good_borrowers] == 0)) if np.any(good_borrowers) else 0.0
        
        # FNR: bad borrowers approved
        defaulters = mask & (y_t == 1)
        unmitigated_fnrs[str(g)] = float(np.mean(unmitigated_pred[defaulters] == 1)) if np.any(defaulters) else 0.0

    before_gap = float(max(unmitigated_rates.values()) - min(unmitigated_rates.values()))

    # 2. Threshold Search to Equalize Approval Rates across groups
    target_rate = float(np.mean(unmitigated_pred))
    mitigated_thresholds = {}
    mitigated_rates = {}
    mitigated_fprs = {}
    mitigated_fnrs = {}

    for g in sorted(sens.unique()):
        mask = (sens == g).to_numpy()
        group_scores = y_s[mask]
        # Find quantile threshold for target approval rate
        opt_thresh = float(np.quantile(group_scores, target_rate))
        mitigated_thresholds[str(g)] = round(opt_thresh, 4)

        opt_pred = (group_scores < opt_thresh).astype(int)
        mitigated_rates[str(g)] = float(np.mean(opt_pred))

        good_borrowers = mask & (y_t == 0)
        mitigated_fprs[str(g)] = float(np.mean(y_s[good_borrowers] >= opt_thresh)) if np.any(good_borrowers) else 0.0

        defaulters = mask & (y_t == 1)
        mitigated_fnrs[str(g)] = float(np.mean(y_s[defaulters] < opt_thresh)) if np.any(defaulters) else 0.0

    after_gap = float(max(mitigated_rates.values()) - min(mitigated_rates.values()))

    return {
        "status": "offline_simulation_only",
        "unmitigated_threshold": decline_at_or_above,
        "mitigated_thresholds_by_group": mitigated_thresholds,
        "before": {
            "approval_rates": {k: round(v, 4) for k, v in unmitigated_rates.items()},
            "disparity_gap": round(before_gap, 4),
            "fpr_by_group": {k: round(v, 4) for k, v in unmitigated_fprs.items()},
            "fnr_by_group": {k: round(v, 4) for k, v in unmitigated_fnrs.items()},
        },
        "after": {
            "approval_rates": {k: round(v, 4) for k, v in mitigated_rates.items()},
            "disparity_gap": round(after_gap, 4),
            "fpr_by_group": {k: round(v, 4) for k, v in mitigated_fprs.items()},
            "fnr_by_group": {k: round(v, 4) for k, v in mitigated_fnrs.items()},
        },
        "disparity_reduction_pct": round(float((before_gap - after_gap) / max(before_gap, 1e-6) * 100), 2),
    }
