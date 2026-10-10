"""Cost-based decisioning, Expected Loss, and profit curve optimization (Step 6).

Financial and Economic Assumptions:
----------------------------------
1. Expected Loss (EL) Formula:
     EL = PD * LGD * EAD (Exposure At Default / loan_amount)
   where:
     - PD  (Probability of Default) in [0, 1] is the calibrated risk score.
     - LGD (Loss Given Default) in [0, 1] represents the fractional net loss post recovery
           (default: 0.65 or 65%, standard industry baseline for uncollateralized retail credit).
     - EAD is the loan principal amount requested.

2. Profit & Loss (P&L) Function:
   - For an approved performing loan (y = 0):
       Revenue = interest_margin * loan_amount
       (default interest_margin: 0.08 or 8% annual net margin over cost of funds).
   - For an approved defaulting loan (y = 1):
       Loss = - (LGD * loan_amount)
   - For a declined loan:
       P&L = $0 (opportunity cost can be tracked separately).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def compute_expected_loss(
    pd: float | np.ndarray,
    lgd: float = 0.65,
    loan_amount: float | np.ndarray = 10000.0,
) -> float | np.ndarray:
    """Compute expected credit loss: EL = PD * LGD * loan_amount.

    Pure function with transparent assumptions.
    """
    pd_arr = np.asarray(pd, dtype=float)
    loan_arr = np.asarray(loan_amount, dtype=float)
    el = pd_arr * float(lgd) * loan_arr
    if isinstance(pd, (int, float)) and isinstance(loan_amount, (int, float)):
        return float(el)
    return el


def compute_portfolio_pnl(
    y_true: np.ndarray,
    y_score: np.ndarray,
    loan_amounts: np.ndarray,
    threshold: float,
    lgd: float = 0.65,
    interest_margin: float = 0.08,
) -> dict[str, float]:
    """Calculate realized portfolio revenue, default loss, and net profit at a decision threshold.

    Decision policy: Approve if y_score < threshold, Decline otherwise.
    """
    y_t = np.asarray(y_true, dtype=int)
    y_s = np.asarray(y_score, dtype=float)
    loans = np.asarray(loan_amounts, dtype=float)

    approved = y_s < threshold
    n_total = len(y_t)
    n_approved = int(np.sum(approved))
    approval_rate = float(n_approved / max(n_total, 1))

    # Revenue from approved non-defaulters
    good_approved = approved & (y_t == 0)
    total_revenue = float(np.sum(loans[good_approved] * interest_margin))

    # Default losses from approved defaulters
    bad_approved = approved & (y_t == 1)
    total_default_loss = float(np.sum(loans[bad_approved] * lgd))

    # Expected Loss (model-based sum across approved loans)
    total_expected_loss = float(np.sum(compute_expected_loss(y_s[approved], lgd, loans[approved])))

    net_profit = total_revenue - total_default_loss
    default_rate_approved = float(np.sum(bad_approved) / max(n_approved, 1))

    return {
        "threshold": round(float(threshold), 4),
        "n_approved": n_approved,
        "approval_rate": round(approval_rate, 4),
        "default_rate_approved": round(default_rate_approved, 4),
        "total_revenue": round(total_revenue, 2),
        "total_default_loss": round(total_default_loss, 2),
        "net_profit": round(net_profit, 2),
        "total_expected_loss": round(total_expected_loss, 2),
    }


def compute_profit_curve(
    y_true: np.ndarray,
    y_score: np.ndarray,
    loan_amounts: np.ndarray,
    lgd: float = 0.65,
    interest_margin: float = 0.08,
    n_thresholds: int = 100,
    baseline_approve_below: float = 0.15,
    baseline_decline_above: float = 0.45,
) -> dict[str, Any]:
    """Evaluate P&L across a continuum of approval thresholds to find the profit-maximizing cutoff."""
    y_t = np.asarray(y_true, dtype=int)
    y_s = np.asarray(y_score, dtype=float)
    loans = np.asarray(loan_amounts, dtype=float)

    threshold_grid = np.linspace(0.01, 0.99, n_thresholds)
    curve_points = []
    best_profit = -float("inf")
    best_threshold = 0.15
    best_stats = {}

    for t in threshold_grid:
        stats = compute_portfolio_pnl(y_t, y_s, loans, t, lgd=lgd, interest_margin=interest_margin)
        curve_points.append(stats)
        if stats["net_profit"] > best_profit:
            best_profit = stats["net_profit"]
            best_threshold = t
            best_stats = stats

    # Baseline P&L (standard band policy: approve < 0.15, review approved at 50% or binary threshold 0.15)
    baseline_stats = compute_portfolio_pnl(
        y_t, y_s, loans, baseline_approve_below, lgd=lgd, interest_margin=interest_margin
    )

    profit_gain = float(best_stats["net_profit"] - baseline_stats["net_profit"])
    profit_gain_pct = (
        float(profit_gain / max(abs(baseline_stats["net_profit"]), 1.0) * 100)
        if baseline_stats["net_profit"] != 0
        else 0.0
    )

    el_reduction = float(baseline_stats["total_expected_loss"] - best_stats["total_expected_loss"])
    el_reduction_pct = (
        float(el_reduction / max(baseline_stats["total_expected_loss"], 1.0) * 100)
        if baseline_stats["total_expected_loss"] > 0
        else 0.0
    )

    return {
        "assumptions": {
            "lgd": lgd,
            "interest_margin": interest_margin,
            "baseline_approve_below": baseline_approve_below,
            "baseline_decline_above": baseline_decline_above,
        },
        "optimal": {
            "threshold": round(float(best_threshold), 4),
            "net_profit": best_stats["net_profit"],
            "approval_rate": best_stats["approval_rate"],
            "default_rate_approved": best_stats["default_rate_approved"],
            "total_expected_loss": best_stats["total_expected_loss"],
        },
        "baseline": {
            "threshold": baseline_approve_below,
            "net_profit": baseline_stats["net_profit"],
            "approval_rate": baseline_stats["approval_rate"],
            "default_rate_approved": baseline_stats["default_rate_approved"],
            "total_expected_loss": baseline_stats["total_expected_loss"],
        },
        "comparison": {
            "profit_gain": round(profit_gain, 2),
            "profit_gain_pct": round(profit_gain_pct, 2),
            "expected_loss_reduction": round(el_reduction, 2),
            "expected_loss_reduction_pct": round(el_reduction_pct, 2),
        },
        "curve": curve_points,
    }


def generate_threshold_report(
    analysis_results: dict,
    reports_dir: Path | str,
    generate_plot: bool = True,
) -> tuple[str, Path | None]:
    """Generate reports/threshold_analysis.md and render the profit curve plot."""
    rep_dir = Path(reports_dir)
    rep_dir.mkdir(parents=True, exist_ok=True)

    assumptions = analysis_results["assumptions"]
    opt = analysis_results["optimal"]
    base = analysis_results["baseline"]
    comp = analysis_results["comparison"]
    curve = analysis_results["curve"]

    plot_path = None
    if generate_plot:
        try:
            import matplotlib.pyplot as plt

            thresholds = [p["threshold"] for p in curve]
            profits = [p["net_profit"] for p in curve]
            app_rates = [p["approval_rate"] * 100 for p in curve]

            fig, ax1 = plt.subplots(figsize=(10, 6))

            color = "tab:blue"
            ax1.set_xlabel("Decision Threshold (PD Cutoff)", fontsize=12)
            ax1.set_ylabel("Net Portfolio Profit ($)", color=color, fontsize=12)
            line1 = ax1.plot(thresholds, profits, color=color, linewidth=2.5, label="Net Profit ($)")
            ax1.tick_params(axis="y", labelcolor=color)

            # Highlight optimal threshold
            ax1.axvline(
                opt["threshold"],
                color="tab:green",
                linestyle="--",
                linewidth=2,
                label=f"Optimal Threshold ({opt['threshold']:.2f})",
            )
            # Highlight baseline threshold
            ax1.axvline(
                base["threshold"],
                color="tab:red",
                linestyle=":",
                linewidth=2,
                label=f"Baseline Threshold ({base['threshold']:.2f})",
            )

            # Secondary axis: Approval rate
            ax2 = ax1.twinx()
            color = "tab:purple"
            ax2.set_ylabel("Approval Rate (%)", color=color, fontsize=12)
            line2 = ax2.plot(thresholds, app_rates, color=color, linestyle="-.", linewidth=1.5, label="Approval Rate (%)")
            ax2.tick_params(axis="y", labelcolor=color)

            # Combine legends
            lines = line1 + line2 + [
                plt.Line2D([0], [0], color="tab:green", linestyle="--", lw=2),
                plt.Line2D([0], [0], color="tab:red", linestyle=":", lw=2),
            ]
            labels = ["Net Profit ($)", "Approval Rate (%)", f"Optimal Cutoff ({opt['threshold']:.2f})", f"Baseline Cutoff ({base['threshold']:.2f})"]
            ax1.legend(lines, labels, loc="upper right", frameon=True)

            plt.title("CreditSentinel Expected Loss & Profit Optimization Curve", fontsize=14, fontweight="bold", pad=15)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            plot_path = rep_dir / "profit_curve.png"
            plt.savefig(plot_path, dpi=300)
            plt.close()
        except Exception as e:
            plot_path = None

    md = f"""# CreditSentinel Expected Loss & Cost-Based Threshold Optimization Report

