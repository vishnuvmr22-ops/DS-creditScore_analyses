"""Slice 6 — bounded, ordered, pseudonymized audit reads (FR-009, FR-017, FR-019)."""

from __future__ import annotations

import json

import pytest

from creditsentinel.api.audit import JsonlAuditReader, JsonlAuditSink


def _seed(path, n=5, decisions=None):
    sink = JsonlAuditSink(path)
    decisions = decisions or ["approve", "decline", "review", "decline", "approve"]
    for i in range(n):
        sink.append(
            {
                "applicant_id": f"pseudo_{i:012d}",
                "pd": 0.1 * i,
                "decision": decisions[i % len(decisions)],
                "model_version": "1",
                "feature_pipeline_version": "1.0.0",
                "drivers": [{"feature": "debt_to_income", "label": "debt-to-income ratio",
                             "shap": 1.0, "direction": "increases_risk"}],
                "reason_generator": "template",
            }
        )
    return path


def test_reads_newest_first(tmp_path):
    path = _seed(tmp_path / "audit.jsonl")
    entries = JsonlAuditReader(path).recent(limit=10)
    assert [round(e["pd"], 3) for e in entries] == [0.4, 0.3, 0.2, 0.1, 0.0]


def test_limit_bounds_the_result(tmp_path):
    path = _seed(tmp_path / "audit.jsonl")
    assert len(JsonlAuditReader(path).recent(limit=2)) == 2


def test_filter_is_applied_before_truncation(tmp_path):
    """"The 2 most recent declines" must mean that — not "declines among the 2 most recent"."""
    path = _seed(tmp_path / "audit.jsonl")
    entries = JsonlAuditReader(path).recent(limit=2, decision="decline")
    assert len(entries) == 2
    assert {e["decision"] for e in entries} == {"decline"}


def test_filter_narrows_to_matching_entries_only(tmp_path):
    path = _seed(tmp_path / "audit.jsonl")
    entries = JsonlAuditReader(path).recent(limit=50, decision="approve")
    assert entries and all(e["decision"] == "approve" for e in entries)


def test_empty_result_is_not_an_error(tmp_path):
    path = _seed(tmp_path / "audit.jsonl", decisions=["approve"] * 5)
    assert JsonlAuditReader(path).recent(limit=10, decision="decline") == []


def test_missing_log_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        JsonlAuditReader(tmp_path / "nothing.jsonl").recent(limit=10)


def test_malformed_lines_are_skipped(tmp_path):
    path = _seed(tmp_path / "audit.jsonl", n=2)
    with path.open("a", encoding="utf-8") as f:
        f.write("this is not json\n")
    entries = JsonlAuditReader(path).recent(limit=10)
    assert len(entries) == 2


def test_never_returns_a_raw_identifier(tmp_path):
    """The guarantee comes from what the writer omits; this proves the reader keeps it."""
    path = _seed(tmp_path / "audit.jsonl")
    entries = JsonlAuditReader(path).recent(limit=50)
    blob = json.dumps(entries)
    assert "APP-" not in blob
    assert all(e["applicant_id"].startswith("pseudo_") for e in entries)
