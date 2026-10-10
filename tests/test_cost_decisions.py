"""Tests for Expected Loss, cost-based decision optimization, and profit curves (Step 6)."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest

from creditsentinel.config import Settings
from creditsentinel.cost import (
    compute_expected_loss,
    compute_portfolio_pnl,
    compute_profit_curve,
    generate_threshold_report,
)
from creditsentinel.decision import decide


def test_compute_expected_loss_scalar_and_array():
    # EL = PD * LGD * loan_amount
    # 0.10 * 0.65 * 10000 = 650.0
    el_scalar = compute_expected_loss(0.10, lgd=0.65, loan_amount=10000.0)
    assert el_scalar == pytest.approx(650.0)

    # Array computation
    pds = np.array([0.05, 0.20, 0.50])
    loans = np.array([10000.0, 20000.0, 5000.0])
    el_arr = compute_expected_loss(pds, lgd=0.60, loan_amount=loans)
    assert len(el_arr) == 3
    assert el_arr[0] == pytest.approx(0.05 * 0.60 * 10000.0)
    assert el_arr[1] == pytest.approx(0.20 * 0.60 * 20000.0)
    assert el_arr[2] == pytest.approx(0.50 * 0.60 * 5000.0)


def test_portfolio_pnl_calculation():
    y_true = np.array([0, 0, 1, 1])
    y_score = np.array([0.10, 0.20, 0.30, 0.80])
    loans = np.array([10000.0, 10000.0, 10000.0, 10000.0])

    # Threshold 0.25 approves indices 0 and 1 (both y=0)
    res = compute_portfolio_pnl(y_true, y_score, loans, threshold=0.25, lgd=0.65, interest_margin=0.08)
    assert res["n_approved"] == 2
    assert res["approval_rate"] == 0.50
    assert res["default_rate_approved"] == 0.0
    # Revenue = 2 * (10000 * 0.08) = 1600.0, loss = 0
    assert res["total_revenue"] == 1600.0
    assert res["total_default_loss"] == 0.0
    assert res["net_profit"] == 1600.0

    # Threshold 0.50 approves indices 0, 1, and 2 (one y=1 defaulter)
    res_high = compute_portfolio_pnl(y_true, y_score, loans, threshold=0.50, lgd=0.65, interest_margin=0.08)
    assert res_high["n_approved"] == 3
    # Revenue = 2 * (10000 * 0.08) = 1600.0, loss = 1 * (10000 * 0.65) = 6500.0
    assert res_high["total_revenue"] == 1600.0
    assert res_high["total_default_loss"] == 6500.0
    assert res_high["net_profit"] == 1600.0 - 6500.0


def test_compute_profit_curve_finds_optimum():
    rng = np.random.default_rng(42)
    n = 500
    y_true = rng.choice([0, 1], size=n, p=[0.88, 0.12])
    # Scores correlate with true defaults
    y_score = np.clip(np.where(y_true == 1, rng.normal(0.45, 0.15, size=n), rng.normal(0.12, 0.08, size=n)), 0.01, 0.99)
    loans = rng.uniform(5000.0, 25000.0, size=n)

    res = compute_profit_curve(
        y_true, y_score, loans, lgd=0.65, interest_margin=0.08, n_thresholds=50
    )

    assert "optimal" in res
    assert "baseline" in res
    assert "comparison" in res
    assert "curve" in res
    assert 0.0 < res["optimal"]["threshold"] < 1.0
    assert res["optimal"]["net_profit"] >= res["baseline"]["net_profit"]


def test_generate_threshold_report(tmp_path):
    rng = np.random.default_rng(42)
    n = 100
    y_true = rng.choice([0, 1], size=n, p=[0.9, 0.1])
    y_score = rng.uniform(0.05, 0.70, size=n)
    loans = np.full(n, 10000.0)

    res = compute_profit_curve(y_true, y_score, loans, lgd=0.65, interest_margin=0.08, n_thresholds=20)
    md, plot_path = generate_threshold_report(res, tmp_path, generate_plot=True)

    assert (tmp_path / "threshold_analysis.md").exists()
    assert "Expected Loss & Cost-Based Threshold Optimization Report" in md
    assert "Loss Given Default (LGD)" in md
    if plot_path:
        assert plot_path.exists()


def test_service_score_includes_expected_loss_and_respects_decision_mode(service):
    from creditsentinel.api.schemas import ScoreRequest

    req = ScoreRequest(
        applicant_id="app-test-cost",
        age=35.0,
        annual_income=75000.0,
        employment_length=5.0,
        debt_to_income=0.25,
        credit_utilization=0.30,
        num_delinquencies=0.0,
        num_open_accounts=6.0,
        loan_amount=20000.0,
        interest_rate=12.0,
        home_ownership="MORTGAGE",
        purpose="debt_consolidation",
    )

    # 1. Default bands mode
    service.settings.decision_mode = "bands"
    resp_bands = service.score(req)
    assert resp_bands.expected_loss is not None
    assert resp_bands.expected_loss > 0
    assert resp_bands.thresholds.approve_below == service.settings.approve_below

    # 2. Cost-based mode
    service.settings.decision_mode = "cost_based"
    service.settings.cost_optimized_approve_below = 0.25
    service.settings.cost_optimized_decline_at_or_above = 0.40
    resp_cost = service.score(req)
    assert resp_cost.expected_loss is not None
    assert resp_cost.thresholds.approve_below == 0.25
    assert resp_cost.thresholds.decline_at_or_above == 0.40
