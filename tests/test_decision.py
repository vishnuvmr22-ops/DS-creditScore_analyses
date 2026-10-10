"""Slice 2 — decision policy (FR-10)."""

from __future__ import annotations

import pytest

from creditsentinel.decision import decide


def test_bands():
    assert decide(0.05, 0.15, 0.45) == "approve"
    assert decide(0.30, 0.15, 0.45) == "review"
    assert decide(0.60, 0.15, 0.45) == "decline"


def test_boundaries_inclusive():
    assert decide(0.15, 0.15, 0.45) == "review"  # approve is strict <
    assert decide(0.45, 0.15, 0.45) == "decline"  # decline is >=


def test_invalid_pd_raises():
    with pytest.raises(ValueError):
        decide(1.5, 0.15, 0.45)


def test_invalid_thresholds_raise():
    with pytest.raises(ValueError):
        decide(0.3, 0.6, 0.4)
