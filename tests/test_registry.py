"""Slice 1 — MLflow registry adapter: governed register + load roundtrip (AD-1, AD-5)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from creditsentinel.governance.fairness import approval_rate_parity
from creditsentinel.governance.gate import GovernanceError, GovernedModel
from creditsentinel.governance.metrics import core_metrics
from creditsentinel.models.registry import MlflowRegistry


def _tiny_governed_model() -> GovernedModel:
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
        model_card="# card\nSYNTHETIC content",
        params={"solver": "lbfgs"},
        n_train=400,
        n_test=100,
    )


@pytest.fixture
def registry(tmp_path):
    uri = f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}"
    art = (tmp_path / "artifacts").as_uri()
    return MlflowRegistry(uri, "test-pd", art)


def test_register_and_load_roundtrip(registry):
    version = registry.register_governed(_tiny_governed_model())
    assert str(version) == "1"
    loaded = registry.load_latest()
    assert loaded.model_version == "1"
    assert loaded.feature_pipeline_version == "1.0.0"
    preds = loaded.predict_pd(pd.DataFrame({"f1": [0.0, 2.0], "f2": [0.0, -1.0]}))
    assert preds.shape == (2,)
    assert ((preds >= 0) & (preds <= 1)).all()


def test_registry_refuses_ungoverned(registry):
    bad = _tiny_governed_model()
    bad.metrics = {}  # strip governance
    with pytest.raises(GovernanceError):
        registry.register_governed(bad)


def test_load_without_model_errors(registry):
    with pytest.raises(RuntimeError):
        registry.load_latest()