_Generated {pd.Timestamp.now().isoformat(timespec='seconds')}_

> **ECONOMIC ASSUMPTION DISCLAIMER**:
> All calculations in this report are based on assumed financial parameters:
> - **Loss Given Default (LGD)**: `{assumptions['lgd']:.2f}` (Assumes 65% loss on default after collection/recovery)
> - **Net Interest Margin**: `{assumptions['interest_margin']:.2f}` (Assumes 8% net margin over funding costs)
> - **Exposure at Default (EAD)**: Loan principal amount requested.

---

## 1. Executive Summary & Policy Comparison

| Metric | Baseline Policy (`approve < {base['threshold']:.2f}`) | Cost-Optimized Policy (`approve < {opt['threshold']:.2f}`) | Impact / Uplift |
| :--- | :---: | :---: | :---: |
| **Decision Threshold** | `{base['threshold']:.4f}` | **`{opt['threshold']:.4f}`** | `+{opt['threshold'] - base['threshold']:.4f}` |
| **Portfolio Approval Rate** | `{base['approval_rate'] * 100:.2f}%` | **`{opt['approval_rate'] * 100:.2f}%`** | `{comp['profit_gain_pct'] > 0 and '+' or ''}{(opt['approval_rate'] - base['approval_rate']) * 100:.2f}%` |
| **Default Rate in Approvals** | `{base['default_rate_approved'] * 100:.2f}%` | **`{opt['default_rate_approved'] * 100:.2f}%`** | `{(opt['default_rate_approved'] - base['default_rate_approved']) * 100:.2f}%` |
| **Total Expected Loss** | `${base['total_expected_loss']:,.2f}` | **`${opt['total_expected_loss']:,.2f}`** | **`{comp['expected_loss_reduction'] >= 0 and '-' or '+'}${abs(comp['expected_loss_reduction']):,.2f}`** |
| **Net Portfolio Profit** | `${base['net_profit']:,.2f}` | **`${opt['net_profit']:,.2f}`** | **`+${comp['profit_gain']:,.2f}` (`+{comp['profit_gain_pct']:.2f}%`)** |

