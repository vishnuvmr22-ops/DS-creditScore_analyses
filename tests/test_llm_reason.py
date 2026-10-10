"""Tests for deterministic reason generation without external LLM dependencies (Step 7 Part B)."""

from __future__ import annotations

from creditsentinel.explain.drivers import Driver
from creditsentinel.explain.reason import (
    PolicyPassage,
    ReasonCode,
    TemplateReasonAdapter,
    assert_grounded,
)


def _drivers():
    return [
        Driver("debt_to_income", "debt-to-income ratio", 0.41, "increases_risk"),
        Driver("num_delinquencies", "recent delinquencies", 0.22, "increases_risk"),
        Driver("annual_income", "annual income", -0.10, "decreases_risk"),
    ]


def test_template_adapter_grounded_generation():
    adapter = TemplateReasonAdapter()
    reason = adapter.generate(
        "decline",
        _drivers(),
        [PolicyPassage("risk-policy#affordability", "Affordability policy excerpt.")],
    )
    assert reason.generator == "template"
    assert "debt-to-income ratio" in reason.text
    assert "risk-policy#affordability" in reason.policy_refs
    assert_grounded(reason, _drivers())


def test_template_adapter_approve_grounded():
    adapter = TemplateReasonAdapter()
    reason = adapter.generate("approve", _drivers(), [])
    assert reason.generator == "template"
    assert "annual income" in reason.text
    assert_grounded(reason, _drivers())
