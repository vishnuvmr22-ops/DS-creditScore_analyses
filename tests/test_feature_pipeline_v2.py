"""Unit tests for Step 2 — Feature pipeline v2, Home Credit columns, engineered ratios, and validation."""

from __future__ import annotations

import numpy as np
import pytest
from pydantic import ValidationError

from creditsentinel.api.schemas import ScoreRequest
from creditsentinel.features.pipeline import (
    FEATURE_PIPELINE_VERSION,
    feature_names,
    transform,
)
from creditsentinel.homecredit import create_sample_homecredit_df


def test_pipeline_version_bumped():
    assert FEATURE_PIPELINE_VERSION == "2.0.0"


def test_synthetic_feature_transform_preserves_shape():
    raw = {
        "age": 30,
        "annual_income": 60000,
        "employment_length": 5,
        "debt_to_income": 0.25,
        "credit_utilization": 0.30,
        "num_delinquencies": 0,
        "num_open_accounts": 8,
        "loan_amount": 10000,
        "interest_rate": 10.0,
        "home_ownership": "RENT",
        "purpose": "debt_consolidation",
    }
    feats = transform(raw)
    expected_cols = feature_names(mode="synthetic")
    assert list(feats.columns) == expected_cols
    assert len(feats) == 1
    assert feats["income_to_loan"].iloc[0] == pytest.approx(6.0)
    assert feats["delinquency_flag"].iloc[0] == 0.0


def test_homecredit_feature_transform_engineered_ratios():
    raw_hc = {
        "age": 40.0,
        "annual_income": 100000.0,
        "employment_length": 10.0,
        "loan_amount": 200000.0,
        "annuity": 20000.0,
        "goods_price": 180000.0,
        "debt_to_income": 0.20,
        "EXT_SOURCE_1": 0.6,
        "EXT_SOURCE_2": 0.7,
        "EXT_SOURCE_3": 0.8,
        "NAME_CONTRACT_TYPE": "Cash loans",
        "NAME_INCOME_TYPE": "Working",
        "NAME_EDUCATION_TYPE": "Higher education",
        "NAME_FAMILY_STATUS": "Married",
        "NAME_HOUSING_TYPE": "House / apartment",
        "FLAG_OWN_CAR": "Y",
        "FLAG_OWN_REALTY": "Y",
    }
    feats = transform(raw_hc, mode="homecredit")
    expected_cols = feature_names(mode="homecredit")
    assert list(feats.columns) == expected_cols

    # Verify engineered ratios
    assert feats["credit_to_income"].iloc[0] == pytest.approx(2.0)
    assert feats["annuity_to_income"].iloc[0] == pytest.approx(0.20)
    assert feats["goods_to_loan"].iloc[0] == pytest.approx(0.90)
    assert feats["employment_to_age"].iloc[0] == pytest.approx(10.0 / 40.0)
    assert feats["ext_sources_mean"].iloc[0] == pytest.approx(0.70)


def test_zero_division_safety_in_ratios():
    """Ratios must handle 0 income, 0 loan, and young age safely without inf/nan."""
    edge_case = {
        "age": 0.0,
        "annual_income": 0.0,
        "employment_length": 0.0,
        "loan_amount": 0.0,
        "annuity": 0.0,
        "goods_price": 0.0,
        "debt_to_income": 0.0,
        "EXT_SOURCE_1": 0.0,
        "EXT_SOURCE_2": 0.0,
        "EXT_SOURCE_3": 0.0,
    }
    feats = transform(edge_case, mode="homecredit")
    assert np.isfinite(feats["credit_to_income"].iloc[0])
    assert np.isfinite(feats["annuity_to_income"].iloc[0])
    assert np.isfinite(feats["goods_to_loan"].iloc[0])
    assert np.isfinite(feats["employment_to_age"].iloc[0])


def test_score_request_validation_bounds():
    # Valid synthetic
    req_syn = ScoreRequest(
        applicant_id="A-1",
        age=25,
        annual_income=50000,
        employment_length=3,
        loan_amount=10000,
        debt_to_income=0.3,
        credit_utilization=0.4,
        num_delinquencies=0,
        num_open_accounts=5,
        interest_rate=12,
        home_ownership="OWN",
        purpose="credit_card",
    )
    assert req_syn.applicant_id == "A-1"

    # Valid homecredit
    req_hc = ScoreRequest(
        applicant_id="A-HC",
        age=35,
        annual_income=80000,
        employment_length=8,
        loan_amount=250000,
        debt_to_income=0.20,
        ext_source_1=0.45,
        ext_source_2=0.55,
        ext_source_3=0.65,
        annuity=15000,
        cnt_children=2,
        contract_type="Cash loans",
    )
    assert req_hc.ext_source_1 == 0.45
    assert req_hc.contract_type == "Cash loans"


    # Invalid EXT_SOURCE (> 1.0)
    with pytest.raises(ValidationError):
        ScoreRequest(
            applicant_id="ERR-1",
            age=30,
            annual_income=50000,
            employment_length=3,
            loan_amount=10000,
            debt_to_income=0.30,
            ext_source_1=1.5,  # out of [0, 1] bounds
        )

    # Invalid negative income
    with pytest.raises(ValidationError):
        ScoreRequest(
            applicant_id="ERR-2",
            age=30,
            annual_income=-500,
            employment_length=3,
            loan_amount=10000,
            debt_to_income=0.30,
        )

