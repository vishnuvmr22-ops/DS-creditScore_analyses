"""Slice 1 — feature pipeline determinism (FR-2, AD-2)."""

from __future__ import annotations

import pandas as pd

from creditsentinel.dataset import generate
from creditsentinel.features import pipeline as fp
from creditsentinel.features.schema import PROTECTED_ATTRIBUTE, TARGET


def _sample_applicant() -> dict:
    return {
        "age": 35,
        "annual_income": 55000,
        "employment_length": 5,
        "debt_to_income": 0.42,
        "credit_utilization": 0.65,
        "num_delinquencies": 2,
        "num_open_accounts": 8,
        "loan_amount": 18000,
        "interest_rate": 17.5,
        "home_ownership": "RENT",
        "purpose": "credit_card",
    }


def test_transform_is_deterministic():
    a = fp.transform(_sample_applicant())
    b = fp.transform(_sample_applicant())
    pd.testing.assert_frame_equal(a, b)


def test_feature_order_matches_names():
    feats = fp.transform(_sample_applicant())
    assert list(feats.columns) == fp.feature_names()


def test_protected_attribute_not_a_feature():
    names = fp.feature_names()
    assert PROTECTED_ATTRIBUTE not in names
    assert not any(PROTECTED_ATTRIBUTE in n for n in names)


def test_engineered_features_present():
    feats = fp.transform(_sample_applicant())
    assert "income_to_loan" in feats.columns
    assert feats.loc[0, "delinquency_flag"] == 1.0  # 2 delinquencies -> flag set


def test_dataset_generation_reproducible():
    d1 = generate(n=500, seed=7)
    d2 = generate(n=500, seed=7)
    pd.testing.assert_frame_equal(d1, d2)
    assert TARGET in d1.columns
    assert set(d1[TARGET].unique()) <= {0, 1}


def test_onehot_is_exclusive():
    feats = fp.transform(_sample_applicant())
    assert feats.loc[0, "home_ownership=RENT"] == 1.0
    assert feats.loc[0, "home_ownership=OWN"] == 0.0
    assert feats.loc[0, "purpose=credit_card"] == 1.0
