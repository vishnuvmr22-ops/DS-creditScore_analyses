"""Slice 6 — the console's read-only API surface (FR-015..FR-020).

Every endpoint here is a projection of something the system already produced.
None of them computes, and none of them can be made to write.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from creditsentinel.api import app as app_module
from creditsentinel.api import reads
from creditsentinel.models.registry import GovernanceRecord

_METRICS = {
    "auc_roc": 0.683,
    "ks": 0.284,
    "brier": 0.173,
    "calibration": {
        "expected_calibration_error": 0.114,
        "bins": [
            {"bin": 0, "n": 317, "mean_pred": 0.0697, "observed": 0.0883},
            {"bin": 1, "n": 638, "mean_pred": 0.1477, "observed": 0.1661},
        ],
    },
}
_FAIRNESS = {
    "approval_rate_by_group": {"A": 0.879, "B": 0.897},
    "parity_gap": 0.0179,
    "disparate_impact_ratio": 0.98,
}
_DRIFT_RUN = {
    "run_id": "run-abc",
    "ts": "2026-07-21T10:12:03+00:00",
    "scenario": "stable",
    "cutoff": 0.2,
    "features": {
        "debt_to_income": {"psi": 0.013, "breach": False},
        "age": {"psi": 0.31, "breach": True},
    },
    "score": {"psi": 0.021, "breach": False},
    "breached_features": ["age"],
    "any_breach": True,
}
_AUDIT_ENTRY = {
    "audit_id": "d62b",
    "ts": "2026-07-18T02:05:27+00:00",
    "applicant_id": "pseudo_e6cae956dbeb",
    "pd": 0.762275,
    "decision": "decline",
    "model_version": "1",
    "feature_pipeline_version": "1.0.0",
    "drivers": [
        {"feature": "debt_to_income", "label": "debt-to-income ratio",
         "shap": 1.190659, "direction": "increases_risk"}
    ],
    "reason_generator": "template",
}


class _StubGovernance:
    def __init__(self, available=True):
        self.available = available

    def _check(self):
        if not self.available:
            raise RuntimeError("no registered model 'creditsentinel-pd'")

    def load_governance(self) -> GovernanceRecord:
        self._check()
        return GovernanceRecord(
            model_version="1",
            feature_pipeline_version="1.0.0",
            metrics=_METRICS,
            fairness=_FAIRNESS,
        )

    def load_model_card(self) -> tuple[str, str]:
        self._check()
        return "1", "# Model Card\nSYNTHETIC content"


class _StubDriftStore:
    def __init__(self, record=None):
        self.record_value = record
        self.reads = 0

    def latest(self) -> dict:
        self.reads += 1
        if self.record_value is None:
            raise FileNotFoundError("no drift runs recorded")
        return self.record_value


class _StubAuditReader:
    def __init__(self, entries=None):
        self.entries = entries
        self.calls = []

    def recent(self, limit: int, decision: str | None = None) -> list[dict]:
        if self.entries is None:
            raise FileNotFoundError("no audit log")
        self.calls.append((limit, decision))
        matched = [e for e in self.entries if decision is None or e["decision"] == decision]
        return matched[:limit]


@pytest.fixture
def client(service):
    app_module.set_service(service)
    app_module.app.dependency_overrides[reads.get_governance_reader] = lambda: _StubGovernance()
    app_module.app.dependency_overrides[reads.get_drift_store] = lambda: _StubDriftStore(_DRIFT_RUN)
    app_module.app.dependency_overrides[reads.get_audit_reader] = lambda: _StubAuditReader([_AUDIT_ENTRY])
    yield TestClient(app_module.app)
    app_module.app.dependency_overrides.clear()


def _override(dep, value):
    app_module.app.dependency_overrides[dep] = lambda: value


# --------------------------------------------------------------------------- policy


def test_decision_policy_exposes_the_active_configuration(client):
    body = client.get("/decision-policy").json()
    assert body["approve_below"] < body["decline_at_or_above"]
    assert body["top_n_drivers"] >= 1
    assert 0 < body["psi_cutoff"] < 1


def test_decision_policy_matches_what_score_echoes(client, low_risk_applicant):
    policy = client.get("/decision-policy").json()
    scored = client.post("/score", json=low_risk_applicant).json()
    assert scored["thresholds"]["approve_below"] == policy["approve_below"]
    assert scored["thresholds"]["decline_at_or_above"] == policy["decline_at_or_above"]


# ----------------------------------------------------------------------- governance


def test_governance_returns_metrics_calibration_and_fairness(client):
    body = client.get("/governance").json()
    assert body["model_version"] == "1"
    assert body["metrics"]["auc_roc"] == 0.683
    assert body["metrics"]["calibration"]["expected_calibration_error"] == 0.114
    assert len(body["metrics"]["calibration"]["bins"]) == 2
    assert body["fairness"]["approval_rate_by_group"] == {"A": 0.879, "B": 0.897}


def test_governance_version_agrees_with_health(client):
    assert client.get("/governance").json()["model_version"] == "1"


def test_governance_reports_not_produced_without_a_model(client):
    _override(reads.get_governance_reader, _StubGovernance(available=False))
    r = client.get("/governance")
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["status"] == "not_produced"
    assert detail["artifact"] == "governance"
    assert "creditsentinel-train" in detail["remedy"]


def test_model_card_is_served_verbatim(client):
    body = client.get("/governance/model-card").json()
    assert body["model_version"] == "1"
    assert body["content"] == "# Model Card\nSYNTHETIC content"


def test_model_card_reports_not_produced_without_a_model(client):
    _override(reads.get_governance_reader, _StubGovernance(available=False))
    r = client.get("/governance/model-card")
    assert r.status_code == 404
    assert r.json()["detail"]["artifact"] == "model_card"


# ---------------------------------------------------------------------------- drift


def test_drift_returns_the_recorded_evaluation(client):
    body = client.get("/drift").json()
    assert body["run_id"] == "run-abc"
    assert body["scenario"] == "stable"
    assert body["cutoff"] == 0.2
    assert body["breached_features"] == ["age"]
    assert body["any_breach"] is True
    assert body["score"]["psi"] == 0.021


def test_drift_read_never_computes(client):
    """Two reads with no job between them must return the identical record (FR-016a)."""
    first = client.get("/drift").json()
    second = client.get("/drift").json()
    assert first == second
    assert first["run_id"] == second["run_id"]


def test_drift_omits_score_when_no_model_was_loadable(client):
    record = {k: v for k, v in _DRIFT_RUN.items() if k != "score"}
    _override(reads.get_drift_store, _StubDriftStore(record))
    assert client.get("/drift").json()["score"] is None


def test_drift_reports_not_produced_when_nothing_recorded(client):
    _override(reads.get_drift_store, _StubDriftStore(None))
    r = client.get("/drift")
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert detail["status"] == "not_produced"
    assert detail["artifact"] == "drift_run"
    assert "creditsentinel-drift" in detail["remedy"]


def test_drift_breach_flags_agree_with_the_cutoff(client):
    body = client.get("/drift").json()
    breached = {f for f, v in body["features"].items() if v["psi"] >= body["cutoff"]}
    assert breached == set(body["breached_features"])


# ---------------------------------------------------------------------------- audit


def test_audit_returns_entries_with_a_count(client):
    body = client.get("/audit").json()
    assert body["count"] == len(body["entries"]) == 1
    entry = body["entries"][0]
    assert entry["applicant_id"].startswith("pseudo_")
    assert entry["decision"] == "decline"
    assert entry["drivers"][0]["feature"] == "debt_to_income"
    assert entry["reason_generator"] == "template"


def test_audit_applies_the_default_limit(client):
    reader = _StubAuditReader([_AUDIT_ENTRY])
    _override(reads.get_audit_reader, reader)
    client.get("/audit")
    assert reader.calls == [(50, None)]


def test_audit_passes_the_requested_limit_and_filter(client):
    reader = _StubAuditReader([_AUDIT_ENTRY])
    _override(reads.get_audit_reader, reader)
    client.get("/audit?limit=10&decision=decline")
    assert reader.calls == [(10, "decline")]


@pytest.mark.parametrize("limit", [0, -1, 201, 9999])
def test_audit_rejects_out_of_range_limits(client, limit):
    assert client.get(f"/audit?limit={limit}").status_code == 422


def test_audit_rejects_an_unknown_decision(client):
    assert client.get("/audit?decision=maybe").status_code == 422


def test_audit_empty_result_is_200_not_404(client):
    _override(reads.get_audit_reader, _StubAuditReader([]))
    r = client.get("/audit?decision=approve")
    assert r.status_code == 200
    assert r.json() == {"count": 0, "entries": []}


def test_audit_reports_not_produced_when_no_log_exists(client):
    _override(reads.get_audit_reader, _StubAuditReader(None))
    r = client.get("/audit")
    assert r.status_code == 404
    assert r.json()["detail"]["artifact"] == "audit_log"


def test_no_read_response_carries_a_raw_applicant_identifier(client, high_risk_applicant):
    """FR-019 — reads expose pseudonymized references and published figures only.

    Feature *names* legitimately appear (drift is distributional; audit records the
    drivers behind a decision). What must never appear is the identifier the caller
    submitted, or an applicant's own attribute values.
    """
    client.post("/score", json=high_risk_applicant)
    raw_id = high_risk_applicant["applicant_id"]
    for path in ("/decision-policy", "/governance", "/governance/model-card", "/drift", "/audit"):
        assert raw_id not in client.get(path).text


def test_audit_entries_expose_drivers_but_no_attribute_values(client):
    """Drivers are model output about a decision, not the applicant's submitted data."""
    entry = client.get("/audit").json()["entries"][0]
    assert set(entry) == {
        "audit_id", "ts", "applicant_id", "pd", "decision", "model_version",
        "feature_pipeline_version", "drivers", "reason_generator",
    }
    assert set(entry["drivers"][0]) == {"feature", "label", "shap", "direction"}
