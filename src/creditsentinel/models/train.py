"""Training & governance orchestration entrypoint (FR-1..FR-7, AD-1, Step 4 & 5).

Generates/loads dataset, handles class imbalance, fits and compares Logistic Regression,
LightGBM, and XGBoost against a Bureau-only baseline, applies Isotonic Calibration,
computes comprehensive discrimination + calibration + fairness metrics (including Fairlearn
multidimensional audit and offline mitigation experiment), and registers the governed model
version to MLflow.
"""

from __future__ import annotations

import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from ..config import Settings, get_settings
from ..dataset import get_dataset, write_dataset
from ..features import pipeline as fp
from ..features.schema import PROTECTED_ATTRIBUTE, TARGET
from ..governance.fairness import (
    approval_rate_parity,
    extended_fairlearn_audit,
    mitigation_threshold_optimizer_experiment,
)
from ..governance.gate import GovernedModel
from ..governance.metrics import core_metrics
from ..governance.model_card import build_model_card
from ..monitoring.baseline import build_baseline
from .registry import MlflowRegistry


def _select_bureau_columns(columns: list[str]) -> list[str]:
    """Select bureau and external score columns for baseline comparison."""
    bureau_keywords = [
        "EXT_SOURCE",
        "ext_source",
        "bureau",
        "debt_to_income",
        "credit_utilization",
        "num_delinquencies",
        "num_open_accounts",
    ]
    b_cols = [c for c in columns if any(kw in c for kw in bureau_keywords)]
    return b_cols if b_cols else columns[:4]


def _build_sensitive_features_df(df: pd.DataFrame) -> pd.DataFrame:
    """Extract or standardize protected demographic attributes (gender, age_group, region_rating)."""
    n = len(df)
    
    # 1. Gender
    if "gender" in df.columns:
        gender = df["gender"].astype(str)
    elif "CODE_GENDER" in df.columns:
        gender = df["CODE_GENDER"].astype(str).replace({"XNA": "F"})
    elif "group" in df.columns:
        gender = df["group"].map({"A": "F", "B": "M"}).fillna("F")
    else:
        gender = pd.Series(["F"] * n)

    # 2. Age Group
    if "age_group" in df.columns:
        age_group = df["age_group"].astype(str)
    elif "age" in df.columns:
        bins = [18, 25, 35, 50, 65, 100]
        labels = ["<25", "25-34", "35-49", "50-64", "65+"]
        age_group = pd.cut(df["age"].astype(float), bins=bins, labels=labels, right=False).astype(str)
    else:
        age_group = pd.Series(["35-49"] * n)

    # 3. Region Rating
    if "region_rating" in df.columns:
        region_rating = df["region_rating"].astype(str)
    elif "REGION_RATING_CLIENT" in df.columns:
        region_rating = df["REGION_RATING_CLIENT"].fillna(2).astype(int).astype(str)
    else:
        region_rating = pd.Series(["2"] * n)

    return pd.DataFrame({
        "gender": gender.values,
        "age_group": age_group.values,
        "region_rating": region_rating.values,
    }, index=df.index)


