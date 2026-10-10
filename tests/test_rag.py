"""Tests for Policy Retriever Port and NullPolicyRetriever (Step 7 Part B)."""

from __future__ import annotations

from creditsentinel.explain.reason import PolicyPassage
from creditsentinel.rag.retriever import NullPolicyRetriever, PolicyRetrieverPort


def test_null_policy_retriever_satisfies_protocol():
    retriever: PolicyRetrieverPort = NullPolicyRetriever()
    passages = retriever.retrieve("declined due to high debt-to-income ratio", k=3)
    assert isinstance(passages, list)
    assert len(passages) == 0


def test_scoring_with_policy_passages_attaches_refs(trained_model, settings, tmp_path, high_risk_applicant):
    from creditsentinel.api.audit import JsonlAuditSink
    from creditsentinel.api.redact import HashRedactor
    from creditsentinel.api.schemas import ScoreRequest
    from creditsentinel.api.service import ScoringService
    from creditsentinel.explain.drivers import ShapDriverExtractor
    from creditsentinel.explain.reason import TemplateReasonAdapter

    class _StubPolicyRetriever:
        def retrieve(self, query: str, k: int = 3) -> list[PolicyPassage]:
            return [PolicyPassage(ref="POL-DEBT-001", text="High debt to income ratio policy excerpt.")]

    svc = ScoringService(
        model=trained_model,
        extractor=ShapDriverExtractor(trained_model.model),
        reason_adapter=TemplateReasonAdapter(),
        retriever=_StubPolicyRetriever(),
        redactor=HashRedactor(),
        audit=JsonlAuditSink(str(tmp_path / "audit.jsonl")),
        settings=settings,
    )

    resp = svc.score(ScoreRequest(**high_risk_applicant))
    assert resp.decision == "decline"
    assert resp.reason_code.policy_refs == ["POL-DEBT-001"]
    assert "POL-DEBT-001" in resp.reason_code.text
