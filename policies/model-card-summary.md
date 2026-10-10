# Model Card Summary (for RAG grounding)

## model-card#intended-use
The PD model estimates probability of default for a credit applicant in a
demonstration context on synthetic data. It supports approve/decline/review
decisions and adverse-action reason codes. It is not for real lending decisions.

## model-card#drivers
The model's decisions are explained with SHAP driver attribution. The most common
risk-increasing drivers are debt-to-income ratio, recent delinquencies, credit
utilization, and offered interest rate. Favorable drivers include higher income
and longer employment.

## model-card#limitations
Metrics reflect synthetic data and do not represent real-world performance. The
model has no temporal validation and no reject inference. Reason codes describe
statistical associations, not causal determinations.

## model-card#governance
Every registered model version carries logged metrics (AUC-ROC, KS, Brier),
calibration, a fairness parity metric across a protected attribute, and a model
card. Ungoverned versions cannot be registered.
