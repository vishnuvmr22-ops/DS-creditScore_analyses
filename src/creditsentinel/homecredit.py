"""Home Credit Default Risk dataset loader and preprocessor (Step 1).

Loads and standardizes tabular credit application data from Home Credit
(data/raw/application_train.csv), isolates protected demographic attributes
(gender, age band, region rating) for fairness audits, cleans data anomalies
(e.g., DAYS_EMPLOYED == 365243), and maps the label to canonical TARGET ('default').
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .features.schema import TARGET

HOMECREDIT_PROVENANCE = (
    "HOME CREDIT DEFAULT RISK DATASET — sourced from application_train.csv. "
    "Cleaned of known anomalies (DAYS_EMPLOYED=365243 replaced with NaN/0). "
    "Sensitive demographic attributes (gender, age_group, region_rating) "
    "are preserved for fairness audits and strictly isolated from model features."
)

# Core raw columns selected from application_train.csv (15-25 meaningful features)
HOMECREDIT_RAW_COLUMNS = [
    # Identifiers & Target
    "SK_ID_CURR",
    "TARGET",
    # Sensitive / Fairness attributes (strictly isolated from model training matrix)
    "CODE_GENDER",
    "REGION_RATING_CLIENT",
    # External Credit bureau scores (top signal drivers in Home Credit)
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    # Financial amounts
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    # Temporal & Employment
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
    "DAYS_REGISTRATION",
    "DAYS_ID_PUBLISH",
    # Demographics & Family
    "CNT_CHILDREN",
    "CNT_FAM_MEMBERS",
    "REGION_POPULATION_RELATIVE",
    # Categoricals
    "NAME_CONTRACT_TYPE",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "FLAG_OWN_CAR",
    "FLAG_OWN_REALTY",
]


def _clean_homecredit_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Clean anomalies and create canonical fields."""
    out = df.copy()

    # 1. Target column mapping
    if "TARGET" in out.columns:
        out[TARGET] = out["TARGET"].astype(int)

    # 2. Anomaly handling: DAYS_EMPLOYED == 365243 represents unemployed / pensioner anomaly
    days_emp = out["DAYS_EMPLOYED"].copy()
    days_emp = days_emp.replace(365243, np.nan)
    # Convert negative days to positive years
    out["employment_length"] = (-days_emp / 365.25).clip(lower=0.0).fillna(0.0)

    # 3. DAYS_BIRTH -> positive age in years
    age_years = (-out["DAYS_BIRTH"] / 365.25).clip(lower=18.0, upper=100.0)
    out["age"] = age_years.round(1)

    # 4. Create fairness demographic columns
    # Age group
    bins = [18, 25, 35, 50, 65, 100]
    labels = ["<25", "25-34", "35-49", "50-64", "65+"]
    out["age_group"] = pd.cut(out["age"], bins=bins, labels=labels, right=False).astype(str)

    # Gender & Group mapping for governance compatibility
    gender = out["CODE_GENDER"].astype(str).replace({"XNA": "F"})
    out["gender"] = gender
    # Map to 'group' (A/B) for default fairness parity checks (Group A = Female, Group B = Male)
    out["group"] = gender.map({"F": "A", "M": "B"}).fillna("A")

    # Region rating
    if "REGION_RATING_CLIENT" in out.columns:
        out["region_rating"] = out["REGION_RATING_CLIENT"].fillna(2).astype(int).astype(str)
    else:
        out["region_rating"] = "2"

    # 5. Standardized aliases for core credit features
    out["annual_income"] = out["AMT_INCOME_TOTAL"].astype(float)
    out["loan_amount"] = out["AMT_CREDIT"].astype(float)
    out["annuity"] = out["AMT_ANNUITY"].fillna(out["AMT_CREDIT"] * 0.05).astype(float)

    # Financial ratio: debt-to-income equivalent (annuity to income ratio)
    out["debt_to_income"] = (out["annuity"] / out["annual_income"].clip(lower=1.0)).clip(0.0, 2.0)

    # External source fillna with median / 0.5 neutral value
    for ext_col in ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]:
        if ext_col in out.columns:
            out[ext_col] = out[ext_col].astype(float).fillna(0.5)

    return out


