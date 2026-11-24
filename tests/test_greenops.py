import pandas as pd
import pytest

from src.greenops import GreenOpsDetector, deduplicate_invoices


def make_training():
    rows = []
    for site in ["CHD-01", "CHD-02"]:
        for resource, suffix, center in [
            ("electricity", "ELE", 100.0),
            ("water", "WAT", 20.0),
            ("diesel", "DIE", 10.0),
        ]:
            for i in range(30):
                value = center + (i % 5) * 0.2
                rows.append({
                    "site_id": site,
                    "resource_type": resource,
                    "meter_id": f"MTR-{site[-2:]}-{suffix}",
                    "timestamp": pd.Timestamp("2025-01-01") + pd.Timedelta(days=i),
                    "consumption": value,
                    "estimated_cost_inr": value * 8,
                    "emissions_kgco2e": value * 0.7,
                    "generator_log_present": True,
                    "meter_id_changed_flag": False,
                })
    return pd.DataFrame(rows)


def test_invoice_deduplication():
    data = pd.DataFrame({"invoice_id": ["A", "A", "B"], "amount_inr": [10, 10, 20]})
    clean, duplicates = deduplicate_invoices(data)
    assert len(clean) == 2
    assert len(duplicates) == 2


def test_detector_fits_with_pandas_2_mad_calculation():
    detector = GreenOpsDetector().fit(make_training())
    assert detector.fitted
    assert not detector.group_stats["mad"].isna().any()


def test_meter_swap_is_detected_from_baseline_not_prebaked_flag():
    training = make_training()
    detector = GreenOpsDetector().fit(training, meter_reference=training)
    row = training.iloc[0].to_dict()
    row["meter_id"] = "MTR-NEW-01-ELE"
    row["meter_id_changed_flag"] = False  # Deliberately stale source flag.
    result = detector.predict_one(row)
    assert result["flagged"]
    assert any("Meter ID changed" in reason for reason in result["reasons"])


def test_prebaked_meter_flag_is_not_trusted():
    training = make_training()
    detector = GreenOpsDetector().fit(training, meter_reference=training)
    row = training.iloc[0].to_dict()
    row["meter_id_changed_flag"] = True
    result = detector.predict_one(row)
    assert not any("Meter ID changed" in reason for reason in result["reasons"])


def test_missing_diesel_log_is_flagged():
    training = make_training()
    detector = GreenOpsDetector().fit(training, meter_reference=training)
    row = training[training.resource_type == "diesel"].iloc[0].to_dict()
    row["generator_log_present"] = False
    result = detector.predict_one(row)
    assert result["flagged"]
    assert "Diesel generator log is missing" in result["reasons"]


def test_predict_before_fit_raises():
    with pytest.raises(RuntimeError, match="Call fit"):
        GreenOpsDetector().predict_one({})
