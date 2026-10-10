"""Scoring service — composition root wiring core logic to adapters (AD-6, Step 7 Part B).

Orchestrates the full /score path: validate -> features -> PD -> decision ->
SHAP drivers -> grounded reason -> response + PII-safe audit log.
Uses deterministic TemplateReasonAdapter and NullPolicyRetriever (zero external LLM/vector store deps).
"""

from __future__ import annotations

from ..config import Settings, get_settings
from ..decision import decide
from ..explain.drivers import Driver, ShapDriverExtractor, risk_increasing
from ..explain.reason import ReasonCodePort, TemplateReasonAdapter, assert_grounded
from ..features import pipeline as fp
from ..models.registry import LoadedModel, MlflowRegistry
from ..rag.retriever import NullPolicyRetriever, PolicyRetrieverPort
from .audit import AuditSinkPort, JsonlAuditSink
from .redact import HashRedactor, RedactorPort
from .schemas import (
    DriverOut,
    ReasonCodeOut,
    ScoreRequest,
    ScoreResponse,
    Thresholds,
)


def _default_reason_adapter(settings: Settings) -> ReasonCodePort:
    """Deterministic, grounded template reason adapter (Step 7 Part B)."""
    return TemplateReasonAdapter()


class ScoringService:
    def __init__(
        self,
        model: LoadedModel,
        extractor: ShapDriverExtractor,
        reason_adapter: ReasonCodePort,
        retriever: PolicyRetrieverPort,
        redactor: RedactorPort,
        audit: AuditSinkPort,
        settings: Settings,
    ):
        self.model = model
        self.extractor = extractor
        self.reason_adapter = reason_adapter
        self.retriever = retriever
        self.redactor = redactor
        self.audit = audit
        self.settings = settings

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        reason_adapter: ReasonCodePort | None = None,
        retriever: PolicyRetrieverPort | None = None,
    ) -> ScoringService:
        settings = settings or get_settings()
        registry = MlflowRegistry(
            settings.mlflow_tracking_uri, settings.model_name, settings.mlflow_artifact_root
        )
        model = registry.load_latest()

        if retriever is None:
            retriever = NullPolicyRetriever()

        if reason_adapter is None:
            reason_adapter = _default_reason_adapter(settings)

        return cls(
            model=model,
            extractor=ShapDriverExtractor(model.model),
            reason_adapter=reason_adapter,
            retriever=retriever,
            redactor=HashRedactor(),
            audit=JsonlAuditSink(settings.audit_log_path),
            settings=settings,
        )

    def _query(self, decision: str, drivers: list[Driver]) -> str:
        risk = risk_increasing(drivers) or drivers
        return f"{decision} adverse action " + " ".join(d.label for d in risk[:3])

    def score(self, request: ScoreRequest) -> ScoreResponse:
        from ..cost import compute_expected_loss

        s = self.settings
        features = fp.transform(request.features_dict())
        pd_value = float(self.model.predict_pd(features)[0])

        # Select decision thresholds based on decision_mode
        if s.decision_mode == "cost_based":
            app_below = s.cost_optimized_approve_below
            dec_above = s.cost_optimized_decline_at_or_above
        else:
            app_below = s.approve_below
            dec_above = s.decline_at_or_above

        decision = decide(pd_value, app_below, dec_above)
        drivers = self.extractor.top_drivers(features, s.top_n_drivers)

        # Expected Loss computation (PD * LGD * loan_amount)
        loan_amt = getattr(request, "loan_amount", None)
        if loan_amt is None and "loan_amount" in request.features_dict():
            loan_amt = float(request.features_dict()["loan_amount"])

        expected_loss = (
            round(float(compute_expected_loss(pd_value, s.lgd, loan_amt)), 2)
            if loan_amt is not None
            else None
        )

        policy = self.retriever.retrieve(self._query(decision, drivers), k=s.top_n_drivers)
        reason = self.reason_adapter.generate(decision, drivers, policy)
        # Enforce grounding regardless of which reason adapter ran (constitution IV).
        assert_grounded(reason, drivers)

        pseudo_id = self.redactor.pseudonymize(request.applicant_id)
        audit_id = self.audit.append(
            {
                "applicant_id": pseudo_id,  # pseudonymized, never raw (AD-4)
                "pd": round(pd_value, 6),
                "decision": decision,
                "expected_loss": expected_loss,
                "model_version": self.model.model_version,
                "feature_pipeline_version": self.model.feature_pipeline_version,
                "drivers": [d.as_dict() for d in drivers],
                "reason_generator": reason.generator,
            }
        )

        return ScoreResponse(
            applicant_id=pseudo_id,
            pd=round(pd_value, 6),
            decision=decision,
            expected_loss=expected_loss,
            thresholds=Thresholds(
                approve_below=app_below, decline_at_or_above=dec_above
            ),
            model_version=self.model.model_version,
            feature_pipeline_version=self.model.feature_pipeline_version,
            drivers=[DriverOut(**d.as_dict()) for d in drivers],
            reason_code=ReasonCodeOut(**reason.as_dict()),
            audit_id=audit_id,
        )
