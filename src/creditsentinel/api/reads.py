"""Read-only API surface for the operator console (FR-015..FR-020, AD-6).

A driving adapter, nothing more: it projects artifacts the system already
produced into HTTP. It computes no metric, evaluates no drift and — by
construction — offers no way to mutate models, policies, thresholds or audit
records (FR-022, constitution III). Every route here is a GET.

Missing artifacts are reported as a distinguishable "not produced" 404 carrying
the command that would create them, so the console can tell three states apart:
service unreachable, artifact absent, and genuine fault.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import Settings, get_settings
from ..models.registry import GovernanceReaderPort, MlflowRegistry
from ..monitoring.runs import DriftRunStorePort, JsonlDriftRunStore
from .audit import AuditReaderPort, JsonlAuditReader
from .schemas import (
    AuditPageOut,
    DecisionPolicyOut,
    DriftRunOut,
    GovernanceOut,
    ModelCardOut,
)

router = APIRouter(tags=["console"])


def _not_produced(artifact: str, remedy: str) -> HTTPException:
    """404 that says which artifact is missing and what would produce it (FR-020)."""
    return HTTPException(
        status_code=404,
        detail={"status": "not_produced", "artifact": artifact, "remedy": remedy},
    )


# --- Dependency seams (tests override these on the app) --------------------


def get_settings_dep() -> Settings:
    return get_settings()


def get_governance_reader(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> GovernanceReaderPort:
    return MlflowRegistry(
        settings.mlflow_tracking_uri, settings.model_name, settings.mlflow_artifact_root or None
    )


def get_drift_store(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> DriftRunStorePort:
    return JsonlDriftRunStore(settings.drift_runs_path)


def get_audit_reader(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> AuditReaderPort:
    return JsonlAuditReader(settings.audit_log_path)


# --- Routes ----------------------------------------------------------------


@router.get("/decision-policy", response_model=DecisionPolicyOut)
def decision_policy(
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> DecisionPolicyOut:
    return DecisionPolicyOut(
        approve_below=settings.approve_below,
        decline_at_or_above=settings.decline_at_or_above,
        top_n_drivers=settings.top_n_drivers,
        psi_cutoff=settings.psi_cutoff,
    )


@router.get("/governance", response_model=GovernanceOut)
def governance(
    reader: Annotated[GovernanceReaderPort, Depends(get_governance_reader)],
) -> GovernanceOut:
    try:
        record = reader.load_governance()
    except Exception as exc:  # noqa: BLE001 - absent registry surfaces as not_produced
        raise _not_produced(
            "governance", "run `uv run creditsentinel-train` to train and register a governed model"
        ) from exc
    return GovernanceOut(
        model_version=record.model_version,
        feature_pipeline_version=record.feature_pipeline_version,
        metrics=record.metrics,
        fairness=record.fairness,
    )


@router.get("/governance/model-card", response_model=ModelCardOut)
def model_card(
    reader: Annotated[GovernanceReaderPort, Depends(get_governance_reader)],
) -> ModelCardOut:
    try:
        version, content = reader.load_model_card()
    except Exception as exc:  # noqa: BLE001
        raise _not_produced(
            "model_card", "run `uv run creditsentinel-train` to train and register a governed model"
        ) from exc
    return ModelCardOut(model_version=version, content=content)


@router.get("/drift", response_model=DriftRunOut)
def drift(store: Annotated[DriftRunStorePort, Depends(get_drift_store)]) -> DriftRunOut:
    """The most recently *recorded* evaluation. Never computes one (FR-016a)."""
    try:
        record = store.latest()
    except FileNotFoundError as exc:
        raise _not_produced(
            "drift_run", "run `uv run creditsentinel-drift --scenario stable` to record one"
        ) from exc
    return DriftRunOut(**record)


@router.get("/audit", response_model=AuditPageOut)
def audit(
    reader: Annotated[AuditReaderPort, Depends(get_audit_reader)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
    limit: Annotated[int | None, Query(ge=1, le=200)] = None,
    decision: Literal["approve", "review", "decline"] | None = None,
) -> AuditPageOut:
    bounded = min(limit or settings.audit_read_default_limit, settings.audit_read_max_limit)
    try:
        entries = reader.recent(limit=bounded, decision=decision)
    except FileNotFoundError as exc:
        raise _not_produced(
            "audit_log", "score an applicant to create the decision audit trail"
        ) from exc
    return AuditPageOut(count=len(entries), entries=entries)
