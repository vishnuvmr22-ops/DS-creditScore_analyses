"""Governed-registration gate (FR-6, AD-5, constitution III).

Ungoverned models cannot be registered: a version must carry core metrics, a
fairness metric, and a model card, or registration is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_METRIC_KEYS = {"auc_roc", "ks", "brier", "calibration"}
REQUIRED_FAIRNESS_KEYS = {"approval_rate_by_group", "parity_gap", "disparate_impact_ratio"}


class GovernanceError(RuntimeError):
    """Raised when a model version fails the governance gate."""


@dataclass
class GovernedModel:
    model: Any
    feature_pipeline_version: str
    metrics: dict
    fairness: dict
    model_card: str
    params: dict
    n_train: int
    n_test: int
    fairness_extended: dict | None = None


def assert_governed(bundle: GovernedModel) -> None:
    """Raise :class:`GovernanceError` if any governance artifact is missing."""
    missing = REQUIRED_METRIC_KEYS - set(bundle.metrics or {})
    if missing:
        raise GovernanceError(f"cannot register: missing metrics {sorted(missing)}")
    missing_f = REQUIRED_FAIRNESS_KEYS - set(bundle.fairness or {})
    if missing_f:
        raise GovernanceError(f"cannot register: missing fairness metrics {sorted(missing_f)}")
    if not (bundle.model_card and bundle.model_card.strip()):
        raise GovernanceError("cannot register: missing model card")
    if not bundle.feature_pipeline_version:
        raise GovernanceError("cannot register: missing feature_pipeline_version")