def _format_markdown_report(report_data: dict, output_path: Path) -> str:
    """Generate and persist Markdown model comparison report."""
    md = f"""# CreditSentinel Model Evaluation & Benchmark Report

_Generated {pd.Timestamp.now().isoformat(timespec='seconds')}_

## 1. Candidate Model Benchmark

| Model Architecture | AUC-ROC | KS Statistic | Brier Score | PR-AUC | ECE |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Bureau-Only Baseline** | {report_data['bureau_baseline']['auc_roc']:.4f} | {report_data['bureau_baseline']['ks']:.4f} | {report_data['bureau_baseline']['brier']:.4f} | {report_data['bureau_baseline']['pr_auc']:.4f} | {report_data['bureau_baseline']['calibration']['expected_calibration_error']:.4f} |
| **Logistic Regression** | {report_data['logistic_regression']['auc_roc']:.4f} | {report_data['logistic_regression']['ks']:.4f} | {report_data['logistic_regression']['brier']:.4f} | {report_data['logistic_regression']['pr_auc']:.4f} | {report_data['logistic_regression']['calibration']['expected_calibration_error']:.4f} |
| **LightGBM** | {report_data['lightgbm']['auc_roc']:.4f} | {report_data['lightgbm']['ks']:.4f} | {report_data['lightgbm']['brier']:.4f} | {report_data['lightgbm']['pr_auc']:.4f} | {report_data['lightgbm']['calibration']['expected_calibration_error']:.4f} |
| **XGBoost (Primary)** | **{report_data['xgboost']['auc_roc']:.4f}** | **{report_data['xgboost']['ks']:.4f}** | **{report_data['xgboost']['brier']:.4f}** | **{report_data['xgboost']['pr_auc']:.4f}** | **{report_data['xgboost']['calibration']['expected_calibration_error']:.4f}** |

---

## 2. Bureau-Only Uplift Analysis

- **Baseline Model AUC**: `{report_data['bureau_baseline']['auc_roc']:.4f}`
- **Full Model AUC**: `{report_data['xgboost']['auc_roc']:.4f}`
- **Delta AUC Uplift**: `+{report_data['delta_auc']:.4f}`
- **Delta KS Uplift**: `+{report_data['delta_ks']:.4f}`

---

## 3. Probability Calibration (Isotonic)

- **Uncalibrated Brier Score**: `{report_data['xgboost']['brier']:.4f}`
- **Calibrated Brier Score**: `{report_data['calibrated']['brier']:.4f}`
- **Uncalibrated ECE**: `{report_data['xgboost']['calibration']['expected_calibration_error']:.4f}`
- **Calibrated ECE**: `{report_data['calibrated']['calibration']['expected_calibration_error']:.4f}`

---

## 4. Governed Model Fairness Gate

- **Approval Rate (Group A)**: `{report_data['fairness']['approval_rate_by_group'].get('A', 0.0):.4f}`
- **Approval Rate (Group B)**: `{report_data['fairness']['approval_rate_by_group'].get('B', 0.0):.4f}`
- **Parity Gap**: `{report_data['fairness']['parity_gap']:.4f}`
- **Disparate Impact Ratio**: `{report_data['fairness']['disparate_impact_ratio']:.4f}`
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    return md


def _format_fairness_markdown_report(
    fairness_extended: dict,
    mitigation_report: dict,
    output_path: Path,
) -> str:
    """Generate and persist detailed Fairlearn audit and mitigation report."""
    largest = fairness_extended.get("largest_gaps", {})
    before = mitigation_report.get("before", {})
    after = mitigation_report.get("after", {})

    lines = [
        "# CreditSentinel Multidimensional Fairness & Bias Audit Report",
        "",
        f"_Generated {pd.Timestamp.now().isoformat(timespec='seconds')}_",
        "",
        "## 1. Executive Summary & Audit Scope",
        "",
        "Audited using **Fairlearn `MetricFrame`** across 3 distinct demographic dimensions:",
        "- **Gender**: Female (`F`) vs. Male (`M`)",
        "- **Age Band**: `<25`, `25-34`, `35-49`, `50-64`, `65+`",
        "- **Region Rating**: Client regional rating tier (`1`, `2`, `3`)",
        "",
        "### Key Audit Findings",
        f"- **Largest Selection (Approval) Rate Gap**: `{largest.get('selection_rate', 0.0):.4f}`",
        f"- **Largest False Positive Rate (FPR) Gap**: `{largest.get('false_positive_rate', 0.0):.4f}` (creditworthy applicants declined)",
        f"- **Largest False Negative Rate (FNR) Gap**: `{largest.get('false_negative_rate', 0.0):.4f}` (defaulting applicants approved)",
        "",
        "---",
        "",
        "## 2. Granular Demographic Metric Breakdown",
        "",
    ]

    by_dim = fairness_extended.get("by_dimension", {})
    for dim_name, dim_data in by_dim.items():
        lines.append(f"### Dimension: `{dim_name}`")
        lines.append(f"- **Selection Rate Gap**: `{dim_data.get('selection_rate_gap', 0.0):.4f}`")
        lines.append(f"- **FPR Gap**: `{dim_data.get('fpr_gap', 0.0):.4f}` | **FNR Gap**: `{dim_data.get('fnr_gap', 0.0):.4f}`")
        lines.append("")
        lines.append("| Subgroup | Approval (Selection) Rate | False Positive Rate (FPR) | False Negative Rate (FNR) |")
        lines.append("| :--- | :---: | :---: | :---: |")
        bg = dim_data.get("by_group", {})
        groups = sorted(bg.get("selection_rate", {}).keys())
        for g in groups:
            sr = bg.get("selection_rate", {}).get(g, 0.0)
            fpr = bg.get("false_positive_rate", {}).get(g, 0.0)
            fnr = bg.get("false_negative_rate", {}).get(g, 0.0)
            lines.append(f"| **{g}** | {sr:.4f} | {fpr:.4f} | {fnr:.4f} |")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Offline Fairness Mitigation Experiment",
        "",
        "> **GOVERNANCE NOTICE**: This experiment evaluates post-processing threshold optimization to equalize approval rates.",
        "> This is strictly an **offline simulation report** and does **NOT** alter online production scoring logic.",
        "",
        f"- **Unmitigated Uniform Threshold**: `{mitigation_report.get('unmitigated_threshold', 0.45):.4f}`",
        f"- **Optimized Per-Group Thresholds**: `{json.dumps(mitigation_report.get('mitigated_thresholds_by_group', {}))}`",
        f"- **Disparity Gap Before**: `{before.get('disparity_gap', 0.0):.4f}`",
        f"- **Disparity Gap After**: `{after.get('disparity_gap', 0.0):.4f}`",
        f"- **Disparity Reduction**: `+{mitigation_report.get('disparity_reduction_pct', 0.0):.1f}%`",
        "",
        "### Before vs. After Mitigation Comparison",
        "| Subgroup | Unmitigated Approval Rate | Mitigated Approval Rate | Unmitigated FPR | Mitigated FPR |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])

    groups = sorted(before.get("approval_rates", {}).keys())
    for g in groups:
        b_ar = before.get("approval_rates", {}).get(g, 0.0)
        a_ar = after.get("approval_rates", {}).get(g, 0.0)
        b_fpr = before.get("fpr_by_group", {}).get(g, 0.0)
        a_fpr = after.get("fpr_by_group", {}).get(g, 0.0)
        lines.append(f"| **{g}** | {b_ar:.4f} | {a_ar:.4f} | {b_fpr:.4f} | {a_fpr:.4f} |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Remaining Disparities & Ethical Assessment",
        "",
        "- **Trade-offs**: Equalizing demographic selection rates via threshold optimization creates slight shifts in per-group False Positive Rates.",
        "- **Compliance**: In many jurisdictions (e.g., US ECOA / Regulation B), utilizing protected class status at decision time to apply disparate thresholds requires rigorous fair lending legal validation.",
        "- **Recommendation**: Maintain a single uniform score threshold for live scoring, while monitoring demographic metric slices continuously in the governance registry.",
        "",
    ])

    md = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    return md


def train_and_register(settings: Settings | None = None, n: int = 8000) -> dict:
    settings = settings or get_settings()
    rng_seed = settings.seed

    df, provenance = get_dataset(settings=settings, n=n, seed=rng_seed)
    if settings.data_source == "synthetic":
        write_dataset(settings.data_dir, n=n, seed=rng_seed)

    y = df[TARGET].to_numpy()
    groups = df[PROTECTED_ATTRIBUTE] if PROTECTED_ATTRIBUTE in df.columns else pd.Series(["A"] * len(df))
    sensitive_df = _build_sensitive_features_df(df)
    X = fp.transform(df, mode=settings.data_source, use_behavioral=settings.use_behavioral)

    # 1. Stratified Train / Test Split
    X_train_full, X_test, y_train_full, y_test, g_train, g_test, sf_train, sf_test = train_test_split(
        X, y, groups, sensitive_df, test_size=0.25, random_state=rng_seed, stratify=y
    )

    # 2. Split train into fit and calibration sets (80/20)
    X_train, X_calib, y_train, y_calib = train_test_split(
        X_train_full, y_train_full, test_size=0.20, random_state=rng_seed, stratify=y_train_full
    )

    # 3. Class Imbalance Weighting
    neg_count = np.sum(y_train == 0)
    pos_count = np.sum(y_train == 1)
    scale_pos_weight = float(neg_count / max(pos_count, 1))

    # 4. Bureau-Only Baseline Model
    bureau_cols = _select_bureau_columns(list(X.columns))
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    bureau_lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=rng_seed))
    bureau_lr.fit(X_train_full[bureau_cols].fillna(0), y_train_full)
    bureau_scores = bureau_lr.predict_proba(X_test[bureau_cols].fillna(0))[:, 1]
    bureau_metrics = core_metrics(y_test, bureau_scores)

    # 5. Full Logistic Regression Candidate
    lr = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=rng_seed, class_weight="balanced"))
    lr.fit(X_train_full.fillna(0), y_train_full)
    lr_scores = lr.predict_proba(X_test.fillna(0))[:, 1]
    lr_metrics = core_metrics(y_test, lr_scores)

    # 6. LightGBM Candidate
    lgb_params = {
        "n_estimators": 300,
        "max_depth": 4,
        "learning_rate": 0.05,
        "scale_pos_weight": scale_pos_weight,
        "random_state": rng_seed,
        "verbose": -1,
    }
    lgb_model = lgb.LGBMClassifier(**lgb_params)
    lgb_model.fit(X_train_full, y_train_full)
    lgb_scores = lgb_model.predict_proba(X_test)[:, 1]
    lgb_metrics = core_metrics(y_test, lgb_scores)

    # 7. XGBoost (Primary Production Model)
    xgb_params = {
        "n_estimators": 300,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "scale_pos_weight": scale_pos_weight,
        "random_state": rng_seed,
        "eval_metric": "logloss",
    }
    xgb_model = XGBClassifier(**xgb_params)
    xgb_model.fit(X_train_full, y_train_full)

    xgb_scores = xgb_model.predict_proba(X_test)[:, 1]
    xgb_metrics = core_metrics(y_test, xgb_scores)
    fairness = approval_rate_parity(g_test, xgb_scores, settings.decline_at_or_above)

    # 8. Fairlearn Extended Audit & Mitigation Experiment
    fairness_extended = extended_fairlearn_audit(
        y_true=y_test,
        y_score=xgb_scores,
        sensitive_features=sf_test,
        decline_at_or_above=settings.decline_at_or_above,
    )
    mitigation_experiment = mitigation_threshold_optimizer_experiment(
        y_true=y_test,
        y_score=xgb_scores,
        sensitive_feature=sf_test["gender"],
        decline_at_or_above=settings.decline_at_or_above,
    )

    # 9. Isotonic Calibration (3-fold cross-validation)
    calibrator = CalibratedClassifierCV(estimator=XGBClassifier(**xgb_params), method="isotonic", cv=3)
    calibrator.fit(X_train_full, y_train_full)
    calib_scores = calibrator.predict_proba(X_test)[:, 1]
    calib_metrics = core_metrics(y_test, calib_scores)

    # 10. Calculate Delta Uplift
    delta_auc = float(xgb_metrics["auc_roc"] - bureau_metrics["auc_roc"])
    delta_ks = float(xgb_metrics["ks"] - bureau_metrics["ks"])

    # 11. Persist Model Card and Governance Bundle
    card = build_model_card(
        model_name=settings.model_name,
        model_version="pending",
        feature_pipeline_version=fp.FEATURE_PIPELINE_VERSION,
        metrics=xgb_metrics,
        fairness=fairness,
        dataset_provenance=provenance,
        n_train=len(X_train_full),
        n_test=len(X_test),
        fairness_extended=fairness_extended,
        mitigation_experiment=mitigation_experiment,
    )

    bundle = GovernedModel(
        model=xgb_model,
        feature_pipeline_version=fp.FEATURE_PIPELINE_VERSION,
        metrics=xgb_metrics,
        fairness=fairness,
        model_card=card,
        params=xgb_params,
        n_train=len(X_train_full),
        n_test=len(X_test),
        fairness_extended=fairness_extended,
    )

    registry = MlflowRegistry(
        settings.mlflow_tracking_uri, settings.model_name, settings.mlflow_artifact_root
    )
    version = registry.register_governed(bundle)

    # 12. Write Baseline Distributions for PSI Monitoring
    train_scores = xgb_model.predict_proba(X_train_full)[:, 1]
    baseline = build_baseline(X_train_full, train_scores)
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    settings.baseline_stats_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    # 13. Save Evaluation & Fairness Reports
    report_data = {
        "bureau_baseline": bureau_metrics,
        "logistic_regression": lr_metrics,
        "lightgbm": lgb_metrics,
        "xgboost": xgb_metrics,
        "calibrated": calib_metrics,
        "delta_auc": delta_auc,
        "delta_ks": delta_ks,
        "fairness": fairness,
    }
    report_path = Path(settings.data_dir).parent / "reports" / "model_comparison.md"
    _format_markdown_report(report_data, report_path)

    fairness_report_path = Path(settings.data_dir).parent / "reports" / "fairness_audit.md"
    _format_fairness_markdown_report(fairness_extended, mitigation_experiment, fairness_report_path)

    return {
        "model_version": version,
        "feature_pipeline_version": fp.FEATURE_PIPELINE_VERSION,
        "metrics": {k: v for k, v in xgb_metrics.items() if k != "calibration"},
        "calibration_ece": xgb_metrics["calibration"]["expected_calibration_error"],
        "fairness": fairness,
        "fairness_extended": fairness_extended,
        "mitigation_experiment": mitigation_experiment,
        "baseline_auc": bureau_metrics["auc_roc"],
        "delta_auc": delta_auc,
        "delta_ks": delta_ks,
        "n_train": len(X_train_full),
        "n_test": len(X_test),
    }


def main() -> None:  # pragma: no cover - CLI wrapper
    result = train_and_register()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
