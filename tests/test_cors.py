"""Slice 6 — browser access is restricted to an explicit origin list (FR-021)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from creditsentinel.api import app as app_module


def _client(service):
    app_module.set_service(service)
    return TestClient(app_module.app)


def test_configured_origin_receives_cors_headers(service):
    client = _client(service)
    r = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_unlisted_origin_receives_no_cors_headers(service):
    """The browser — not the server — blocks it; the server simply withholds consent."""
    client = _client(service)
    r = client.get("/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_preflight_is_answered_for_a_configured_origin(service):
    client = _client(service)
    r = client.options(
        "/score",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_credentials_are_not_allowed(service):
    """No authentication exists, so allowing credentials would be security theatre."""
    client = _client(service)
    r = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.headers.get("access-control-allow-credentials") != "true"
