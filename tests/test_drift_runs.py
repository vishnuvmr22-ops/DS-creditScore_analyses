"""Slice 6 — drift evaluations are recorded durably (FR-016).

The job used to print and exit; nothing survived it. The console must show an
evaluation that actually ran, so runs are appended to a JSONL store and the
newest one is the last line.
"""

from __future__ import annotations

import json

import pytest

from creditsentinel.monitoring.runs import JsonlDriftRunStore

_REPORT = {
    "cutoff": 0.2,
    "features": {"debt_to_income": {"psi": 0.31, "breach": True}, "age": {"psi": 0.01, "breach": False}},
    "breached_features": ["debt_to_income"],
    "any_breach": True,
}


def test_record_returns_a_run_id_and_persists(tmp_path):
    store = JsonlDriftRunStore(tmp_path / "drift_runs.jsonl")
    run_id = store.record(_REPORT, scenario="drift")
    assert run_id
    latest = store.latest()
    assert latest["run_id"] == run_id
    assert latest["scenario"] == "drift"
    assert latest["any_breach"] is True
    assert latest["features"]["debt_to_income"]["psi"] == 0.31


def test_record_stamps_a_utc_timestamp(tmp_path):
    store = JsonlDriftRunStore(tmp_path / "drift_runs.jsonl")
    store.record(_REPORT, scenario="stable")
    ts = store.latest()["ts"]
    assert ts.endswith("+00:00")


def test_latest_is_the_most_recent_record(tmp_path):
    store = JsonlDriftRunStore(tmp_path / "drift_runs.jsonl")
    store.record({**_REPORT, "any_breach": True}, scenario="drift")
    second = store.record({**_REPORT, "any_breach": False, "breached_features": []}, scenario="stable")
    latest = store.latest()
    assert latest["run_id"] == second
    assert latest["scenario"] == "stable"
    assert latest["any_breach"] is False


def test_store_is_append_only(tmp_path):
    """History is the point of a monitoring artifact — earlier runs are never rewritten."""
    path = tmp_path / "drift_runs.jsonl"
    store = JsonlDriftRunStore(path)
    first = store.record(_REPORT, scenario="stable")
    store.record(_REPORT, scenario="drift")
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["run_id"] == first


def test_latest_raises_when_nothing_recorded(tmp_path):
    store = JsonlDriftRunStore(tmp_path / "nothing.jsonl")
    with pytest.raises(FileNotFoundError):
        store.latest()


def test_latest_tolerates_a_truncated_trailing_line(tmp_path):
    """A half-written last line must not take the drift view down."""
    path = tmp_path / "drift_runs.jsonl"
    store = JsonlDriftRunStore(path)
    good = store.record(_REPORT, scenario="stable")
    with path.open("a", encoding="utf-8") as f:
        f.write('{"run_id": "half-writ')
    assert store.latest()["run_id"] == good


def test_record_carries_no_applicant_data(tmp_path):
    """Drift is distributional; nothing applicant-level may enter the record."""
    store = JsonlDriftRunStore(tmp_path / "drift_runs.jsonl")
    store.record(_REPORT, scenario="stable")
    assert set(store.latest()) == {
        "run_id", "ts", "scenario", "cutoff", "features", "breached_features", "any_breach",
    }