def load_homecredit(
    csv_path: str | Path,
    nrows: int | None = None,
    settings: Any | None = None,
) -> pd.DataFrame:
    """Load and preprocess Home Credit application CSV.

    When settings.use_behavioral is True, merges historical behavioral features from
    settings.behavioral_features_path.
    """
    from .config import get_settings
    from .features.aggregate import merge_behavioral_features

    settings = settings or get_settings()
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Home Credit dataset not found at '{path}'. "
            "Please place application_train.csv into data/raw/ or run with CS_DATA_SOURCE=synthetic."
        )

    available_cols = set(pd.read_csv(path, nrows=0).columns)
    usecols = [c for c in HOMECREDIT_RAW_COLUMNS if c in available_cols]

    df = pd.read_csv(path, usecols=usecols, nrows=nrows)
    cleaned = _clean_homecredit_frame(df)

    if getattr(settings, "use_behavioral", False):
        cleaned = merge_behavioral_features(
            cleaned,
            behavioral_path=getattr(settings, "behavioral_features_path", None),
        )

    return cleaned



def create_sample_homecredit_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic mock Home Credit DataFrame for tests and dry-runs."""
    rng = np.random.default_rng(seed)

    # Target default rate around ~8.07% (matching real Home Credit dataset)
    defaults = rng.choice([0, 1], size=n, p=[0.92, 0.08])

    raw_data = {
        "SK_ID_CURR": np.arange(100000, 100000 + n),
        "TARGET": defaults,
        "CODE_GENDER": rng.choice(["F", "M"], size=n, p=[0.65, 0.35]),
        "REGION_RATING_CLIENT": rng.choice([1, 2, 3], size=n, p=[0.15, 0.70, 0.15]),
        "EXT_SOURCE_1": rng.uniform(0.1, 0.9, size=n),
        "EXT_SOURCE_2": rng.uniform(0.1, 0.9, size=n),
        "EXT_SOURCE_3": rng.uniform(0.1, 0.9, size=n),
        "AMT_INCOME_TOTAL": rng.normal(160000, 50000, size=n).clip(30000, 500000),
        "AMT_CREDIT": rng.normal(500000, 200000, size=n).clip(50000, 1500000),
        "AMT_ANNUITY": rng.normal(25000, 10000, size=n).clip(3000, 80000),
        "AMT_GOODS_PRICE": rng.normal(450000, 180000, size=n).clip(45000, 1400000),
        "DAYS_BIRTH": -rng.integers(21 * 365, 68 * 365, size=n),
        "DAYS_EMPLOYED": rng.choice([-1500, -3000, -500, 365243], size=n, p=[0.4, 0.3, 0.2, 0.1]),
        "DAYS_REGISTRATION": -rng.integers(100, 10000, size=n),
        "DAYS_ID_PUBLISH": -rng.integers(100, 5000, size=n),
        "CNT_CHILDREN": rng.choice([0, 1, 2], size=n, p=[0.7, 0.2, 0.1]),
        "CNT_FAM_MEMBERS": rng.choice([1, 2, 3, 4], size=n, p=[0.2, 0.5, 0.2, 0.1]),
        "REGION_POPULATION_RELATIVE": rng.uniform(0.001, 0.07, size=n),
        "NAME_CONTRACT_TYPE": rng.choice(["Cash loans", "Revolving loans"], size=n, p=[0.9, 0.1]),
        "NAME_INCOME_TYPE": rng.choice(
            ["Working", "Commercial associate", "Pensioner", "State servant"],
            size=n,
            p=[0.5, 0.25, 0.15, 0.1],
        ),
        "NAME_EDUCATION_TYPE": rng.choice(
            ["Secondary / secondary special", "Higher education", "Incomplete higher"],
            size=n,
            p=[0.7, 0.25, 0.05],
        ),
        "NAME_FAMILY_STATUS": rng.choice(
            ["Married", "Single / not married", "Civil marriage", "Widow"],
            size=n,
            p=[0.6, 0.2, 0.1, 0.1],
        ),
        "NAME_HOUSING_TYPE": rng.choice(
            ["House / apartment", "With parents", "Rented apartment"], size=n, p=[0.85, 0.1, 0.05]
        ),
        "FLAG_OWN_CAR": rng.choice(["Y", "N"], size=n, p=[0.35, 0.65]),
        "FLAG_OWN_REALTY": rng.choice(["Y", "N"], size=n, p=[0.7, 0.3]),
    }
    df = pd.DataFrame(raw_data)
    return _clean_homecredit_frame(df)


def write_sample_homecredit_csv(csv_path: str | Path, n: int = 200, seed: int = 42) -> Path:
    """Write sample raw CSV file matching the Home Credit raw format."""
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    defaults = rng.choice([0, 1], size=n, p=[0.92, 0.08])
    raw_data = {
        "SK_ID_CURR": np.arange(100000, 100000 + n),
        "TARGET": defaults,
        "CODE_GENDER": rng.choice(["F", "M"], size=n, p=[0.65, 0.35]),
        "REGION_RATING_CLIENT": rng.choice([1, 2, 3], size=n, p=[0.15, 0.70, 0.15]),
        "EXT_SOURCE_1": rng.uniform(0.1, 0.9, size=n),
        "EXT_SOURCE_2": rng.uniform(0.1, 0.9, size=n),
        "EXT_SOURCE_3": rng.uniform(0.1, 0.9, size=n),
        "AMT_INCOME_TOTAL": rng.normal(160000, 50000, size=n).clip(30000, 500000),
        "AMT_CREDIT": rng.normal(500000, 200000, size=n).clip(50000, 1500000),
        "AMT_ANNUITY": rng.normal(25000, 10000, size=n).clip(3000, 80000),
        "AMT_GOODS_PRICE": rng.normal(450000, 180000, size=n).clip(45000, 1400000),
        "DAYS_BIRTH": -rng.integers(21 * 365, 68 * 365, size=n),
        "DAYS_EMPLOYED": rng.choice([-1500, -3000, -500, 365243], size=n, p=[0.4, 0.3, 0.2, 0.1]),
        "DAYS_REGISTRATION": -rng.integers(100, 10000, size=n),
        "DAYS_ID_PUBLISH": -rng.integers(100, 5000, size=n),
        "CNT_CHILDREN": rng.choice([0, 1, 2], size=n, p=[0.7, 0.2, 0.1]),
        "CNT_FAM_MEMBERS": rng.choice([1, 2, 3, 4], size=n, p=[0.2, 0.5, 0.2, 0.1]),
        "REGION_POPULATION_RELATIVE": rng.uniform(0.001, 0.07, size=n),
        "NAME_CONTRACT_TYPE": rng.choice(["Cash loans", "Revolving loans"], size=n, p=[0.9, 0.1]),
        "NAME_INCOME_TYPE": rng.choice(
            ["Working", "Commercial associate", "Pensioner", "State servant"],
            size=n,
            p=[0.5, 0.25, 0.15, 0.1],
        ),
        "NAME_EDUCATION_TYPE": rng.choice(
            ["Secondary / secondary special", "Higher education", "Incomplete higher"],
            size=n,
            p=[0.7, 0.25, 0.05],
        ),
        "NAME_FAMILY_STATUS": rng.choice(
            ["Married", "Single / not married", "Civil marriage", "Widow"],
            size=n,
            p=[0.6, 0.2, 0.1, 0.1],
        ),
        "NAME_HOUSING_TYPE": rng.choice(
            ["House / apartment", "With parents", "Rented apartment"], size=n, p=[0.85, 0.1, 0.05]
        ),
        "FLAG_OWN_CAR": rng.choice(["Y", "N"], size=n, p=[0.35, 0.65]),
        "FLAG_OWN_REALTY": rng.choice(["Y", "N"], size=n, p=[0.7, 0.3]),
    }
    pd.DataFrame(raw_data).to_csv(path, index=False)
    return path
