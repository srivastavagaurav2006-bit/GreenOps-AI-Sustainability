# Responsible AI, ESG Data Governance and BRSR Support

## 1. Intended use and limitations
GreenOps AI is an **ESG/BRSR data-auditing prototype** built with synthetic demonstration records. It helps surface possible data-quality issues and unusual resource-consumption patterns for review. It is not production software, a statutory reporting system, legal advice, an audit opinion, or SEBI certification.

The system must not autonomously approve invoices, change source records, calculate final disclosures, or submit regulatory filings. A model alert is a review signal—not proof of fraud, error, emissions, or non-compliance.

## 2. BRSR / BRSR Core traceability
For any future organisational pilot:
- Map each proposed metric to the applicable reporting boundary, period, unit, methodology and responsible data owner.
- Preserve source-system references, original values, transformation steps, approved emission factors, calculation versions and timestamps.
- Maintain evidence for estimates, exclusions, restatements and changes in methodology.
- Reconcile reported values to approved source records and document review/sign-off.
- Have the sustainability, finance and compliance teams confirm the current SEBI requirements and applicability before use. This prototype does not determine regulatory applicability or certify compliance.

## 3. Privacy and DPDP Act considerations
The supplied dataset is synthetic and is not intended to represent identifiable people. A real deployment should be assessed by the organisation's privacy/legal team against applicable Indian data-protection requirements, including the Digital Personal Data Protection Act, 2023 and rules/notifications in force at the time of deployment.

Recommended controls include:
- Collect only fields needed for the stated operational purpose; avoid personal data in meter and invoice exports where possible.
- Define purpose, access roles, retention periods and secure deletion procedures.
- Apply encryption in transit and at rest, least-privilege access, secrets management and access logging.
- Mask or tokenize identifiers in development and test environments.
- Establish incident response, vendor review and data-sharing controls before connecting external systems.

These are design recommendations, not a claim that this prototype is DPDP-compliant.

## 4. Bias, representativeness and model limitations
Sites differ in capacity, weather, equipment, operating schedules and resource mix. A single global threshold can over-flag large sites or miss unusual patterns at smaller sites.

Before a pilot:
- Report false-positive and false-negative rates by site, resource type and time period.
- Validate site/resource baselines with operations teams and review seasonal effects.
- Use time-separated and independently labelled validation data; do not treat synthetic scenario performance as field accuracy.
- Monitor drift, missingness and changes in meter/invoice systems.
- Record model version, threshold, features and reason codes for every alert.

Isolation Forest scores are not probabilities. Robust-baseline checks and deterministic rules are explainable signals but can still be wrong.

## 5. Human oversight and accountability
- Operations/site owners investigate consumption and meter alerts against source evidence.
- Finance validates suspected duplicate invoices against vendor, invoice number, billing period, amount and supporting documents before any payment decision.
- Sustainability owners validate emissions factors, boundaries, calculations and disclosure evidence.
- Compliance/legal specialists determine applicable reporting obligations.
- An authorised human approves all source corrections, invoice actions and disclosures. Maintain a record of reviewer, decision, rationale and date.

## 6. Reliability, security and fallback
Retain immutable source extracts and reproducible transformations. Restrict write access; this prototype is read-only and provides recommendations only. If model scoring fails, pause automated scoring and use documented manual checks rather than silently treating records as normal.

## 7. Governance review before deployment
Complete security assessment, privacy review, data-owner approval, model validation, access-control testing, retention design and compliance review. Reassess these controls after material changes to data sources, features, thresholds or intended use.

**Status:** Educational / internship prototype using synthetic data. Not production-ready, not SEBI-certified, and not a substitute for independent audit or professional compliance review.
