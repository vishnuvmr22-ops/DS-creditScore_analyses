"""Deterministic, versioned feature pipeline (FR-2, AD-2).

Pure core: no I/O, no external deps beyond pandas/numpy. The same input at the
same ``FEATURE_PIPELINE_VERSION`` yields byte-identical features.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from .schema import (
    CATEGORICAL_FIELDS,
    HOMECREDIT_BEHAVIORAL_FIELDS,
    HOMECREDIT_CATEGORICAL_FIELDS,
    HOMECREDIT_NUMERIC_FIELDS,
    NUMERIC_FIELDS,
)

FEATURE_PIPELINE_VERSION = "2.0.0"


def _engineered_synthetic(df: pd.DataFrame) -> pd.DataFrame:
    """Deterministic engineered features for synthetic dataset."""
    out = pd.DataFrame(index=df.index)
    # Income relative to loan size (avoid div-by-zero deterministically).
    out["income_to_loan"] = df["annual_income"] / df["loan_amount"].clip(lower=1.0)
    # Binary flag: any delinquency.
    out["delinquency_flag"] = (df["num_delinquencies"] > 0).astype("float64")
    return out


def _engineered_homecredit(df: pd.DataFrame) -> pd.DataFrame:
    """Deterministic engineered features for Home Credit dataset."""
    out = pd.DataFrame(index=df.index)
    # Financial ratios with safe division bounds
    out["credit_to_income"] = df["loan_amount"] / df["annual_income"].clip(lower=1.0)
    out["annuity_to_income"] = df["annuity"] / df["annual_income"].clip(lower=1.0)
    out["goods_to_loan"] = df["goods_price"] / df["loan_amount"].clip(lower=1.0)
    # Tenure / demographic ratios
    out["employment_to_age"] = df["employment_length"] / df["age"].clip(lower=18.0)
    # External bureau scores composite mean
    e1 = df["EXT_SOURCE_1"].fillna(0.5)
    e2 = df["EXT_SOURCE_2"].fillna(0.5)
    e3 = df["EXT_SOURCE_3"].fillna(0.5)
    out["ext_sources_mean"] = (e1 + e2 + e3) / 3.0
    return out


def feature_names(mode: str = "synthetic", use_behavioral: bool = False) -> list[str]:
    """Ordered feature-matrix column names produced by :func:`transform`."""
    if mode == "homecredit":
        names = list(HOMECREDIT_NUMERIC_FIELDS)
        names += [
            "credit_to_income",
            "annuity_to_income",
            "goods_to_loan",
            "employment_to_age",
            "ext_sources_mean",
        ]
        if use_behavioral:
            names += list(HOMECREDIT_BEHAVIORAL_FIELDS)
        for field, cats in HOMECREDIT_CATEGORICAL_FIELDS.items():
            names += [f"{field}={c}" for c in cats]
        return names

    # Default: synthetic schema
    names = list(NUMERIC_FIELDS)
    names += ["income_to_loan", "delinquency_flag"]
    for field, cats in CATEGORICAL_FIELDS.items():
        names += [f"{field}={c}" for c in cats]
    return names



def _coerce_frame(data: pd.DataFrame | Mapping[str, Any]) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy()
    return pd.DataFrame([dict(data)])


def _detect_mode(df: pd.DataFrame, explicit_mode: str | None = None) -> str:
    if explicit_mode in ("homecredit", "synthetic"):
        return explicit_mode
    try:
        from ..config import get_settings

        ds = get_settings().data_source
        if ds in ("homecredit", "synthetic"):
            return ds
    except Exception:
        pass
    # Fallback to column-based detection
    cols_lower = {str(c).lower() for c in df.columns}
    if "ext_source_2" in cols_lower or "name_contract_type" in cols_lower or "amt_credit" in cols_lower:
        return "homecredit"
    return "synthetic"



def _normalize_homecredit_input(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names and defaults for Home Credit serving and training."""
    out = df.copy()

    # Map alias fields if present in serving request
    if "ext_source_1" in out.columns and "EXT_SOURCE_1" not in out.columns:
        out["EXT_SOURCE_1"] = out["ext_source_1"]
    if "ext_source_2" in out.columns and "EXT_SOURCE_2" not in out.columns:
        out["EXT_SOURCE_2"] = out["ext_source_2"]
    if "ext_source_3" in out.columns and "EXT_SOURCE_3" not in out.columns:
        out["EXT_SOURCE_3"] = out["ext_source_3"]
    if "days_id_publish" in out.columns and "DAYS_ID_PUBLISH" not in out.columns:
        out["DAYS_ID_PUBLISH"] = out["days_id_publish"]
    if "days_registration" in out.columns and "DAYS_REGISTRATION" not in out.columns:
        out["DAYS_REGISTRATION"] = out["days_registration"]
    if "cnt_children" in out.columns and "CNT_CHILDREN" not in out.columns:
        out["CNT_CHILDREN"] = out["cnt_children"]
    if "cnt_fam_members" in out.columns and "CNT_FAM_MEMBERS" not in out.columns:
        out["CNT_FAM_MEMBERS"] = out["cnt_fam_members"]
    if "region_population_relative" in out.columns and "REGION_POPULATION_RELATIVE" not in out.columns:
        out["REGION_POPULATION_RELATIVE"] = out["region_population_relative"]

    # Provide defaults for missing numeric columns
    defaults = {
        "age": 45.0,
        "annual_income": 60000.0,
        "employment_length": 5.0,
        "loan_amount": 15000.0,
        "annuity": 1000.0,
        "goods_price": 15000.0,
        "debt_to_income": 0.3,
        "EXT_SOURCE_1": 0.5,
        "EXT_SOURCE_2": 0.5,
        "EXT_SOURCE_3": 0.5,
        "DAYS_ID_PUBLISH": 2500.0,
        "DAYS_REGISTRATION": 4500.0,
        "CNT_CHILDREN": 0.0,
        "CNT_FAM_MEMBERS": 2.0,
        "REGION_POPULATION_RELATIVE": 0.02,
    }
    for col, val in defaults.items():
        if col not in out.columns:
            out[col] = val
        else:
            out[col] = out[col].fillna(val)

    # Defaults for categoricals
    cat_defaults = {
        "NAME_CONTRACT_TYPE": "Cash loans",
        "NAME_INCOME_TYPE": "Working",
        "NAME_EDUCATION_TYPE": "Secondary / secondary special",
        "NAME_FAMILY_STATUS": "Married",
        "NAME_HOUSING_TYPE": "House / apartment",
        "FLAG_OWN_CAR": "N",
        "FLAG_OWN_REALTY": "Y",
    }
    for col, val in cat_defaults.items():
        if col not in out.columns:
            out[col] = val
        else:
            out[col] = out[col].fillna(val)

    return out


