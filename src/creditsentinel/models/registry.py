"""Model Registry port + MLflow adapter (AD-1, AD-5).

The offline pipeline is the only writer; the online API is read-only. Registration
runs through the governance gate so ungoverned models cannot be registered.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import mlflow
import numpy as np
import pandas as pd
from mlflow.tracking import MlflowClient

from ..governance.gate import GovernedModel, assert_governed


@dataclass
class LoadedModel:
    model: object
    model_version: str
    feature_pipeline_version: str

    def predict_pd(self, features: pd.DataFrame) -> np.ndarray:
        """Return PD in [0, 1] for a feature matrix."""
        proba = self.model.predict_proba(features)
        return np.asarray(proba)[:, 1]


@dataclass
class GovernanceRecord:
    """The governance artifacts logged for one registered model version.

    Read back verbatim — never recomputed. The registry is the system of record
    (constitution III), so the console shows what registration actually logged.
    """

    model_version: str
    feature_pipeline_version: str
    metrics: dict
    fairness: dict


class ModelRegistryPort(Protocol):
    def register_governed(self, bundle: GovernedModel) -> str: ...
    def load_latest(self) -> LoadedModel: ...


class GovernanceReaderPort(Protocol):
    def load_governance(self) -> GovernanceRecord: ...
    def load_model_card(self) -> tuple[str, str]: ...


class MlflowRegistry:
    """MLflow-backed implementation of :class:`ModelRegistryPort`."""

    def __init__(self, tracking_uri: str, model_name: str, artifact_root: str | None = None):
        self.model_name = model_name
        self.artifact_root = artifact_root
        # SQLite tracking backend needs its parent dir to exist.
        if tracking_uri.startswith("sqlite:///"):
            db_path = tracking_uri.replace("sqlite:///", "", 1)
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_registry_uri(tracking_uri)
        self._client = MlflowClient(tracking_uri=tracking_uri, registry_uri=tracking_uri)

    def _ensure_experiment(self) -> str:
        exp = self._client.get_experiment_by_name(self.model_name)
        if exp is not None:
            return exp.experiment_id
        kwargs = {"artifact_location": self.artifact_root} if self.artifact_root else {}
        return self._client.create_experiment(self.model_name, **kwargs)

    def register_governed(self, bundle: GovernedModel) -> str:
        # Gate BEFORE any registry write.
        assert_governed(bundle)

        mlflow.set_experiment(experiment_id=self._ensure_experiment())
        with mlflow.start_run() as run:
            mlflow.log_params(bundle.params)
            mlflow.set_tag("feature_pipeline_version", bundle.feature_pipeline_version)
            mlflow.log_metric("auc_roc", bundle.metrics["auc_roc"])
            mlflow.log_metric("ks", bundle.metrics["ks"])
            mlflow.log_metric("brier", bundle.metrics["brier"])
            mlflow.log_metric(
                "expected_calibration_error",
                bundle.metrics["calibration"]["expected_calibration_error"],
            )
            mlflow.log_metric("parity_gap", bundle.fairness["parity_gap"])
            mlflow.log_metric("disparate_impact_ratio", bundle.fairness["disparate_impact_ratio"])

            mlflow.log_text(bundle.model_card, "model_card.md")
            mlflow.log_text(json.dumps(bundle.metrics, indent=2), "metrics.json")
            mlflow.log_text(json.dumps(bundle.fairness, indent=2), "fairness.json")
            if getattr(bundle, "fairness_extended", None):
                mlflow.log_text(json.dumps(bundle.fairness_extended, indent=2), "fairness_extended.json")
                for k, v in bundle.fairness_extended.get("largest_gaps", {}).items():
                    mlflow.log_metric(f"fairlearn_max_gap_{k}", float(v))

            mlflow.sklearn.log_model(
                bundle.model,
                name="model",
                registered_model_name=self.model_name,
                serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
            )
            run_id = run.info.run_id

        # Resolve the registry version created for this run and tag it.
        version = self._version_for_run(run_id)
        self._client.set_model_version_tag(
            self.model_name, version, "feature_pipeline_version", bundle.feature_pipeline_version
        )
        return version

    def _version_for_run(self, run_id: str) -> str:
        versions = self._client.search_model_versions(f"name='{self.model_name}'")
        for v in versions:
            if v.run_id == run_id:
                return v.version
        # Fallback: highest version number.
        return str(max(int(v.version) for v in versions))

    def _latest_version(self):
        versions = self._client.search_model_versions(f"name='{self.model_name}'")
        if not versions:
            raise RuntimeError(
                f"no registered model '{self.model_name}'; run training first (creditsentinel-train)"
            )
        return max(versions, key=lambda v: int(v.version))

    def load_latest(self) -> LoadedModel:
        latest = self._latest_version()
        model = mlflow.sklearn.load_model(f"models:/{self.model_name}/{latest.version}")
        fpv = (latest.tags or {}).get("feature_pipeline_version", "unknown")
        return LoadedModel(
            model=model, model_version=str(latest.version), feature_pipeline_version=fpv
        )

    def _artifact_text(self, run_id: str, name: str) -> str:
        """Read one artifact logged on a run. Works against a local store or a server."""
        return mlflow.artifacts.load_text(f"runs:/{run_id}/{name}")

    def load_governance(self) -> GovernanceRecord:
        """Governance for the version that `load_latest()` serves (FR-015)."""
        latest = self._latest_version()
        return GovernanceRecord(
            model_version=str(latest.version),
            feature_pipeline_version=(latest.tags or {}).get(
                "feature_pipeline_version", "unknown"
            ),
            metrics=json.loads(self._artifact_text(latest.run_id, "metrics.json")),
            fairness=json.loads(self._artifact_text(latest.run_id, "fairness.json")),
        )

    def load_model_card(self) -> tuple[str, str]:
        latest = self._latest_version()
        return str(latest.version), self._artifact_text(latest.run_id, "model_card.md")
