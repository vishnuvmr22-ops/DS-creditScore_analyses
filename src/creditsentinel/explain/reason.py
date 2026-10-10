"""Reason-code port + deterministic template adapter (FR-14/FR-16, AD-3, Step 7).

Both the template adapter (here) and the Anthropic adapter (Slice 3) satisfy the
same grounding contract: the reason text is built from the ACTUAL top SHAP drivers
plus retrieved policy passages — never free-hallucinated. A grounding assertion is
enforced regardless of which adapter produced the text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .drivers import Driver, risk_increasing


# --------------------------------------------------------------------------
# Plain-English reason dictionary for SHAP risk drivers (Step 7)
# Covers core synthetic features, Home Credit bureau metrics, engineered ratios,
# and behavioral/transaction proxies.
# --------------------------------------------------------------------------
FEATURE_REASONS: dict[str, dict[str, str]] = {
    # 1. Synthetic & Shared Core Features
    "age": {
        "increases_risk": "applicant age risk profile",
        "decreases_risk": "established applicant age profile",
    },
    "annual_income": {
        "increases_risk": "limited annual income relative to debt obligations",
        "decreases_risk": "strong annual income stability",
    },
    "employment_length": {
        "increases_risk": "limited length of employment",
        "decreases_risk": "extended length of employment",
    },
    "debt_to_income": {
        "increases_risk": "elevated debt-to-income ratio",
        "decreases_risk": "favorable debt-to-income ratio",
    },
    "credit_utilization": {
        "increases_risk": "high credit utilization across revolving lines",
        "decreases_risk": "low credit utilization across revolving lines",
    },
    "num_delinquencies": {
        "increases_risk": "history of recent delinquencies",
        "decreases_risk": "clean record with zero recent delinquencies",
    },
    "num_open_accounts": {
        "increases_risk": "high number of open accounts",
        "decreases_risk": "well-managed number of open accounts",
    },
    "loan_amount": {
        "increases_risk": "large requested loan amount",
        "decreases_risk": "conservative requested loan amount",
    },
    "interest_rate": {
        "increases_risk": "high loan interest rate",
        "decreases_risk": "favorable loan interest rate",
    },
    "income_to_loan": {
        "increases_risk": "low income relative to loan size",
        "decreases_risk": "robust income relative to loan size",
    },
    "delinquency_flag": {
        "increases_risk": "presence of delinquencies",
        "decreases_risk": "clean payment history without delinquencies",
    },

    # 2. Home Credit External Bureau Risk Scores
    "EXT_SOURCE_1": {
        "increases_risk": "low external bureau risk score 1",
        "decreases_risk": "strong external bureau risk score 1",
    },
    "EXT_SOURCE_2": {
        "increases_risk": "low external bureau risk score 2",
        "decreases_risk": "strong external bureau risk score 2",
    },
    "EXT_SOURCE_3": {
        "increases_risk": "low external bureau risk score 3",
        "decreases_risk": "strong external bureau risk score 3",
    },
    "ext_source_1": {
        "increases_risk": "low external bureau risk score 1",
        "decreases_risk": "strong external bureau risk score 1",
    },
    "ext_source_2": {
        "increases_risk": "low external bureau risk score 2",
        "decreases_risk": "strong external bureau risk score 2",
    },
    "ext_source_3": {
        "increases_risk": "low external bureau risk score 3",
        "decreases_risk": "strong external bureau risk score 3",
    },
    "ext_sources_mean": {
        "increases_risk": "unfavorable average external bureau score",
        "decreases_risk": "strong average external bureau score",
    },

    # 3. Home Credit Financial Attributes & Ratios
    "annuity": {
        "increases_risk": "high loan annuity amount",
        "decreases_risk": "manageable loan annuity amount",
    },
    "goods_price": {
        "increases_risk": "high goods purchase price",
        "decreases_risk": "well-sized goods purchase price",
    },
    "credit_to_income": {
        "increases_risk": "high credit to income ratio",
        "decreases_risk": "healthy credit to income ratio",
    },
    "annuity_to_income": {
        "increases_risk": "high annuity to income ratio",
        "decreases_risk": "favorable annuity to income ratio",
    },
    "employment_to_age": {
        "increases_risk": "short employment tenure relative to age",
        "decreases_risk": "strong employment tenure relative to age",
    },
    "goods_to_loan": {
        "increases_risk": "goods price to loan ratio imbalance",
        "decreases_risk": "healthy goods price to loan ratio",
    },
    "days_id_publish": {
        "increases_risk": "recent identity document publication age",
        "decreases_risk": "established identity document publication age",
    },
    "DAYS_ID_PUBLISH": {
        "increases_risk": "recent identity document publication age",
        "decreases_risk": "established identity document publication age",
    },
    "days_registration": {
        "increases_risk": "recent address registration tenure",
        "decreases_risk": "established address registration tenure",
    },
    "DAYS_REGISTRATION": {
        "increases_risk": "recent address registration tenure",
        "decreases_risk": "established address registration tenure",
    },
    "cnt_children": {
        "increases_risk": "high number of children / dependent obligations",
        "decreases_risk": "favorable number of children",
    },
    "CNT_CHILDREN": {
        "increases_risk": "high number of children / dependent obligations",
        "decreases_risk": "favorable number of children",
    },
    "cnt_fam_members": {
        "increases_risk": "large family size obligations",
        "decreases_risk": "favorable family size",
    },
    "CNT_FAM_MEMBERS": {
        "increases_risk": "large family size obligations",
        "decreases_risk": "favorable family size",
    },
    "region_population_relative": {
        "increases_risk": "lower relative region population density",
        "decreases_risk": "high relative region population density",
    },
    "REGION_POPULATION_RELATIVE": {
        "increases_risk": "lower relative region population density",
        "decreases_risk": "high relative region population density",
    },

    # 4. Behavioral & Transaction Proxies (Installments, Bureau, Cards)
    "has_behavioral_history": {
        "increases_risk": "absence of historical credit repayment records",
        "decreases_risk": "verified presence of historical credit repayment records",
    },
    "installment_late_ratio": {
        "increases_risk": "elevated historical late payment frequency",
        "decreases_risk": "low historical late payment frequency",
    },
    "mean_days_past_due": {
        "increases_risk": "elevated average days past due on historical installments",
        "decreases_risk": "zero or minimal average days past due on historical installments",
    },
    "installment_underpay_ratio": {
        "increases_risk": "elevated historical installment underpayment rate",
        "decreases_risk": "consistent historical installment underpayment rate (low)",
    },
    "payment_recency_days": {
        "increases_risk": "extended days since most recent recorded repayment",
        "decreases_risk": "recent days since most recent recorded repayment",
    },
    "payment_count": {
        "increases_risk": "sparse total number of completed repayments",
        "decreases_risk": "substantial total number of completed repayments",
    },
    "payment_total_amount": {
        "increases_risk": "limited total historical repayment amount",
        "decreases_risk": "substantial total historical repayment amount",
    },
    "payment_avg_amount": {
        "increases_risk": "low average payment installment amount",
        "decreases_risk": "solid average payment installment amount",
    },
    "bureau_total_loans_count": {
        "increases_risk": "high total external loans on bureau",
        "decreases_risk": "moderate total external loans on bureau",
    },
    "bureau_active_loans_count": {
        "increases_risk": "high number of currently active external loans",
        "decreases_risk": "low number of currently active external loans",
    },
    "bureau_total_debt": {
        "increases_risk": "high total outstanding balance across credit bureau accounts",
        "decreases_risk": "low total outstanding balance across credit bureau accounts",
    },
    "bureau_total_overdue": {
        "increases_risk": "elevated total overdue amount across credit bureau accounts",
        "decreases_risk": "zero total overdue amount across credit bureau accounts",
    },
    "bureau_debt_to_credit_ratio": {
        "increases_risk": "high bureau debt to credit ratio",
        "decreases_risk": "low bureau debt to credit ratio",
    },
    "cc_utilization_mean": {
        "increases_risk": "high average revolving credit card balance utilization",
        "decreases_risk": "low average revolving credit card balance utilization",
    },
    "cc_balance_mean": {
        "increases_risk": "high average revolving credit card balance",
        "decreases_risk": "low average revolving credit card balance",
    },
    "cc_drawings_atm_sum": {
        "increases_risk": "high total cash ATM drawings on revolving credit",
        "decreases_risk": "minimal total cash ATM drawings on revolving credit",
    },
    "cc_drawings_pos_sum": {
        "increases_risk": "irregular total point-of-sale merchant spending on credit card",
        "decreases_risk": "steady total point-of-sale merchant spending on credit card",
    },
}


def get_plain_english_phrase(driver: Driver) -> str:
    """Return a plain-English explanation for a SHAP driver, strictly preserving the label for grounding."""
    feat = driver.feature
    direction = driver.direction
    if feat in FEATURE_REASONS and direction in FEATURE_REASONS[feat]:
        return FEATURE_REASONS[feat][direction]

    # Clean fallback embedding the exact driver label for grounding compliance
    qualifier = "elevated" if direction == "increases_risk" else "favorable"
    return f"{qualifier} {driver.label}"


@dataclass
class PolicyPassage:
    ref: str
    text: str


@dataclass
class ReasonCode:
    text: str
    grounded_in: list[str]  # feature names actually cited
    policy_refs: list[str] = field(default_factory=list)
    generator: str = "template"

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "grounded_in": self.grounded_in,
            "policy_refs": self.policy_refs,
            "generator": self.generator,
        }


class GroundingError(RuntimeError):
    """Raised when a reason code does not reference the actual top drivers."""


def assert_grounded(reason: ReasonCode, drivers: list[Driver]) -> None:
    """Guarantee the reason references the real top risk drivers (constitution IV).

    Requires at least one of the top risk-increasing driver labels to appear in the
    reason text, and every `grounded_in` feature to be a real driver.
    """
    driver_features = {d.feature for d in drivers}
    for feat in reason.grounded_in:
        if feat not in driver_features:
            raise GroundingError(f"reason cites non-driver feature '{feat}'")

    # The text must reference at least one ACTUAL top driver (any direction).
    text_lc = reason.text.lower()
    if not any(d.label.lower() in text_lc for d in drivers):
        raise GroundingError("reason text does not reference any actual top driver")


@runtime_checkable
class ReasonCodePort(Protocol):
    def generate(
        self,
        decision: str,
        drivers: list[Driver],
        policy: list[PolicyPassage],
    ) -> ReasonCode: ...


class TemplateReasonAdapter:
    """Deterministic, dependency-free reason generator (the graceful fallback)."""

    def generate(
        self,
        decision: str,
        drivers: list[Driver],
        policy: list[PolicyPassage],
    ) -> ReasonCode:
        policy_refs = [p.ref for p in policy]

        if decision == "approve":
            favorable = [d for d in drivers if d.direction == "decreases_risk"] or drivers
            cited = favorable[:2]
            factors = _join([get_plain_english_phrase(d) for d in cited])
            text = (
                f"Application approved. Estimated default risk is below the approval "
                f"threshold. Supporting factors included: {factors}."
            )
        else:
            risk = risk_increasing(drivers) or drivers
            cited = risk[:3]
            factors = _join([get_plain_english_phrase(d) for d in cited])
            if decision == "decline":
                text = (
                    f"Application declined. The primary factors increasing estimated default "
                    f"risk were: {factors}."
                )
            else:  # review
                text = (
                    f"Application routed to manual review. Notable risk factors were: {factors}."
                )

        if policy_refs:
            text += f" (Consistent with policy: {', '.join(policy_refs)}.)"

        return ReasonCode(
            text=text,
            grounded_in=[d.feature for d in cited],
            policy_refs=policy_refs,
            generator="template",
        )


def _join(labels: list[str]) -> str:
    if not labels:
        return "the applicant's overall risk profile"
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + f", and {labels[-1]}"