def transform(
    data: pd.DataFrame | Mapping[str, Any],
    mode: str | None = None,
    use_behavioral: bool | None = None,
) -> pd.DataFrame:
    """Transform raw applicant rows into the ordered model feature matrix.

    Accepts a DataFrame (batch, training) or a single mapping (one applicant,
    serving). Deterministic: fixed column order, fixed categorical vocabularies,
    no randomness, no fitting on the input.
    """
    from .aggregate import BEHAVIORAL_DEFAULTS

    df = _coerce_frame(data)
    active_mode = _detect_mode(df, explicit_mode=mode)

    if active_mode == "homecredit":
        df = _normalize_homecredit_input(df)
        numeric = df[HOMECREDIT_NUMERIC_FIELDS].astype("float64")
        engineered = _engineered_homecredit(df)

        if use_behavioral is None:
            try:
                from ..config import get_settings

                use_behavioral = get_settings().use_behavioral or ("has_behavioral_history" in df.columns)
            except Exception:
                use_behavioral = "has_behavioral_history" in df.columns

        behavioral_block = None
        if use_behavioral:
            for b_col, b_def in BEHAVIORAL_DEFAULTS.items():
                if b_col not in df.columns:
                    df[b_col] = b_def
                else:
                    df[b_col] = df[b_col].fillna(b_def)
            behavioral_block = df[HOMECREDIT_BEHAVIORAL_FIELDS].astype("float64")

        cat_blocks = []
        for field, cats in HOMECREDIT_CATEGORICAL_FIELDS.items():
            raw = df[field].astype("string")
            block = pd.DataFrame(
                {f"{field}={c}": (raw == c).astype("float64") for c in cats},
                index=df.index,
            )
            cat_blocks.append(block)

        blocks = [numeric, engineered]
        if behavioral_block is not None:
            blocks.append(behavioral_block)
        blocks.extend(cat_blocks)

        features = pd.concat(blocks, axis=1)
        expected_cols = feature_names(mode="homecredit", use_behavioral=bool(use_behavioral))
        features = features[expected_cols]
        return features.reset_index(drop=True)


    # Synthetic transformation
    numeric = df[NUMERIC_FIELDS].astype("float64")
    engineered = _engineered_synthetic(df)

    cat_blocks = []
    for field, cats in CATEGORICAL_FIELDS.items():
        raw = df[field].astype("string")
        block = pd.DataFrame(
            {f"{field}={c}": (raw == c).astype("float64") for c in cats},
            index=df.index,
        )
        cat_blocks.append(block)

    features = pd.concat([numeric, engineered, *cat_blocks], axis=1)
    expected_cols = feature_names(mode="synthetic")
    features = features[expected_cols]
    return features.reset_index(drop=True)

