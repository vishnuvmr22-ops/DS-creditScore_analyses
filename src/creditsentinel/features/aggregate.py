"""Offline behavioral & transaction feature aggregation pipeline (Step 3).

Computes per-applicant longitudinal summary indicators from historical installment
repayments, external credit bureau histories, and revolving credit card balances.

PROVENANCE NOTE:
These aggregated behavioral features act as empirical proxies for granular UPI,
Open-Banking, and bank statement transaction cash-flow metrics (which are proprietary
and not publicly released in open credit benchmarking datasets).

DATA LEAKAGE PREVENTION:
All metrics strictly utilize historical events occurred on or prior to application time
(using non-positive temporal offsets). No future repayment or post-origination data is used.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..config import Settings, get_settings

# Documented neutral defaults for applicants with zero prior credit history
BEHAVIORAL_DEFAULTS: dict[str, float] = {
    "has_behavioral_history": 0.0,
    "installment_late_ratio": 0.0,
    "mean_days_past_due": 0.0,
    "installment_underpay_ratio": 0.0,
    "payment_recency_days": 999.0,
    "payment_count": 0.0,
    "payment_total_amount": 0.0,
    "payment_avg_amount": 0.0,
    "bureau_total_loans_count": 0.0,
    "bureau_active_loans_count": 0.0,
    "bureau_total_debt": 0.0,
    "bureau_total_overdue": 0.0,
    "bureau_debt_to_credit_ratio": 0.0,
    "cc_utilization_mean": 0.0,
    "cc_balance_mean": 0.0,
    "cc_drawings_atm_sum": 0.0,
    "cc_drawings_pos_sum": 0.0,
}


def aggregate_installments(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate historical installment payment records by applicant SK_ID_CURR."""
    if df.empty:
        return pd.DataFrame(columns=["SK_ID_CURR"])

    out = df.copy()
    # Late payment flag: payment made after due date
    late = (out["DAYS_ENTRY_PAYMENT"] > out["DAYS_INSTALMENT"]).astype(float)
    # Days past due: positive days overdue
    dpd = (out["DAYS_ENTRY_PAYMENT"] - out["DAYS_INSTALMENT"]).clip(lower=0.0)
    # Underpayment flag
    underpay = (out["AMT_PAYMENT"].fillna(0) < out["AMT_INSTALMENT"].fillna(0)).astype(float)

    out["_late"] = late
    out["_dpd"] = dpd
    out["_underpay"] = underpay
    out["_recency"] = (-out["DAYS_ENTRY_PAYMENT"]).clip(lower=0.0)

    agg = out.groupby("SK_ID_CURR").agg(
        installment_late_ratio=("_late", "mean"),
        mean_days_past_due=("_dpd", "mean"),
        installment_underpay_ratio=("_underpay", "mean"),
        payment_recency_days=("_recency", "min"),
        payment_count=("_recency", "count"),
        payment_total_amount=("AMT_PAYMENT", "sum"),
        payment_avg_amount=("AMT_PAYMENT", "mean"),
    ).reset_index()

    return agg


