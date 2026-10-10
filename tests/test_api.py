"""Slice 2 — /score endpoint end-to-end (FR-8..FR-12, FR-15) + driver-reference test."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from creditsentinel.api import app as app_module
from creditsentinel.api.schemas import ScoreRequest


def _client(service):
    app_module.set_service(service)
    return TestClient(app_module.app)


def test_health_reports_loaded_model(service):
    client = _client(service)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["model_loaded"] is True
    assert body["feature_pipeline_version"] == "1.0.0"


def test_score_valid_response_shape(service, low_risk_applicant):
    client = _client(service)
    r = client.post("/score", json=low_risk_applicant)
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {
        "applicant_id", "pd", "decision", "thresholds", "model_version",
        "feature_pipeline_version", "drivers", "reason_code", "audit_id",
    }
    assert 0.0 <= body["pd"] <= 1.0
    assert body["decision"] in {"approve", "decline", "review"}
    assert body["applicant_id"].startswith("pseudo_")  # FR-15 pseudonymized


def test_invalid_payload_returns_422(service, low_risk_applicant):
    client = _client(service)
    bad = dict(low_risk_applicant)
    bad["home_ownership"] = "CASTLE"  # not an allowed category
    r = client.post("/score", json=bad)
    assert r.status_code == 422


def test_missing_field_returns_422(service, low_risk_applicant):
    client = _client(service)
    bad = dict(low_risk_applicant)
    del bad["debt_to_income"]
    r = client.post("/score", json=bad)
    assert r.status_code == 422


def test_determinism(service, low_risk_applicant):
    client = _client(service)
    r1 = client.post("/score", json=low_risk_applicant).json()
    r2 = client.post("/score", json=low_risk_applicant).json()
    assert r1["pd"] == r2["pd"]
    assert r1["decision"] == r2["decision"]
    assert [d["feature"] for d in r1["drivers"]] == [d["feature"] for d in r2["drivers"]]


def test_high_risk_declines_with_grounded_reason(service, high_risk_applicant):
    """CI-critical: a decline always carries drivers AND a reason that references them."""
    client = _client(service)
    body = client.post("/score", json=high_risk_applicant).json()
    assert body["decision"] == "decline"
    assert len(body["drivers"]) >= 1
    reason_text = body["reason_code"]["text"].lower()
    # The reason must reference at least one actual top driver's label.
    labels = [d["label"].lower() for d in body["drivers"]]
    assert any(label in reason_text for label in labels)


def test_audit_log_is_pii_safe(service, high_risk_applicant, tmp_path):
    client = _client(service)
    client.post("/score", json=high_risk_applicant)
    # Read the audit sink used by the injected service.
    audit_path = service.audit._path
    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    entry = json.loads(lines[-1])
    assert entry["applicant_id"].startswith("pseudo_")
    assert "APP-HIGH-001" not in json.dumps(entry)  # raw id never logged


def test_features_dict_excludes_id():
    req = ScoreRequest(
        applicant_id="X", age=30, annual_income=50000, employment_length=3,
        debt_to_income=0.3, credit_utilization=0.4, num_delinquencies=0,
        num_open_accounts=5, loan_amount=10000, interest_rate=12.0,
        home_ownership="RENT", purpose="other",
    )
    assert "applicant_id" not in req.features_dict()
