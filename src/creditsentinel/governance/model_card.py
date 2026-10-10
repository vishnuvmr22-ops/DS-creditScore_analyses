"""Auto-generated model card (FR-7, constitution III)."""

from __future__ import annotations

import json
from datetime import UTC, datetime


def build_model_card(
    model_name: str,
    model_version: str | int,
    feature_pipeline_version: str,
    metrics: dict,
    fairness: dict,
    dataset_provenance: str,
    n_train: int,
    n_test: int,
    fairness_extended: dict | None = None,
    mitigation_experiment: dict | None = None,
) -> str:
    """Render a markdown model card for a registered version."""
    cal = metrics.get("calibration", {})
    ece = cal.get("expected_calibration_error", "n/a")

    card_sections = [
        f"""# Model Card — {model_name} v{model_version}

_Generated {datetime.now(UTC).isoformat(timespec="seconds")}_

## Intended use
Estimate probability of default (PD) for a credit applicant in a **portfolio /
demonstration** context. Not for real lending decisions. Outputs feed a decision
policy (approve / decline / review) and a grounded adverse-action reason code.

## Data provenance
{dataset_provenance}

- Training rows: {n_train}
- Test rows: {n_test}
- Feature pipeline version: `{feature_pipeline_version}`

## Performance metrics (test set)
| Metric | Value |
| --- | --- |
| AUC-ROC | {metrics["auc_roc"]:.4f} |
| KS | {metrics["ks"]:.4f} |
| Brier | {metrics["brier"]:.4f} |
| Expected calibration error | {ece if isinstance(ece, str) else f"{ece:.4f}"} |
"""
    ]

    # Core Fairness Gate Parity
    card_sections.append(
        f"""## Fairness (approval-rate parity across protected attribute)
- Approval rate by group: {json.dumps(fairness["approval_rate_by_group"])}
- Parity gap (max−min): {fairness["parity_gap"]:.4f}
- Disparate-impact ratio (min/max): {fairness["disparate_impact_ratio"]:.4f}

The protected attribute is used only to compute this metric and is never a model
feature.
"""
    )

    # Extended Fairlearn Audit Section
    if fairness_extended:
        largest = fairness_extended.get("largest_gaps", {})
        ext_md = [
            "## Extended Fairlearn Audit (Multidimensional Demographic Analysis)",
            "Audited using Fairlearn `MetricFrame` across demographic dimensions (gender, age group, region rating).",
            "",
            "### Largest Demographic Gaps",
            f"- **Largest Selection (Approval) Rate Gap**: `{largest.get('selection_rate', 0.0):.4f}`",
            f"- **Largest False Positive Rate (FPR) Gap**: `{largest.get('false_positive_rate', 0.0):.4f}` (good applicants declined)",
            f"- **Largest False Negative Rate (FNR) Gap**: `{largest.get('false_negative_rate', 0.0):.4f}` (bad applicants approved)",
            "",
            "### Metrics by Demographic Dimension",
        ]
        by_dim = fairness_extended.get("by_dimension", {})
        for dim_name, dim_data in by_dim.items():
            ext_md.append(f"#### Dimension: `{dim_name}`")
            ext_md.append("| Subgroup | Selection Rate (Approval) | False Positive Rate (FPR) | False Negative Rate (FNR) |")
            ext_md.append("| --- | --- | --- | --- |")
            bg = dim_data.get("by_group", {})
            groups = sorted(bg.get("selection_rate", {}).keys())
            for g in groups:
                sr = bg.get("selection_rate", {}).get(g, 0.0)
                fpr = bg.get("false_positive_rate", {}).get(g, 0.0)
                fnr = bg.get("false_negative_rate", {}).get(g, 0.0)
                ext_md.append(f"| {g} | {sr:.4f} | {fpr:.4f} | {fnr:.4f} |")
            ext_md.append("")
        card_sections.append("\n".join(ext_md))

    # Offline Mitigation Experiment Section
    if mitigation_experiment:
        before = mitigation_experiment.get("before", {})
        after = mitigation_experiment.get("after", {})
        mit_md = [
            "## Offline Fairness Mitigation Experiment (Threshold Optimization)",
            "> **NOTICE**: This is an offline simulation report only. Live scoring policy uses a uniform threshold.",
            "",
            f"- **Unmitigated Global Threshold**: `{mitigation_experiment.get('unmitigated_threshold', 0.45):.4f}`",
            f"- **Optimized Per-Group Thresholds**: `{json.dumps(mitigation_experiment.get('mitigated_thresholds_by_group', {}))}`",
            f"- **Disparity Gap Before**: `{before.get('disparity_gap', 0.0):.4f}`",
            f"- **Disparity Gap After**: `{after.get('disparity_gap', 0.0):.4f}`",
            f"- **Disparity Reduction**: `{mitigation_experiment.get('disparity_reduction_pct', 0.0):.1f}%`",
            "",
            "### Before vs. After Comparison",
            "| Subgroup | Before Approval Rate | After Approval Rate | Before FPR | After FPR |",
            "| --- | --- | --- | --- | --- |",
        ]
        groups = sorted(before.get("approval_rates", {}).keys())
        for g in groups:
            b_ar = before.get("approval_rates", {}).get(g, 0.0)
            a_ar = after.get("approval_rates", {}).get(g, 0.0)
            b_fpr = before.get("fpr_by_group", {}).get(g, 0.0)
            a_fpr = after.get("fpr_by_group", {}).get(g, 0.0)
            mit_md.append(f"| {g} | {b_ar:.4f} | {a_ar:.4f} | {b_fpr:.4f} | {a_fpr:.4f} |")
        mit_md.append("")
        card_sections.append("\n".join(mit_md))

    # Limitations
    card_sections.append(
        """## Limitations
- Trained on synthetic/demonstration data; absolute metric values reflect the dataset
  distribution, not unconstrained live lending performance.
- Mitigation post-processing is recorded for offline audit and risk analysis; threshold
  adjustments must satisfy legal and compliance requirements before online deployment.
- No temporal validation, no reject-inference, no macroeconomic stress testing.
"""
    )

    return "\n\n".join(card_sections)
