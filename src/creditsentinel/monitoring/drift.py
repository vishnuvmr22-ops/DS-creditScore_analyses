"""PSI drift job (FR-17, AD-1).

Compares incoming feature/score distributions against the training baseline and
flags features whose PSI meets or exceeds the configured cutoff. Reads the baseline
(not the model registry); optionally loads the model to compute score PSI.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Settings, get_settings
from .runs import JsonlDriftRunStore

_EPS = 1e-6


def psi(expected_props: list[float], actual_props: list[float]) -> float:
    """Population Stability Index between two binned proportion vectors."""
    e = np.asarray(expected_props, dtype=float) + _EPS
    a = np.asarray(actual_props, dtype=float) + _EPS
    e = e / e.sum()
    a = a / a.sum()
    return float(np.sum((a - e) * np.log(a / e)))


def _actual_props(values: np.ndarray, edges: list[float]) -> list[float]:
    counts, _ = np.histogram(np.asarray(values, dtype=float), bins=np.array(edges))
    total = max(counts.sum(), 1)
    return (counts / total).tolist()


def feature_psi(values: np.ndarray, baseline_feature: dict) -> float:
    edges = baseline_feature["edges"]
    return psi(baseline_feature["props"], _actual_props(values, edges))


def run_drift(
    features: pd.DataFrame,
    baseline: dict,
    cutoff: float,
    scores: np.ndarray | None = None,
) -> dict:
    """Return a PSI report: per-feature PSI + breach flags, optional score PSI."""
    feat_report = {}
    for col, base in baseline["features"].items():
        if col not in features.columns:
            continue
        value = feature_psi(features[col].to_numpy(dtype=float), base)
        feat_report[col] = {"psi": round(value, 6), "breach": bool(value >= cutoff)}

    report = {
        "cutoff": cutoff,
        "features": feat_report,
        "breached_features": [c for c, r in feat_report.items() if r["breach"]],
    }
    if scores is not None and "score" in baseline:
        s_psi = psi(baseline["score"]["props"], _actual_props(scores, baseline["score"]["edges"]))
        report["score"] = {"psi": round(s_psi, 6), "breach": bool(s_psi >= cutoff)}

    report["any_breach"] = bool(report["breached_features"]) or report.get("score", {}).get(
        "breach", False
    )
    return report


def load_baseline(settings: Settings) -> dict:
    path = settings.baseline_stats_path
    if not Path(path).exists():
        raise FileNotFoundError(f"no baseline at {path}; run training first (creditsentinel-train)")
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _build_batch(scenario: str, settings: Settings, n: int = 2000):
    """Generate a monitoring batch of features (+ scores if a model is available)."""
    from ..dataset import generate
    from ..features import pipeline as fp

    df = generate(n=n, seed=settings.seed + 1)
    if scenario == "drift":
        # Inject a realistic covariate shift: applicants get riskier.
        df["debt_to_income"] = np.clip(df["debt_to_income"] + 0.35, 0, 2)
        df["credit_utilization"] = np.clip(df["credit_utilization"] + 0.40, 0, 3)
        df["num_delinquencies"] = df["num_delinquencies"] + 2
    features = fp.transform(df)
    scores = _maybe_scores(features, settings)
    return features, scores


def _maybe_scores(features: pd.DataFrame, settings: Settings) -> np.ndarray | None:
    try:
        from ..models.registry import MlflowRegistry

        model = MlflowRegistry(
            settings.mlflow_tracking_uri, settings.model_name, settings.mlflow_artifact_root
        ).load_latest()
        return model.predict_pd(features)
    except Exception:  # noqa: BLE001 - score PSI is optional
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="CreditSentinel PSI drift job")
    parser.add_argument("--scenario", choices=["stable", "drift"], default="stable")
    args = parser.parse_args()

    settings = get_settings()
    baseline = load_baseline(settings)
    features, scores = _build_batch(args.scenario, settings)
    report = run_drift(features, baseline, settings.psi_cutoff, scores)

    # Record the evaluation so the console can show a run that actually happened
    # (FR-016). Recording never changes what this job prints or how it exits.
    JsonlDriftRunStore(settings.drift_runs_path).record(report, scenario=args.scenario)

    print(json.dumps(report, indent=2))
    if report["any_breach"]:
        print(f"DRIFT DETECTED: {report['breached_features']}")
        raise SystemExit(1)
    print("No drift detected.")


if __name__ == "__main__":  # pragma: no cover
    main()
