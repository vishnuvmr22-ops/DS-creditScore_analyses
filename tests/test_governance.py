"""Slice 1 — governance metrics, fairness, and the registration gate (FR-4..FR-7)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from creditsentinel.governance.fairness import approval_rate_parity
from creditsentinel.governance.gate import GovernanceError, GovernedModel, assert_governed
from creditsentinel.governance.metrics import core_metrics, ks_statistic
from creditsentinel.governance.model_card import build_model_card


def _good_metrics():
    rng = np.random.default_rng(0)
    y = rng.binomial(1, 0.3, size=2000)
    score = np.clip(0.3 + 0.4 * y + rng.normal(0, 0.1, size=2000), 0, 1)
    return core_metrics(y, score)


def test_core_metrics_keys_present():
    m = _good_metrics()
    assert {"auc_roc", "ks", "brier", "calibration"} <= set(m)
    assert 0.0 <= m["auc_roc"] <= 1.0


def test_ks_perfect_separation():
    y = np.array([0, 0, 1, 1])
    score = np.array([0.1, 0.2, 0.8, 0.9])
    assert ks_statistic(y, score) == pytest.approx(1.0)


def test_fairness_parity_shape():
    groups = pd.Series(["A", "A", "B", "B"])
    scores = np.array([0.1, 0.7, 0.1, 0.7])
    f = approval_rate_parity(groups, scores, decline_at_or_above=0.6)
    assert set(f["approval_rate_by_group"]) == {"A", "B"}
    assert 0.0 <= f["disparate_impact_ratio"] <= 1.0


def _bundle(**overrides) -> GovernedModel:
    base = dict(
        model=object(),
        feature_pipeline_version="1.0.0",
        metrics=_good_metrics(),
        fairness=approval_rate_parity(
            pd.Series(["A", "B"] * 10), np.linspace(0, 1, 20), 0.6
        ),
        model_card="# card\ncontent",
        params={"n_estimators": 10},
        n_train=100,
        n_test=50,
    )
    base.update(overrides)
    return GovernedModel(**base)


def test_gate_passes_for_governed_model():
    assert_governed(_bundle())  # should not raise


def test_gate_rejects_missing_metrics():
    with pytest.raises(GovernanceError):
        assert_governed(_bundle(metrics={}))


def test_gate_rejects_missing_fairness():
    with pytest.raises(GovernanceError):
        assert_governed(_bundle(fairness={}))


def test_gate_rejects_missing_card():
    with pytest.raises(GovernanceError):
        assert_governed(_bundle(model_card=""))


def test_model_card_contains_required_sections():
    card = build_model_card(
        "creditsentinel-pd", 3, "1.0.0", _good_metrics(),
        approval_rate_parity(pd.Series(["A", "B"] * 10), np.linspace(0, 1, 20), 0.6),
        "SYNTHETIC DATA note", 100, 50,
    )
    for section in ["Intended use", "Data provenance", "Performance metrics", "Fairness", "Limitations"]:
        assert section in card
    assert "SYNTHETIC" in card


def test_extended_fairlearn_audit_metrics_and_gaps():
    from creditsentinel.governance.fairness import extended_fairlearn_audit

    rng = np.random.default_rng(42)
    n = 200
    y_true = rng.choice([0, 1], size=n, p=[0.85, 0.15])
    y_score = rng.uniform(0.1, 0.9, size=n)
    sensitive_features = pd.DataFrame({
        "gender": rng.choice(["F", "M"], size=n),
        "age_group": rng.choice(["<25", "25-34", "35-49"], size=n),
        "region_rating": rng.choice(["1", "2", "3"], size=n),
    })

    audit = extended_fairlearn_audit(y_true, y_score, sensitive_features, decline_at_or_above=0.45)

    assert "by_dimension" in audit
    assert "largest_gaps" in audit
    assert set(audit["by_dimension"].keys()) == {"gender", "age_group", "region_rating"}

    for dim in ["gender", "age_group", "region_rating"]:
        dim_info = audit["by_dimension"][dim]
        assert "by_group" in dim_info
        assert "selection_rate" in dim_info["by_group"]
        assert "false_positive_rate" in dim_info["by_group"]
        assert "false_negative_rate" in dim_info["by_group"]
        assert 0.0 <= dim_info["selection_rate_gap"] <= 1.0

    largest = audit["largest_gaps"]
    assert 0.0 <= largest["selection_rate"] <= 1.0
    assert 0.0 <= largest["false_positive_rate"] <= 1.0
    assert 0.0 <= largest["false_negative_rate"] <= 1.0


def test_mitigation_threshold_optimizer_experiment():
    from creditsentinel.governance.fairness import mitigation_threshold_optimizer_experiment

    rng = np.random.default_rng(42)
    n = 300
    y_true = rng.choice([0, 1], size=n, p=[0.9, 0.1])
    # Give Group B higher average risk scores to test mitigation
    gender = pd.Series(rng.choice(["F", "M"], size=n))
    y_score = np.where(gender == "M", rng.uniform(0.3, 0.8, size=n), rng.uniform(0.1, 0.6, size=n))

    result = mitigation_threshold_optimizer_experiment(y_true, y_score, gender, decline_at_or_above=0.45)

    assert result["status"] == "offline_simulation_only"
    assert "before" in result
    assert "after" in result
    assert "mitigated_thresholds_by_group" in result
    assert set(result["mitigated_thresholds_by_group"].keys()) == {"F", "M"}
    # Disparity gap after quantile threshold optimization should be equalized / smaller
    assert result["after"]["disparity_gap"] <= result["before"]["disparity_gap"] + 0.05

