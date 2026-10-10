"""Central configuration (constitution: no magic numbers in core).

All tunables (thresholds, top-N drivers, PSI cutoff, model name, API key) resolve
from environment via pydantic-settings. Missing ANTHROPIC_API_KEY is NOT an error
(it selects the deterministic template reason adapter, AD-3/AD conventions).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo-root-relative default locations (overridable via env).
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CS_", env_file=".env", extra="ignore", populate_by_name=True
    )

    # --- Decision policy (FR-10, Step 6) ---
    # Calibrated to the PD distribution (Slice 1/2): ~34% approve, ~10% decline,
    # remainder to manual review. Tunable via env for expected-loss trade-offs.
    approve_below: float = 0.15
    decline_at_or_above: float = 0.45

    # --- Cost-Based Decisioning & Expected Loss Assumptions (Step 6) ---
    # Assumption 1: LGD (Loss Given Default) is 0.65 (65% unrecovered on default).
    # Assumption 2: Net interest margin is 0.08 (8% annual net spread over cost of funds).
    # Assumption 3: CS_DECISION_MODE selects between baseline bands ("bands") and
    #               cost-optimized thresholds ("cost_based").
    lgd: float = 0.65
    interest_margin: float = 0.08
    decision_mode: str = "bands"  # "bands" | "cost_based"
    cost_optimized_approve_below: float = 0.22
    cost_optimized_decline_at_or_above: float = 0.38

    # --- Explanation (FR-11) ---
    top_n_drivers: int = 3

    # --- Drift (FR-17) ---
    psi_cutoff: float = 0.20

    # --- Operator console (slice 006) ---
    # Origins allowed to call this service from a browser. Explicit list, never a
    # wildcard: the console is a known origin, not "anyone" (FR-021).
    cors_allow_origins: str = "http://localhost:3000"
    # Bounds on audit reads so a view can never ask for the whole history (FR-017).
    audit_read_default_limit: int = 50
    audit_read_max_limit: int = 200

    # --- Model registry (AD-1) ---
    # MLflow 3.x requires a database backend; SQLite keeps it zero-infra.
    model_name: str = "creditsentinel-pd"
    mlflow_tracking_uri: str = f"sqlite:///{(_REPO_ROOT / 'mlflow' / 'mlflow.db').as_posix()}"
    mlflow_artifact_root: str = (_REPO_ROOT / "mlflow" / "artifacts").as_uri()

    # --- Data / governance artifacts ---
    data_source: str = "synthetic"  # "synthetic" | "homecredit"
    use_behavioral: bool = False  # If True, merge behavioral transaction proxies
    data_dir: str = str(_REPO_ROOT / "data")
    raw_data_dir: str = str(_REPO_ROOT / "data" / "raw")
    processed_data_dir: str = str(_REPO_ROOT / "data" / "processed")
    audit_log_path: str = str(_REPO_ROOT / "data" / "audit_log.jsonl")

    # --- Reproducibility (constitution II) ---
    seed: int = 42

    @property
    def homecredit_raw_path(self) -> Path:
        return Path(self.raw_data_dir) / "application_train.csv"

    @property
    def behavioral_features_path(self) -> Path:
        return Path(self.processed_data_dir) / "behavioral.parquet"

    @property
    def baseline_stats_path(self) -> Path:

        return Path(self.data_dir) / "baseline_stats.json"

    @property
    def drift_runs_path(self) -> Path:
        """Append-only record of every drift evaluation that has run (FR-016)."""
        return Path(self.data_dir) / "drift_runs.jsonl"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def dataset_path(self) -> Path:
        return Path(self.data_dir) / "applicants.parquet"


@lru_cache
def get_settings() -> Settings:
    return Settings()
