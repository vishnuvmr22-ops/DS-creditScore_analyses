"""Slice 4 — PSI drift job (FR-17)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from creditsentinel.monitoring.baseline import build_baseline
from creditsentinel.monitoring.drift import feature_psi, psi, run_drift


def test_psi_zero_for_identical_distribution():
    props = [0.2, 0.3, 0.5]
    assert psi(props, props) == 0.0


def test_psi_positive_for_shifted_distribution():
    assert psi([0.5, 0.3, 0.2], [0.1, 0.2, 0.7]) > 0.1


def _baseline_and_frame(seed=0):
    rng = np.random.default_rng(seed)
    ref = pd.DataFrame(
        {"debt_to_income": rng.normal(0.3, 0.1, 4000), "age": rng.normal(45, 10, 4000)}
    )
    scores = rng.beta(2, 5, 4000)
    return build_baseline(ref, scores), ref, scores


def test_feature_psi_small_for_same_distribution():
    baseline, ref, _ = _baseline_and_frame()
    val = feature_psi(ref["debt_to_income"].to_numpy(), baseline["features"]["debt_to_income"])
    assert val < 0.1


def test_run_drift_flags_injected_drift():
    baseline, ref, scores = _baseline_and_frame()
    drifted = ref.copy()
    drifted["debt_to_income"] = drifted["debt_to_income"] + 0.5  # strong covariate shift
    report = run_drift(drifted, baseline, cutoff=0.2, scores=scores)
    assert report["features"]["debt_to_income"]["breach"] is True
    assert "debt_to_income" in report["breached_features"]
    assert report["any_breach"] is True


def test_run_drift_stable_batch_not_flagged():
    baseline, ref, scores = _baseline_and_frame()
    rng = np.random.default_rng(1)
    stable = pd.DataFrame(
        {"debt_to_income": rng.normal(0.3, 0.1, 4000), "age": rng.normal(45, 10, 4000)}
    )
    report = run_drift(stable, baseline, cutoff=0.2, scores=scores)
    assert report["any_breach"] is False
    assert report["breached_features"] == []


def test_score_psi_reported():
    baseline, ref, scores = _baseline_and_frame()
    report = run_drift(ref, baseline, cutoff=0.2, scores=scores)
    assert "score" in report
    assert report["score"]["psi"] < 0.1


# --- Slice 6: recording a run must not change how the job behaves (FR-016) ---


def _run_main(monkeypatch, tmp_path, scenario: str):
    """Run the CLI against an isolated data dir, returning (exit_code, store_path)."""
    import json as _json

    from creditsentinel import config as config_module
    from creditsentinel.monitoring import drift as drift_module

    baseline, ref, scores = _baseline_and_frame()
    (tmp_path / "baseline_stats.json").write_text(_json.dumps(baseline), encoding="utf-8")

    settings = config_module.Settings(data_dir=str(tmp_path), psi_cutoff=0.2)
    monkeypatch.setattr(drift_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        drift_module,
        "_build_batch",
        lambda scenario, s, n=2000: (
            (ref.copy().assign(debt_to_income=ref["debt_to_income"] + 0.5), scores)
            if scenario == "drift"
            else (ref, scores)
        ),
    )
    monkeypatch.setattr("sys.argv", ["creditsentinel-drift", "--scenario", scenario])

    code = 0
    try:
        drift_module.main()
    except SystemExit as exc:
        code = exc.code
    return code, settings.drift_runs_path


def test_main_still_prints_the_report_and_exits_zero_when_stable(monkeypatch, tmp_path, capsys):
    code, _ = _run_main(monkeypatch, tmp_path, "stable")
    out = capsys.readouterr().out
    assert code == 0
    assert "No drift detected." in out
    assert '"any_breach": false' in out


def test_main_still_flags_and_exits_one_when_drifted(monkeypatch, tmp_path, capsys):
    code, _ = _run_main(monkeypatch, tmp_path, "drift")
    out = capsys.readouterr().out
    assert code == 1
    assert "DRIFT DETECTED" in out


def test_main_records_the_run_it_reported(monkeypatch, tmp_path, capsys):
    from creditsentinel.monitoring.runs import JsonlDriftRunStore

    _, store_path = _run_main(monkeypatch, tmp_path, "drift")
    capsys.readouterr()
    latest = JsonlDriftRunStore(store_path).latest()
    assert latest["scenario"] == "drift"
    assert latest["any_breach"] is True
    assert "debt_to_income" in latest["breached_features"]
