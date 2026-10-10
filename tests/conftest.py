"""Shared fixtures: a real trained ScoringService without MLflow overhead."""

from __future__ import annotations

import pytest
from xgboost import XGBClassifier

from creditsentinel.api.audit import JsonlAuditSink
from creditsentinel.api.redact import HashRedactor
from creditsentinel.api.service import ScoringService
from creditsentinel.config import Settings
from creditsentinel.dataset import generate
from creditsentinel.explain.drivers import ShapDriverExtractor
from creditsentinel.explain.reason import TemplateReasonAdapter
from creditsentinel.features import pipeline as fp
from creditsentinel.features.schema import TARGET
from creditsentinel.models.registry import LoadedModel
from creditsentinel.rag.retriever import NullPolicyRetriever


@pytest.fixture(scope="session")
def trained_model() -> LoadedModel:
    df = generate(n=3000, seed=42)
    X = fp.transform(df)
    y = df[TARGET].to_numpy()
    model = XGBClassifier(
        n_estimators=120, max_depth=4, learning_rate=0.1, random_state=42, eval_metric="logloss"
    )
    model.fit(X, y)
    return LoadedModel(model=model, model_version="test", feature_pipeline_version="1.0.0")


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        approve_below=0.15,
        decline_at_or_above=0.45,
        top_n_drivers=3,
        audit_log_path=str(tmp_path / "audit.jsonl"),
    )


@pytest.fixture
def service(trained_model, settings, tmp_path) -> ScoringService:
    return ScoringService(
        model=trained_model,
        extractor=ShapDriverExtractor(trained_model.model),
        reason_adapter=TemplateReasonAdapter(),
        retriever=NullPolicyRetriever(),
        redactor=HashRedactor(),
        audit=JsonlAuditSink(str(tmp_path / "audit.jsonl")),
        settings=settings,
    )


@pytest.fixture
def low_risk_applicant() -> dict:
    return {
        "applicant_id": "APP-LOW-001",
        "age": 48,
        "annual_income": 140000,
        "employment_length": 20,
        "debt_to_income": 0.08,
        "credit_utilization": 0.05,
        "num_delinquencies": 0,
        "num_open_accounts": 6,
        "loan_amount": 8000,
        "interest_rate": 6.0,
        "home_ownership": "OWN",
        "purpose": "home_improvement",
    }


@pytest.fixture
def high_risk_applicant() -> dict:
    return {
        "applicant_id": "APP-HIGH-001",
        "age": 24,
        "annual_income": 21000,
        "employment_length": 0.5,
        "debt_to_income": 0.95,
        "credit_utilization": 1.4,
        "num_delinquencies": 6,
        "num_open_accounts": 14,
        "loan_amount": 42000,
        "interest_rate": 28.0,
        "home_ownership": "RENT",
        "purpose": "debt_consolidation",
    }
