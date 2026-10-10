"""SHAP driver attribution (FR-11, AD-3). Pure core over a fitted tree model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap

from ..features.schema import FEATURE_LABELS


@dataclass
class Driver:
    feature: str
    label: str
    shap: float
    direction: str  # "increases_risk" | "decreases_risk"

    def as_dict(self) -> dict:
        return {
            "feature": self.feature,
            "label": self.label,
            "shap": round(self.shap, 6),
            "direction": self.direction,
        }


class ShapDriverExtractor:
    """Wraps a SHAP TreeExplainer for a fitted tree PD model."""

    def __init__(self, model):
        self._explainer = shap.TreeExplainer(model)

    def top_drivers(self, features: pd.DataFrame, top_n: int) -> list[Driver]:
        """Return the top-N drivers for a single-row feature frame, ranked by |shap|.

        Positive SHAP raises the default log-odds ⇒ increases risk.
        """
        if len(features) != 1:
            raise ValueError("top_drivers expects exactly one applicant row")
        values = self._explainer.shap_values(features)
        arr = np.asarray(values)
        # Binary classifiers may return (1, n_features) or (n_features,).
        row = arr.reshape(arr.shape[0], -1)[0] if arr.ndim > 1 else arr
        order = np.argsort(np.abs(row))[::-1][:top_n]
        drivers: list[Driver] = []
        for i in order:
            name = features.columns[i]
            val = float(row[i])
            drivers.append(
                Driver(
                    feature=name,
                    label=FEATURE_LABELS.get(name, name.replace("=", " = ").replace("_", " ")),
                    shap=val,
                    direction="increases_risk" if val > 0 else "decreases_risk",
                )
            )
        return drivers


def risk_increasing(drivers: list[Driver]) -> list[Driver]:
    """Subset of drivers that push toward decline — the basis for an adverse reason."""
    return [d for d in drivers if d.direction == "increases_risk"]
