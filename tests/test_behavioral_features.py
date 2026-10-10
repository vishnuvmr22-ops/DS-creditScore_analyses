"""Unit tests for Step 3 — Offline behavioral & transaction feature aggregation."""

from __future__ import annotations

import pandas as pd
import pytest

from creditsentinel.config import Settings
from creditsentinel.features.aggregate import (
    BEHAVIORAL_DEFAULTS,
    aggregate_bureau,
    aggregate_credit_card,
    aggregate_installments,
    build_behavioral_features,
    merge_behavioral_features,
)
from creditsentinel.features.pipeline import feature_names, transform
from creditsentinel.homecredit import create_sample_homecredit_df


def test_aggregate_installments_rfm_metrics():
    df_inst = pd.DataFrame({
        "SK_ID_CURR": [101, 101, 101, 102],
        "DAYS_INSTALMENT": [-100, -70, -40, -50],
        "DAYS_ENTRY_PAYMENT": [-95, -75, -30, -50],  # 101 has 2 late payments (-95>-100, -30>-40)
        "AMT_INSTALMENT": [5000.0, 5000.0, 5000.0, 8000.0],
        "AMT_PAYMENT": [5000.0, 5000.0, 4000.0, 8000.0],  # 101 has 1 underpayment
    })

    agg = aggregate_installments(df_inst)
    assert len(agg) == 2
    row_101 = agg[agg["SK_ID_CURR"] == 101].iloc[0]

    # 2 out of 3 late payments
    assert row_101["installment_late_ratio"] == pytest.approx(2.0 / 3.0)
    # Days past due: 5 + 0 + 10 = 15 / 3 = 5.0
    assert row_101["mean_days_past_due"] == pytest.approx(5.0)
    # Underpayment: 1 out of 3
    assert row_101["installment_underpay_ratio"] == pytest.approx(1.0 / 3.0)
    # Recency: min -DAYS_ENTRY_PAYMENT -> -(-30) = 30 days ago
    assert row_101["payment_recency_days"] == pytest.approx(30.0)
    assert row_101["payment_count"] == 3
    assert row_101["payment_total_amount"] == pytest.approx(14000.0)
    assert row_101["payment_avg_amount"] == pytest.approx(14000.0 / 3.0)


def test_aggregate_bureau_metrics():
    df_bureau = pd.DataFrame({
        "SK_ID_CURR": [201, 201, 202],
        "CREDIT_ACTIVE": ["Active", "Closed", "Active"],
        "DAYS_CREDIT": [-300, -600, -100],
        "AMT_CREDIT_SUM": [100000.0, 50000.0, 200000.0],
        "AMT_CREDIT_SUM_DEBT": [40000.0, 0.0, 150000.0],
        "AMT_CREDIT_SUM_OVERDUE": [0.0, 0.0, 5000.0],
    })

    agg = aggregate_bureau(df_bureau)
    assert len(agg) == 2
    row_201 = agg[agg["SK_ID_CURR"] == 201].iloc[0]

    assert row_201["bureau_total_loans_count"] == 2
    assert row_201["bureau_active_loans_count"] == 1
    assert row_201["bureau_total_debt"] == pytest.approx(40000.0)
    assert row_201["bureau_total_overdue"] == pytest.approx(0.0)
    # Debt to credit ratio: 40000 / (100000 + 50000) = 40000 / 150000
    assert row_201["bureau_debt_to_credit_ratio"] == pytest.approx(40000.0 / 150000.0)


def test_aggregate_credit_card_metrics():
    df_cc = pd.DataFrame({
        "SK_ID_CURR": [301, 301],
        "AMT_BALANCE": [20000.0, 40000.0],
        "AMT_CREDIT_LIMIT_ACTUAL": [50000.0, 50000.0],
        "AMT_DRAWINGS_ATM_CURRENT": [5000.0, 2000.0],
        "AMT_DRAWINGS_POS_CURRENT": [15000.0, 10000.0],
    })

    agg = aggregate_credit_card(df_cc)
    assert len(agg) == 1
    row_301 = agg.iloc[0]
    # Utilization: (0.4 + 0.8) / 2 = 0.6
    assert row_301["cc_utilization_mean"] == pytest.approx(0.60)
    assert row_301["cc_balance_mean"] == pytest.approx(30000.0)
    assert row_301["cc_drawings_atm_sum"] == pytest.approx(7000.0)
    assert row_301["cc_drawings_pos_sum"] == pytest.approx(25000.0)


def test_build_and_merge_behavioral_features(tmp_path):
    df_inst = pd.DataFrame({
        "SK_ID_CURR": [1001],
        "DAYS_INSTALMENT": [-50],
        "DAYS_ENTRY_PAYMENT": [-40],
        "AMT_INSTALMENT": [1000.0],
        "AMT_PAYMENT": [1000.0],
    })

    out_file = tmp_path / "behavioral.parquet"
    behavioral_df = build_behavioral_features(
        raw_dir=tmp_path,
        output_path=out_file,
        installments_df=df_inst,
    )
    assert out_file.exists()
    assert len(behavioral_df) == 1
    assert behavioral_df.iloc[0]["has_behavioral_history"] == 1.0

    # Applicant test frame: one with history (1001), one without (1002)
    applicants = pd.DataFrame({
        "SK_ID_CURR": [1001, 1002],
        "age": [30.0, 45.0],
        "annual_income": [50000.0, 80000.0],
    })

    merged = merge_behavioral_features(applicants, behavioral_df=behavioral_df)
    assert len(merged) == 2

    # Applicant 1001 has history
    assert merged.loc[merged["SK_ID_CURR"] == 1001, "has_behavioral_history"].iloc[0] == 1.0
    # Applicant 1002 has NO history -> defaults applied
    assert merged.loc[merged["SK_ID_CURR"] == 1002, "has_behavioral_history"].iloc[0] == 0.0
    assert merged.loc[merged["SK_ID_CURR"] == 1002, "payment_recency_days"].iloc[0] == BEHAVIORAL_DEFAULTS["payment_recency_days"]


def test_feature_pipeline_includes_behavioral_when_enabled():
    sample_hc = create_sample_homecredit_df(n=5, seed=42)
    # Add behavioral defaults
    for col, val in BEHAVIORAL_DEFAULTS.items():
        sample_hc[col] = val
    sample_hc["has_behavioral_history"] = 1.0

    feats_with_beh = transform(sample_hc, mode="homecredit", use_behavioral=True)
    expected_cols = feature_names(mode="homecredit", use_behavioral=True)
    assert list(feats_with_beh.columns) == expected_cols
    assert "has_behavioral_history" in feats_with_beh.columns
    assert "installment_late_ratio" in feats_with_beh.columns
    assert "bureau_active_loans_count" in feats_with_beh.columns
    assert "cc_utilization_mean" in feats_with_beh.columns