---

## 2. Theoretical Framework

1. **Expected Loss Formulation**:
   $$\\text{{EL}} = \\text{{PD}} \\times \\text{{LGD}} \\times \\text{{Loan\\_Amount}}$$

2. **Portfolio P&L Objective Function**:
   $$\\max_{{T}} \\Pi(T) = \\sum_{{i: \\text{{PD}}_i < T, y_i = 0}} (\\text{{Margin}} \\times L_i) - \\sum_{{i: \\text{{PD}}_i < T, y_i = 1}} (\\text{{LGD}} \\times L_i)$$

3. **Marginal Approval Breakeven Condition**:
   At the marginal threshold $T^*$, the expected profit on an applicant is zero:
   $$T^* \\times \\text{{LGD}} = (1 - T^*) \\times \\text{{Margin}} \\implies T^* = \\frac{{\\text{{Margin}}}}{{\\text{{LGD}} + \\text{{Margin}}}} = \\frac{{0.08}}{{0.65 + 0.08}} \\approx 0.1096$$

---

## 3. Threshold Sample Curve

| Threshold | Approval Rate | Default Rate in Approvals | Total Revenue ($) | Total Default Loss ($) | Net Profit ($) | Expected Loss ($) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    # Sample ~10 representative threshold rows
    sample_indices = np.linspace(0, len(curve) - 1, 10, dtype=int)
    for idx in sample_indices:
        row = curve[idx]
        is_opt = " **(Optimal)**" if abs(row["threshold"] - opt["threshold"]) < 0.015 else ""
        md += f"| `{row['threshold']:.2f}`{is_opt} | {row['approval_rate'] * 100:.1f}% | {row['default_rate_approved'] * 100:.2f}% | ${row['total_revenue']:,.2f} | ${row['total_default_loss']:,.2f} | **${row['net_profit']:,.2f}** | ${row['total_expected_loss']:,.2f} |\n"

    md += f"""
---

## 4. Operational & Governance Guidelines

- **Live Scoring Safety**: Live decisioning defaults to band policy (`approve_below=0.15`, `decline_at_or_above=0.45`).
- **Activation**: To activate cost-optimized thresholds in production scoring, set `CS_DECISION_MODE=cost_based`.
- **Grounded Auditing**: Every scoring response includes `expected_loss` field for risk accounting without disrupting core decisioning.
"""

    report_path = rep_dir / "threshold_analysis.md"
    report_path.write_text(md, encoding="utf-8")
    return md, plot_path


