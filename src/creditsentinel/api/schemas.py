"""Request/response contracts (FR-8). Pydantic v2; invalid input -> HTTP 422."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..features.schema import CATEGORICAL_FIELDS

HomeOwnership = Literal["RENT", "OWN", "MORTGAGE"]
Purpose = Literal[
    "debt_consolidation", "credit_card", "home_improvement", "major_purchase", "other"
]
HomeCreditContractType = Literal["Cash loans", "Revolving loans"]
HomeCreditIncomeType = Literal["Working", "Commercial associate", "Pensioner", "State servant"]
HomeCreditEducation = Literal[
    "Higher education", "Secondary / secondary special", "Incomplete higher"
]
HomeCreditFamilyStatus = Literal["Married", "Single / not married", "Civil marriage", "Widow"]
HomeCreditHousing = Literal["House / apartment", "With parents", "Rented apartment"]
FlagYN = Literal["Y", "N"]

# Guard: keep Literals in sync with the canonical schema.
assert set(CATEGORICAL_FIELDS["home_ownership"]) == {"RENT", "OWN", "MORTGAGE"}


class ScoreRequest(BaseModel):
    applicant_id: str = Field(..., min_length=1, description="Pseudonymized before logging")
    age: float = Field(..., ge=18, le=120)
    annual_income: float = Field(..., ge=0)
    employment_length: float = Field(..., ge=0, le=60)
    loan_amount: float = Field(..., gt=0)
    debt_to_income: float = Field(..., ge=0, le=2)


    # Synthetic-mode fields (with defaults for Home Credit callers)
    credit_utilization: float = Field(default=0.45, ge=0, le=3)
    num_delinquencies: float = Field(default=0.0, ge=0)
    num_open_accounts: float = Field(default=9.0, ge=0)
    interest_rate: float = Field(default=13.0, ge=0, le=100)
    home_ownership: HomeOwnership = Field(default="RENT")
    purpose: Purpose = Field(default="debt_consolidation")

    # Home Credit mode fields (with validation bounds)
    ext_source_1: float | None = Field(default=None, ge=0.0, le=1.0, description="External bureau score 1")
    ext_source_2: float | None = Field(default=None, ge=0.0, le=1.0, description="External bureau score 2")
    ext_source_3: float | None = Field(default=None, ge=0.0, le=1.0, description="External bureau score 3")
    annuity: float | None = Field(default=None, ge=0.0, description="Loan annuity payment")
    goods_price: float | None = Field(default=None, ge=0.0, description="Goods purchase price")
    days_id_publish: float | None = Field(default=None, ge=0.0, description="Days since ID document published")
    days_registration: float | None = Field(default=None, ge=0.0, description="Days since address registration")
    cnt_children: float | None = Field(default=None, ge=0, le=20, description="Number of children")
    cnt_fam_members: float | None = Field(default=None, ge=1, le=25, description="Number of family members")
    region_population_relative: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Relative population density of client region"
    )
    contract_type: HomeCreditContractType | None = Field(default=None)
    income_type: HomeCreditIncomeType | None = Field(default=None)
    education_type: HomeCreditEducation | None = Field(default=None)
    family_status: HomeCreditFamilyStatus | None = Field(default=None)
    housing_type: HomeCreditHousing | None = Field(default=None)
    own_car: FlagYN | None = Field(default=None)
    own_realty: FlagYN | None = Field(default=None)

    def features_dict(self) -> dict:
        """Applicant fields only (no id, dropping None values) for the feature pipeline."""
        return {k: v for k, v in self.model_dump(exclude={"applicant_id"}).items() if v is not None}



class DriverOut(BaseModel):
    feature: str
    label: str
    shap: float
    direction: str


class ReasonCodeOut(BaseModel):
    text: str
    grounded_in: list[str]
    policy_refs: list[str]
    generator: str


class Thresholds(BaseModel):
    approve_below: float
    decline_at_or_above: float


class ScoreResponse(BaseModel):
    applicant_id: str  # pseudonymized
    pd: float
    decision: str
    thresholds: Thresholds
    model_version: str
    feature_pipeline_version: str
    drivers: list[DriverOut]
    reason_code: ReasonCodeOut
    audit_id: str
    expected_loss: float | None = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str | None = None
    feature_pipeline_version: str | None = None


# --------------------------------------------------------------------------
# Console read-only surface (slice 006, FR-015..FR-020).
# Every model below is a projection of something the system already produced;
# none of them is ever accepted as input.
# --------------------------------------------------------------------------

Decision = Literal["approve", "review", "decline"]


class DecisionPolicyOut(BaseModel):
    """Active policy configuration, so the console never hard-codes it (FR-018)."""

    approve_below: float
    decline_at_or_above: float
    top_n_drivers: int
    psi_cutoff: float


class CalibrationBinOut(BaseModel):
    bin: int
    n: int
    mean_pred: float
    observed: float


class CalibrationOut(BaseModel):
    expected_calibration_error: float
    bins: list[CalibrationBinOut]


class MetricsOut(BaseModel):
    auc_roc: float
    ks: float
    brier: float
    calibration: CalibrationOut


class FairnessOut(BaseModel):
    approval_rate_by_group: dict[str, float]
    parity_gap: float
    disparate_impact_ratio: float


class GovernanceOut(BaseModel):
    model_version: str
    feature_pipeline_version: str
    metrics: MetricsOut
    fairness: FairnessOut


class ModelCardOut(BaseModel):
    model_version: str
    content: str


class DriftFeatureOut(BaseModel):
    psi: float
    breach: bool


class DriftRunOut(BaseModel):
    run_id: str
    ts: str
    scenario: str
    cutoff: float
    features: dict[str, DriftFeatureOut]
    # Absent when no model was loadable when the job ran — not an error.
    score: DriftFeatureOut | None = None
    breached_features: list[str]
    any_breach: bool


class AuditEntryOut(BaseModel):
    audit_id: str
    ts: str
    applicant_id: str  # pseudonymized at write time; never a raw identifier
    pd: float
    decision: str
    model_version: str
    feature_pipeline_version: str
    drivers: list[DriverOut]
    reason_generator: str


class AuditPageOut(BaseModel):
    count: int
    entries: list[AuditEntryOut]
