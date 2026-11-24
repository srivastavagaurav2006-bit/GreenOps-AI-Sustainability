from pathlib import Path
import time

import numpy as np
import pandas as pd
import sys
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.greenops import GreenOpsDetector
CASES_PATH = ROOT / "tests" / "test_cases.csv"
REPORTS_DIR = ROOT / "reports"


def make_training_data(seed=42):
    """Create a reproducible, clean reference population for the detector benchmark."""
    rng = np.random.default_rng(seed)
    rows = []
    for site_num in range(1, 6):
        site_id = f"CHD-{site_num:02d}"
        for resource_type, meter_suffix, center in [
            ("electricity", "ELE", 120.0),
            ("water", "WAT", 18.0),
            ("diesel", "DIE", 10.0),
        ]:
            for _ in range(100):
                consumption = max(0.1, rng.normal(center, center * 0.08))
                cost_rate = {"electricity": 8.0, "water": 32.0, "diesel": 92.0}[resource_type]
                emission_rate = {"electricity": 0.7, "water": 0.0003, "diesel": 2.68}[resource_type]
                rows.append({
                    "site_id": site_id,
                    "resource_type": resource_type,
                    "meter_id": f"MTR-{site_num:02d}-{meter_suffix}",
                    "timestamp": pd.Timestamp("2025-01-01") + pd.Timedelta(minutes=len(rows)),
                    "consumption": consumption,
                    "estimated_cost_inr": consumption * cost_rate,
                    "emissions_kgco2e": consumption * emission_rate,
                    "generator_log_present": True,
                })
    return pd.DataFrame(rows)


def make_case_row(scenario, training):
    site_id = "CHD-01"
    resource_type = "diesel" if scenario == "missing_diesel_log" else "electricity"
    baseline = training[
        (training.site_id == site_id) & (training.resource_type == resource_type)
    ].iloc[0]
    row = baseline.to_dict()
    row.update({
        "site_id": site_id,
        "resource_type": resource_type,
        "generator_log_present": True,
        "duplicate_invoice_flag": False,
    })

    if scenario == "high_consumption":
        row["consumption"] = float(baseline.consumption) * 25
        row["estimated_cost_inr"] = float(baseline.estimated_cost_inr) * 25
        row["emissions_kgco2e"] = float(baseline.emissions_kgco2e) * 25
    elif scenario == "missing_diesel_log":
        row["generator_log_present"] = False
    elif scenario == "meter_change":
        row["meter_id"] = "MTR-NEW-01-ELE"
    elif scenario == "duplicate_invoice":
        row["duplicate_invoice_flag"] = True
    return row


def run():
    REPORTS_DIR.mkdir(exist_ok=True)
    cases = pd.read_csv(CASES_PATH)
    training = make_training_data()
    detector = GreenOpsDetector(contamination=0.03, random_state=42).fit(
        training, meter_reference=training
    )

    predictions = []
    elapsed_ms = []
    for _, case in cases.iterrows():
        row = make_case_row(case["scenario"], training)
        start = time.perf_counter()
        prediction = detector.predict_one(row)
        elapsed_ms.append((time.perf_counter() - start) * 1000)
        predictions.append(prediction["flagged"])

    cases["predicted_flag"] = predictions
    cases["correct"] = cases["expected_flag"].astype(bool) == cases["predicted_flag"]
    y_true = cases["expected_flag"].astype(bool)
    y_pred = cases["predicted_flag"].astype(bool)

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[False, True]).ravel()

    results = {
        "test_cases": int(len(cases)),
        "correct": int(cases["correct"].sum()),
        "accuracy_pct": round(accuracy * 100, 2),
        "precision_pct": round(precision * 100, 2),
        "recall_pct": round(recall * 100, 2),
        "f1_pct": round(f1 * 100, 2),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "mean_latency_ms": round(float(np.mean(elapsed_ms)), 3),
        "p95_latency_ms": round(float(np.percentile(elapsed_ms, 95)), 3),
        "cost_per_request_inr": 0.0,
        "cost_note": "Local deterministic inference; excludes hardware, electricity, development and hosting costs.",
        "evaluation_note": "Synthetic scenario benchmark against the GreenOpsDetector; not independent production validation.",
    }
    cases.to_csv(REPORTS_DIR / "test_case_results.csv", index=False)
    pd.DataFrame([results]).to_csv(REPORTS_DIR / "test_results.csv", index=False)
    print(results)
    if accuracy < 0.80:
        raise AssertionError(f"Acceptance threshold not met: {accuracy:.1%} < 80%")
    return results


if __name__ == "__main__":
    run()
