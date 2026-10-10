"""Canonical applicant schema shared by training and serving.

The Protected Attribute (``group``) is defined here for governance/fairness use
only and is NEVER included in the model feature matrix (constitution III, AD-5).
"""

from __future__ import annotations

# Numeric raw applicant fields (model inputs).
NUMERIC_FIELDS: list[str] = [
    "age",
    "annual_income",
    "employment_length",
    "debt_to_income",
    "credit_utilization",
    "num_delinquencies",
    "num_open_accounts",
    "loan_amount",
    "interest_rate",
]

# Categorical raw fields with FIXED category vocabularies (deterministic one-hot).
CATEGORICAL_FIELDS: dict[str, list[str]] = {
    "home_ownership": ["RENT", "OWN", "MORTGAGE"],
    "purpose": ["debt_consolidation", "credit_card", "home_improvement", "major_purchase", "other"],
}

# Home Credit specific numerical fields
HOMECREDIT_NUMERIC_FIELDS: list[str] = [
    "age",
    "annual_income",
    "employment_length",
    "loan_amount",
    "annuity",
    "goods_price",
    "debt_to_income",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "DAYS_ID_PUBLISH",
    "DAYS_REGISTRATION",
    "CNT_CHILDREN",
    "CNT_FAM_MEMBERS",
    "REGION_POPULATION_RELATIVE",
]

# Home Credit specific categorical fields
HOMECREDIT_CATEGORICAL_FIELDS: dict[str, list[str]] = {
    "NAME_CONTRACT_TYPE": ["Cash loans", "Revolving loans"],
    "NAME_INCOME_TYPE": ["Working", "Commercial associate", "Pensioner", "State servant"],
    "NAME_EDUCATION_TYPE": [
        "Higher education",
        "Secondary / secondary special",
        "Incomplete higher",
    ],
    "NAME_FAMILY_STATUS": [
        "Married",
        "Single / not married",
        "Civil marriage",
        "Widow",
    ],
    "NAME_HOUSING_TYPE": [
        "House / apartment",
        "With parents",
        "Rented apartment",
    ],
    "FLAG_OWN_CAR": ["Y", "N"],
    "FLAG_OWN_REALTY": ["Y", "N"],
}

# Behavioral and transaction proxy fields (from auxiliary installment/bureau/card tables)
HOMECREDIT_BEHAVIORAL_FIELDS: list[str] = [
    "has_behavioral_history",
    "installment_late_ratio",
    "mean_days_past_due",
    "installment_underpay_ratio",
    "payment_recency_days",
    "payment_count",
    "payment_total_amount",
    "payment_avg_amount",
    "bureau_total_loans_count",
    "bureau_active_loans_count",
    "bureau_total_debt",
    "bureau_total_overdue",
    "bureau_debt_to_credit_ratio",
    "cc_utilization_mean",
    "cc_balance_mean",
    "cc_drawings_atm_sum",
    "cc_drawings_pos_sum",
]

# Governance-only. Not a feature.
PROTECTED_ATTRIBUTE: str = "group"
PROTECTED_VALUES: list[str] = ["A", "B"]

TARGET: str = "default"

# Human-readable labels for reason codes (FR-14 grounding).
FEATURE_LABELS: dict[str, str] = {
    # Synthetic / Shared
    "age": "applicant age",
    "annual_income": "annual income",
    "employment_length": "length of employment",
    "debt_to_income": "debt-to-income ratio",
    "credit_utilization": "credit utilization",
    "num_delinquencies": "recent delinquencies",
    "num_open_accounts": "number of open accounts",
    "loan_amount": "requested loan amount",
    "interest_rate": "loan interest rate",
    "income_to_loan": "income relative to loan size",
    "delinquency_flag": "presence of delinquencies",
    # Home Credit external bureau scores & financial indicators
    "EXT_SOURCE_1": "external bureau risk score 1",
    "EXT_SOURCE_2": "external bureau risk score 2",
    "EXT_SOURCE_3": "external bureau risk score 3",
    "ext_source_1": "external bureau risk score 1",
    "ext_source_2": "external bureau risk score 2",
    "ext_source_3": "external bureau risk score 3",
    "annuity": "loan annuity amount",
    "goods_price": "goods purchase price",
    "DAYS_ID_PUBLISH": "identity document publication age",
    "DAYS_REGISTRATION": "address registration tenure",
    "days_id_publish": "identity document publication age",
    "days_registration": "address registration tenure",
    "CNT_CHILDREN": "number of children",
    "CNT_FAM_MEMBERS": "family size",
    "cnt_children": "number of children",
    "cnt_fam_members": "family size",
    "REGION_POPULATION_RELATIVE": "relative region population density",
    "region_population_relative": "relative region population density",
    # Engineered behavioral and ratio features
    "credit_to_income": "credit to income ratio",
    "annuity_to_income": "annuity to income ratio",
    "employment_to_age": "employment tenure relative to age",
    "goods_to_loan": "goods price to loan ratio",
    "ext_sources_mean": "average external bureau score",
    # Behavioral transaction proxies (installments, bureau, cards)
    "has_behavioral_history": "historical credit repayment records",
    "installment_late_ratio": "historical late payment frequency",
    "mean_days_past_due": "average days past due on historical installments",
    "installment_underpay_ratio": "historical installment underpayment rate",
    "payment_recency_days": "days since most recent recorded repayment",
    "payment_count": "total number of completed repayments",
    "payment_total_amount": "total historical repayment amount",
    "payment_avg_amount": "average payment installment amount",
    "bureau_total_loans_count": "total external loans on bureau",
    "bureau_active_loans_count": "number of currently active external loans",
    "bureau_total_debt": "total outstanding balance across credit bureau accounts",
    "bureau_total_overdue": "total overdue amount across credit bureau accounts",
    "bureau_debt_to_credit_ratio": "bureau debt to credit ratio",
    "cc_utilization_mean": "average revolving credit card balance utilization",
    "cc_balance_mean": "average revolving credit card balance",
    "cc_drawings_atm_sum": "total cash ATM drawings on revolving credit",
    "cc_drawings_pos_sum": "total point-of-sale merchant spending on credit card",
}


