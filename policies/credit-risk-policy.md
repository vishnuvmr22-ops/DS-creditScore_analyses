# Credit Risk Decisioning Policy

## risk-policy#decision-bands
Applications are decisioned into three bands from the model's probability of
default (PD): approve (PD below the approval threshold), decline (PD at or above
the decline threshold), and manual review (in between). Thresholds are calibrated
against an expected-loss objective, balancing approval rate against default rate.

## risk-policy#manual-review
Applications routed to manual review require a human underwriter to consider
compensating factors not fully captured by the model, such as recent income
changes or documentation. The model's top drivers are provided to focus the review.

## risk-policy#affordability
Affordability is assessed primarily through debt-to-income and income relative to
the requested loan amount. Applicants with limited income relative to obligations
present higher risk of default.

## risk-policy#interest-rate-risk
A high offered interest rate correlates with higher priced risk tiers and can
itself increase the probability of default through higher required payments.

## risk-policy#fair-lending
Decisioning must comply with fair-lending principles. Approval-rate parity across
protected groups is monitored; material disparities trigger investigation. The
protected attribute is never a model input.
