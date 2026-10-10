"""Slice 6 — governance is read back from the registry for the SERVED version (FR-015).

Constitution III makes the registry the system of record. The console must never
recompute governance figures, and must never show figures belonging to a version
other than the one actually serving decisions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from creditsentinel.governance.fairness import approval_rate_parity
from creditsentinel.governance.gate import GovernedModel
from creditsentinel.governance.metrics import core_metrics
from creditsentinel.models.registry import MlflowRegistry


def _governed(card: str = "# Model Card\nSYNTHETIC content") -> GovernedModel:
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"f1": rng.normal(size=400), "f2": rng.normal(size=400)})
    y = (X["f1"] + rng.normal(0, 0.5, size=400) > 0).astype(int).to_numpy()
    model = LogisticRegression().fit(X, y)
    scores = model.predict_proba(X)[:, 1]
    return GovernedModel(
        model=model,
        feature_pipeline_version="1.0.0",
        metrics=core_metrics(y, scores),
        fairness=approval_rate_parity(pd.Series(rng.choice(["A", "B"], size=400)), scores, 0.45),
        model_card=card,
        params={"solver": "lbfgs"},
        n_train=400,
        n_test=100,
    )


@pytest.fixture
def registry(tmp_path):
    uri = f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}"
    return MlflowRegistry(uri, "test-pd", (tmp_path / "artifacts").as_uri())


def test_governance_matches_the_registered_artifacts(registry):
    registry.register_governed(_governed())
    record = registry.load_governance()

    assert record.model_version == "1"
    assert record.feature_pipeline_version == "1.0.0"
    assert 0.0 <= record.metrics["auc_roc"] <= 1.0
    assert "ks" in record.metrics and "brier" in record.metrics
    assert "expected_calibration_error" in record.metrics["calibration"]
    assert record.metrics["calibration"]["bins"]
    assert set(record.fairness) >= {
        "approval_rate_by_group", "parity_gap", "disparate_impact_ratio",
    }


def test_governance_tracks_the_served_version(registry):
    """A second registration moves both the served model and its governance together."""
    registry.register_governed(_governed())
    registry.register_governed(_governed(card="# Model Card\nSECOND version"))

    served = registry.load_latest()
    record = registry.load_governance()
    assert record.model_version == served.model_version == "2"
    assert "SECOND version" in registry.load_model_card()[1]


def test_model_card_is_returned_verbatim(registry):
    registry.register_governed(_governed(card="# Model Card\nline one\n\nline two"))
    version, content = registry.load_model_card()
    assert version == "1"
    assert content == "# Model Card\nline one\n\nline two"


def test_governance_raises_when_no_model_is_registered(registry):
    with pytest.raises(RuntimeError):
        registry.load_governance()


def test_model_card_raises_when_no_model_is_registered(registry):
    with pytest.raises(RuntimeError):
        registry.load_model_card()
