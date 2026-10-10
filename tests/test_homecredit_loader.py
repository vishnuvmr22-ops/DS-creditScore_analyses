"""Unit tests for Step 1 — Home Credit dataset loader, preprocessor, and fairness isolation."""

from __future__ import annotations

import numpy as np
import pytest

from creditsentinel.config import Settings
from creditsentinel.dataset import generate, get_dataset
from creditsentinel.features.pipeline import feature_names, transform
from creditsentinel.features.schema import TARGET
from creditsentinel.homecredit import (
    HOMECREDIT_PROVENANCE,
    create_sample_homecredit_df,
    load_homecredit,
    write_sample_homecredit_csv,
)


def test_create_sample_homecredit_df_schema():
    """Verify sample mock homecredit df contains required columns and valid default rate."""
    df = create_sample_homecredit_df(n=500, seed=42)
    assert len(df) == 500
    assert TARGET in df.columns
    # Check default rate is in reasonable empirical credit range (~4% - 15%)
    default_rate = df[TARGET].mean()
    assert 0.04 <= default_rate <= 0.15

    # Check key columns exist and have been cleaned
    assert "age" in df.columns
    assert "employment_length" in df.columns
    assert "debt_to_income" in df.columns
    assert "EXT_SOURCE_1" in df.columns
    assert "EXT_SOURCE_2" in df.columns
    assert "EXT_SOURCE_3" in df.columns

    # Verify DAYS_EMPLOYED anomaly (365243) was cleaned
    assert not (df["employment_length"] < 0).any()
    assert (df["age"] >= 18).all()


def test_load_homecredit_from_csv_fixture(tmp_path):
    """Verify load_homecredit reads raw CSV, cleans quirks, and derives fairness columns."""
    csv_path = tmp_path / "application_train.csv"
    write_sample_homecredit_csv(csv_path, n=200, seed=123)

    df = load_homecredit(csv_path)
    assert len(df) == 200
    assert TARGET in df.columns

    # Fairness columns must be created
    assert "gender" in df.columns
    assert "age_group" in df.columns
    assert "region_rating" in df.columns
    assert "group" in df.columns
    assert set(df["group"].unique()).issubset({"A", "B"})


def test_load_homecredit_missing_file_raises_filenotfound(tmp_path):
    """Missing raw CSV raises descriptive FileNotFoundError."""
    missing_path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError, match="Home Credit dataset not found"):
        load_homecredit(missing_path)


def test_get_dataset_defaults_to_synthetic(tmp_path):
    """Default Settings uses synthetic data generator."""
    settings = Settings(data_source="synthetic", data_dir=str(tmp_path))
    df, provenance = get_dataset(settings=settings, n=500, seed=42)
    assert len(df) == 500
    assert TARGET in df.columns
    assert "SYNTHETIC DATA" in provenance


def test_get_dataset_switches_to_homecredit(tmp_path):
    """Settings with data_source='homecredit' loads from homecredit_raw_path."""
    raw_dir = tmp_path / "raw"
    csv_path = raw_dir / "application_train.csv"
    write_sample_homecredit_csv(csv_path, n=150, seed=99)

    settings = Settings(
        data_source="homecredit",
        raw_data_dir=str(raw_dir),
        data_dir=str(tmp_path),
    )
    df, provenance = get_dataset(settings=settings)
    assert len(df) == 150
    assert "HOME CREDIT" in provenance
    assert TARGET in df.columns


def test_fairness_attributes_isolated_from_feature_names():
    """Hard Rule 7: sensitive demographics must NEVER be in model feature matrix."""
    model_features = feature_names()
    forbidden = ["gender", "CODE_GENDER", "age_group", "region_rating", "REGION_RATING_CLIENT", "group"]
    for attr in forbidden:
        assert attr not in model_features, f"Protected attribute '{attr}' leaked into model features!"
