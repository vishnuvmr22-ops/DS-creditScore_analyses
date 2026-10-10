"""Slice 2 — reason grounding contract (FR-14/FR-16, constitution IV)."""

from __future__ import annotations

import pytest

from creditsentinel.explain.drivers import Driver
from creditsentinel.explain.reason import (
    GroundingError,
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


def test_template_decline_references_drivers():
    adapter = TemplateReasonAdapter()
    reason = adapter.generate("decline", _drivers(), [])
    assert reason.generator == "template"
    assert "debt-to-income ratio" in reason.text
    assert set(reason.grounded_in) <= {"debt_to_income", "num_delinquencies"}
    assert_grounded(reason, _drivers())  # must not raise


def test_template_includes_policy_refs():
    adapter = TemplateReasonAdapter()
    reason = adapter.generate(
        "decline", _drivers(), [PolicyPassage("risk-policy#adverse-action", "text")]
    )
    assert "risk-policy#adverse-action" in reason.policy_refs
    assert "risk-policy#adverse-action" in reason.text


def test_assert_grounded_rejects_non_driver_citation():
    bad = ReasonCode(text="declined due to debt-to-income ratio", grounded_in=["made_up_feature"])
    with pytest.raises(GroundingError):
        assert_grounded(bad, _drivers())


def test_assert_grounded_rejects_missing_driver_reference():
    bad = ReasonCode(text="declined for unspecified reasons", grounded_in=[])
    with pytest.raises(GroundingError):
        assert_grounded(bad, _drivers())


def test_approve_text_is_neutral():
    reason = TemplateReasonAdapter().generate("approve", _drivers(), [])
    assert "approved" in reason.text.lower()


def test_homecredit_plain_english_reasons_grounded():
    from creditsentinel.explain.reason import FEATURE_REASONS, get_plain_english_phrase

    homecredit_drivers = [
        Driver("EXT_SOURCE_2", "external bureau risk score 2", 0.35, "increases_risk"),
        Driver("credit_to_income", "credit to income ratio", 0.28, "increases_risk"),
        Driver("installment_late_ratio", "historical late payment frequency", 0.15, "increases_risk"),
        Driver("ext_sources_mean", "average external bureau score", -0.20, "decreases_risk"),
    ]

    adapter = TemplateReasonAdapter()

    # 1. Test decline reason code with Home Credit drivers
    decline_reason = adapter.generate("decline", homecredit_drivers, [])
    assert decline_reason.generator == "template"
    assert "external bureau risk score 2" in decline_reason.text
    assert "credit to income ratio" in decline_reason.text
    assert "historical late payment frequency" in decline_reason.text
    assert_grounded(decline_reason, homecredit_drivers)

    # 2. Test review reason code
    review_reason = adapter.generate("review", homecredit_drivers, [])
    assert "manual review" in review_reason.text
    assert_grounded(review_reason, homecredit_drivers)

    # 3. Test approve reason code
    approve_reason = adapter.generate("approve", homecredit_drivers, [])
    assert "approved" in approve_reason.text
    assert "average external bureau score" in approve_reason.text
    assert_grounded(approve_reason, homecredit_drivers)


def test_feature_reasons_dictionary_coverage():
    from creditsentinel.explain.reason import FEATURE_REASONS
    from creditsentinel.features.schema import (
        FEATURE_LABELS,
        HOMECREDIT_BEHAVIORAL_FIELDS,
        HOMECREDIT_NUMERIC_FIELDS,
        NUMERIC_FIELDS,
    )

    all_features = set(NUMERIC_FIELDS) | set(HOMECREDIT_NUMERIC_FIELDS) | set(HOMECREDIT_BEHAVIORAL_FIELDS)
    for feat in all_features:
        if feat in FEATURE_REASONS:
            assert "increases_risk" in FEATURE_REASONS[feat]
            assert "decreases_risk" in FEATURE_REASONS[feat]
            # Ensure the reason text contains the feature label so grounding never fails
            label = FEATURE_LABELS.get(feat, feat.replace("_", " "))
            inc_text = FEATURE_REASONS[feat]["increases_risk"].lower()
            dec_text = FEATURE_REASONS[feat]["decreases_risk"].lower()
            assert label.lower() in inc_text or feat.lower() in inc_text
            assert label.lower() in dec_text or feat.lower() in dec_text