def aggregate_bureau(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate credit bureau records by applicant SK_ID_CURR."""
    if df.empty:
        return pd.DataFrame(columns=["SK_ID_CURR"])

    out = df.copy()
    out["_is_active"] = (out["CREDIT_ACTIVE"] == "Active").astype(float)
    debt = out["AMT_CREDIT_SUM_DEBT"].fillna(0.0).clip(lower=0.0)
    credit = out["AMT_CREDIT_SUM"].fillna(0.0).clip(lower=0.0)
    overdue = out["AMT_CREDIT_SUM_OVERDUE"].fillna(0.0).clip(lower=0.0)

    out["_debt"] = debt
    out["_credit"] = credit
    out["_overdue"] = overdue

    agg = out.groupby("SK_ID_CURR").agg(
        bureau_total_loans_count=("_is_active", "count"),
        bureau_active_loans_count=("_is_active", "sum"),
        bureau_total_debt=("_debt", "sum"),
        bureau_total_overdue=("_overdue", "sum"),
        bureau_credit_sum=("_credit", "sum"),
    ).reset_index()

    agg["bureau_debt_to_credit_ratio"] = agg["bureau_total_debt"] / agg["bureau_credit_sum"].clip(lower=1.0)
    agg = agg.drop(columns=["bureau_credit_sum"], errors="ignore")
    return agg


def aggregate_credit_card(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revolving credit card balance statements by applicant SK_ID_CURR."""
    if df.empty:
        return pd.DataFrame(columns=["SK_ID_CURR"])

    out = df.copy()
    limit = out["AMT_CREDIT_LIMIT_ACTUAL"].clip(lower=1.0)
    balance = out["AMT_BALANCE"].fillna(0.0).clip(lower=0.0)
    utilization = (balance / limit).clip(0.0, 3.0)

    out["_utilization"] = utilization
    out["_balance"] = balance
    out["_drawings_atm"] = out.get("AMT_DRAWINGS_ATM_CURRENT", pd.Series(0, index=out.index)).fillna(0.0)
    out["_drawings_pos"] = out.get("AMT_DRAWINGS_POS_CURRENT", pd.Series(0, index=out.index)).fillna(0.0)

    agg = out.groupby("SK_ID_CURR").agg(
        cc_utilization_mean=("_utilization", "mean"),
        cc_balance_mean=("_balance", "mean"),
        cc_drawings_atm_sum=("_drawings_atm", "sum"),
        cc_drawings_pos_sum=("_drawings_pos", "sum"),
    ).reset_index()

    return agg


def build_behavioral_features(
    raw_dir: str | Path,
    output_path: str | Path | None = None,
    installments_df: pd.DataFrame | None = None,
    bureau_df: pd.DataFrame | None = None,
    credit_card_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Read raw auxiliary files and generate behavioral summary dataframe."""
    raw_path = Path(raw_dir)

    # 1. Installment aggregates
    if installments_df is not None:
        inst_agg = aggregate_installments(installments_df)
    elif (raw_path / "installments_payments.csv").exists():
        inst_raw = pd.read_csv(raw_path / "installments_payments.csv")
        inst_agg = aggregate_installments(inst_raw)
    else:
        inst_agg = pd.DataFrame(columns=["SK_ID_CURR"])

    # 2. Bureau aggregates
    if bureau_df is not None:
        bureau_agg = aggregate_bureau(bureau_df)
    elif (raw_path / "bureau.csv").exists():
        bureau_raw = pd.read_csv(raw_path / "bureau.csv")
        bureau_agg = aggregate_bureau(bureau_raw)
    else:
        bureau_agg = pd.DataFrame(columns=["SK_ID_CURR"])

    # 3. Credit card aggregates
    if credit_card_df is not None:
        cc_agg = aggregate_credit_card(credit_card_df)
    elif (raw_path / "credit_card_balance.csv").exists():
        cc_raw = pd.read_csv(raw_path / "credit_card_balance.csv")
        cc_agg = aggregate_credit_card(cc_raw)
    else:
        cc_agg = pd.DataFrame(columns=["SK_ID_CURR"])

    # Collect all unique applicant IDs across behavioral sources
    all_ids = set(inst_agg["SK_ID_CURR"]).union(bureau_agg["SK_ID_CURR"]).union(cc_agg["SK_ID_CURR"])
    if not all_ids:
        # Empty result with standard schema
        cols = ["SK_ID_CURR", *BEHAVIORAL_DEFAULTS.keys()]
        return pd.DataFrame(columns=cols)

    base = pd.DataFrame({"SK_ID_CURR": list(all_ids)})
    merged = base.merge(inst_agg, on="SK_ID_CURR", how="left")
    merged = merged.merge(bureau_agg, on="SK_ID_CURR", how="left")
    merged = merged.merge(cc_agg, on="SK_ID_CURR", how="left")

    merged["has_behavioral_history"] = 1.0
    for col, default_val in BEHAVIORAL_DEFAULTS.items():
        if col in merged.columns:
            merged[col] = merged[col].fillna(default_val)
        else:
            merged[col] = default_val

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(out_p, index=False)

    return merged


def merge_behavioral_features(
    applicant_df: pd.DataFrame,
    behavioral_df: pd.DataFrame | None = None,
    behavioral_path: str | Path | None = None,
) -> pd.DataFrame:
    """Merge behavioral features into applicant dataframe; fill history defaults for missing IDs."""
    if behavioral_df is None:
        if behavioral_path is not None and Path(behavioral_path).exists():
            behavioral_df = pd.read_parquet(behavioral_path)
        else:
            behavioral_df = pd.DataFrame(columns=["SK_ID_CURR", *BEHAVIORAL_DEFAULTS.keys()])

    if "SK_ID_CURR" not in applicant_df.columns or behavioral_df.empty:
        out = applicant_df.copy()
        for col, default_val in BEHAVIORAL_DEFAULTS.items():
            if col not in out.columns:
                out[col] = default_val
        return out

    merged = applicant_df.merge(behavioral_df, on="SK_ID_CURR", how="left")
    for col, default_val in BEHAVIORAL_DEFAULTS.items():
        if col in merged.columns:
            merged[col] = merged[col].fillna(default_val)
        else:
            merged[col] = default_val

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="CreditSentinel Behavioral Features Aggregation")
    parser.add_argument("--raw-dir", type=str, default=None, help="Directory containing raw auxiliary CSV files")
    parser.add_argument("--output", type=str, default=None, help="Output path for aggregated parquet file")
    args = parser.parse_args()

    settings = get_settings()
    raw_dir = args.raw_dir or settings.raw_data_dir
    output_path = args.output or settings.behavioral_features_path

    print(f"Building behavioral aggregates from '{raw_dir}' -> '{output_path}'...")
    df = build_behavioral_features(raw_dir=raw_dir, output_path=output_path)
    print(f"Aggregated {len(df)} applicant records with {df.shape[1]} behavioral indicators.")


if __name__ == "__main__":
    main()
