"""Slice 6 — the console cannot mutate governed state (FR-022, constitution III).

A UI that could retrain, re-register, re-threshold or rewrite audit history would
route around the governed-registration gate. This asserts the shape of the whole
mounted surface rather than trusting each endpoint's intent.
"""

from __future__ import annotations

from creditsentinel.api.app import app

_IDEMPOTENT = {"GET", "HEAD", "OPTIONS"}
# The single writing action in the system: scoring an applicant, which appends
# one pseudonymized audit entry. Everything else must be a read.
_ALLOWED_WRITES = {("/score", "POST")}


def _declared_routes() -> list[tuple[str, str]]:
    """Every path/verb pair the service publishes.

    Read from the generated OpenAPI document rather than by walking `app.routes`:
    routers mounted via `include_router` nest, and the published schema is the
    surface a client can actually discover and call.
    """
    paths = app.openapi()["paths"]
    return [(path, method.upper()) for path, ops in paths.items() for method in ops]


def test_score_is_the_only_non_idempotent_route():
    writes = {(p, m) for p, m in _declared_routes() if m not in _IDEMPOTENT}
    assert writes == _ALLOWED_WRITES, f"unexpected mutation surface: {writes - _ALLOWED_WRITES}"


def test_no_route_uses_a_mutating_verb_other_than_that_post():
    forbidden = {"PUT", "PATCH", "DELETE"}
    offending = [(p, m) for p, m in _declared_routes() if m in forbidden]
    assert offending == []


def test_every_console_read_endpoint_is_get_only():
    console_paths = {"/decision-policy", "/governance", "/governance/model-card", "/drift", "/audit"}
    for path, method in _declared_routes():
        if path in console_paths:
            assert method in _IDEMPOTENT, f"{path} exposes {method}"


def test_all_console_read_endpoints_are_actually_mounted():
    """Guards the assertion above from passing vacuously if the router is unregistered."""
    mounted = {p for p, _ in _declared_routes()}
    for path in ("/decision-policy", "/governance", "/governance/model-card", "/drift", "/audit"):
        assert path in mounted
