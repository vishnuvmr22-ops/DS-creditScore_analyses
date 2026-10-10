"""Decision policy (FR-10, AD-2). Pure core — thresholds are injected config."""

from __future__ import annotations

from typing import Literal

Decision = Literal["approve", "decline", "review"]


def decide(pd: float, approve_below: float, decline_at_or_above: float) -> Decision:
    """Map a PD to a decision. Bands: approve < approve_below <= review < decline_at_or_above <= decline."""
    if not 0.0 <= pd <= 1.0:
        raise ValueError(f"pd out of range: {pd}")
    if approve_below > decline_at_or_above:
        raise ValueError("approve_below must be <= decline_at_or_above")
    if pd < approve_below:
        return "approve"
    if pd >= decline_at_or_above:
        return "decline"
    return "review"
