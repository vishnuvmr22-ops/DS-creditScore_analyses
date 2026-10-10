"""Core discrimination + calibration metrics (FR-4, constitution III)."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, precision_recall_curve, roc_auc_score


def ks_statistic(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Kolmogorov-Smirnov separation between default/non-default score CDFs."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    order = np.argsort(y_score)
    y_sorted = y_true[order]
    pos = np.cumsum(y_sorted) / max(y_sorted.sum(), 1)
    neg = np.cumsum(1 - y_sorted) / max((1 - y_sorted).sum(), 1)
    return float(np.max(np.abs(pos - neg)))


def recall_at_min_precision(
    y_true: np.ndarray, y_score: np.ndarray, min_precision: float = 0.50
) -> float:
    """Find maximum recall achieved while maintaining at least min_precision."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    valid_recalls = recall[precision >= min_precision]
    return float(np.max(valid_recalls)) if len(valid_recalls) > 0 else 0.0


def calibration_summary(y_true: np.ndarray, y_score: np.ndarray, bins: int = 10) -> dict:
    """Reliability summary: per-bin mean predicted vs. observed default rate."""
    y_true = np.asarray(y_true, dtype=float)
    y_score = np.asarray(y_score, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(y_score, edges[1:-1]), 0, bins - 1)
    table = []
    abs_gaps = []
    for b in range(bins):
        mask = idx == b
        if not mask.any():
            continue
        mean_pred = float(y_score[mask].mean())
        obs = float(y_true[mask].mean())
        table.append({"bin": b, "n": int(mask.sum()), "mean_pred": mean_pred, "observed": obs})
        abs_gaps.append(abs(mean_pred - obs))
    return {"bins": table, "expected_calibration_error": float(np.mean(abs_gaps)) if abs_gaps else 0.0}


def core_metrics(y_true: np.ndarray, y_score: np.ndarray) -> dict:
    """AUC-ROC, KS, Brier, PR-AUC, Recall@Precision + calibration."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    return {
        "auc_roc": float(roc_auc_score(y_true, y_score)),
        "ks": ks_statistic(y_true, y_score),
        "brier": float(brier_score_loss(y_true, y_score)),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "recall_at_precision_50": recall_at_min_precision(y_true, y_score, min_precision=0.50),
        "calibration": calibration_summary(y_true, y_score),
    }

