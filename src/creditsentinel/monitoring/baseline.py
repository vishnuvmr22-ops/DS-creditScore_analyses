"""PSI baseline construction (used by training; consumed by the drift job).

Captures a reference distribution per feature (and for the PD score) as fixed bin
edges + reference proportions, so the drift job can compute PSI on new batches.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

N_BINS = 10
_EPS = 1e-6


def _quantile_edges(values: np.ndarray, n_bins: int = N_BINS) -> list[float]:
    """Unique quantile bin edges with open outer bounds (-inf, +inf)."""
    qs = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.unique(np.quantile(values, qs))
    if edges.size < 2:  # constant feature
        edges = np.array([values.min() - 1.0, values.max() + 1.0])
    edges = edges.astype(float)
    edges[0] = -np.inf
    edges[-1] = np.inf
    return edges.tolist()


def _proportions(values: np.ndarray, edges: list[float]) -> list[float]:
    counts, _ = np.histogram(values, bins=np.array(edges))
    props = counts / max(counts.sum(), 1)
    return (props + _EPS).tolist()


def build_baseline(features: pd.DataFrame, scores: np.ndarray) -> dict:
    """Return a JSON-serializable baseline of reference distributions."""
    feat_baseline = {}
    for col in features.columns:
        vals = features[col].to_numpy(dtype=float)
        edges = _quantile_edges(vals)
        feat_baseline[col] = {"edges": edges, "props": _proportions(vals, edges)}

    score_edges = _quantile_edges(np.asarray(scores, dtype=float))
    return {
        "features": feat_baseline,
        "score": {"edges": score_edges, "props": _proportions(np.asarray(scores), score_edges)},
        "n_bins": N_BINS,
    }