def run_cost_optimization(settings: Any | None = None) -> dict:
    """Offline runner evaluating the test dataset and generating reports/threshold_analysis.md."""
    from .config import get_settings
    from .dataset import get_dataset
    from .features import pipeline as fp
    from .features.schema import TARGET
    from .models.registry import MlflowRegistry
    from sklearn.model_selection import train_test_split

    settings = settings or get_settings()
    df, _ = get_dataset(settings=settings, n=8000, seed=settings.seed)
    y = df[TARGET].to_numpy()
    X = fp.transform(df, mode=settings.data_source, use_behavioral=settings.use_behavioral)

    # Recreate test split identically
    _, X_test, _, y_test, _, _ = train_test_split(
        X, y, df["group"] if "group" in df.columns else np.zeros(len(df)),
        test_size=0.25, random_state=settings.seed, stratify=y
    )

    registry = MlflowRegistry(
        settings.mlflow_tracking_uri, settings.model_name, settings.mlflow_artifact_root
    )
    loaded_model = registry.load_latest()
    scores = loaded_model.predict_pd(X_test)

    # Loan amounts from original test rows
    test_idx = X_test.index
    loan_amounts = df.loc[test_idx, "loan_amount"].to_numpy() if "loan_amount" in df.columns else np.full(len(y_test), 15000.0)

    results = compute_profit_curve(
        y_true=y_test,
        y_score=scores,
        loan_amounts=loan_amounts,
        lgd=settings.lgd,
        interest_margin=settings.interest_margin,
        baseline_approve_below=settings.approve_below,
        baseline_decline_above=settings.decline_at_or_above,
    )

    reports_dir = Path(settings.data_dir).parent / "reports"
    generate_threshold_report(results, reports_dir, generate_plot=True)
    return results


def main() -> None:  # pragma: no cover
    res = run_cost_optimization()
    print(json.dumps({
        "status": "completed",
        "optimal": res["optimal"],
        "baseline": res["baseline"],
        "comparison": res["comparison"],
    }, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
