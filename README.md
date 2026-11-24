# GreenOps AI — Sustainability Monitoring & Anomaly Detection

**YuvaIntern prototype | Synthetic demonstration project**

## Selected use case
Hybrid sustainability exception monitoring for electricity, water, diesel and emissions records. It flags unusual consumption, missing diesel logs, meter ID changes and duplicate invoices. It is decision support, not autonomous payment or reporting software.

## Dataset
- `data/facility_readings_400k.csv.gz`: exactly 400,000 synthetic readings, 15 sites, Jan–Dec 2025.
- `data/monthly_invoices.csv`: monthly invoice records with intentional duplicates.
- Synthetic anomalies, meter changes at two sites from July, and missing diesel logs are injected.
- No real company data is represented.

The large uncompressed CSV is intentionally not tracked in Git. The compressed `facility_readings_400k.csv.gz` is used by the app; keep the raw `.csv` ignored locally.

## Run (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```
## Evaluate
```powershell
python tests/evaluate.py
pytest -q
```
60 deterministic synthetic scenarios are included. `tests/evaluate.py` runs the actual `GreenOpsDetector` against generated scenario rows and records accuracy, precision, recall, F1, confusion counts and local latency in `reports/`. This is a reproducible prototype benchmark, not independently labelled field validation. The reported local cost is an accounting placeholder (₹0 inference charge) and excludes hardware, electricity, development and hosting.

## Opportunity matrix
See `reports/opportunity_matrix.csv`: eight use cases scored for value, feasibility, data readiness and risk (1–5; risk 5 is highest). Invoice duplicate detection is the strongest low-effort opportunity; the selected scope combines it with operational anomaly and data-quality checks.

## Model and controls
Isolation Forest on log-transformed consumption, cost and emissions, supported by site/resource robust-baseline checks and explicit missing-log, meter-change and duplicate-invoice rules. Alerts include reasons and recommended human review. If model scoring is unavailable, deterministic checks remain.

## Responsible AI
See `reports/responsible_ai.md`. BRSR data must be traceable to approved evidence and methodology; confirm current SEBI requirements with compliance specialists. No automated BRSR disclosure or invoice payment is enabled.

## Illustrative ROI
Assumptions: ₹1.8 crore annual invoice spend, 1.2% duplicate-payment prevention opportunity, 520 review hours saved at ₹350/hour, and ₹90,000 annual operating cost. Gross annual benefit ₹398,000; net ₹308,000; payback 2.71 months. These are hypothetical inputs requiring finance validation.

## Next steps
Replace synthetic data with governed exports, approve emissions factors, create time-separated labelled test data, tune thresholds with site teams, complete security/compliance review, and integrate only with human approval.
