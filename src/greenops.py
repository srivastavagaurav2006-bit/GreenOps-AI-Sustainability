import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

FEATURES = ["consumption", "estimated_cost_inr", "emissions_kgco2e"]


class GreenOpsDetector:
    """Hybrid anomaly detector with explainable data-quality rules."""

    def __init__(self, contamination=0.03, random_state=42):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.fitted = False
        self.group_stats = None
        self.meter_baseline = {}

    @staticmethod
    def _key(value):
        return "" if pd.isna(value) else str(value).strip()

    def fit(self, data, meter_reference=None):
        clean = data.copy()
        clean["generator_log_present"] = clean["generator_log_present"].fillna(True).astype(bool)
        clean = clean[clean["generator_log_present"]]

        # pandas 2.0+ removed Series.mad(); calculate median absolute deviation explicitly.
        self.group_stats = (
            clean.groupby(["site_id", "resource_type"])["consumption"]
            .agg(
                median="median",
                mad=lambda values: (values - values.median()).abs().median(),
            )
            .reset_index()
        )
        self.group_stats["mad"] = self.group_stats["mad"].replace(0, np.nan).fillna(1.0)

        # Establish the first observed meter for each site/resource from the reference history.
        # Passing the full readings table avoids learning the baseline from a random ML sample.
        reference = (meter_reference if meter_reference is not None else data).copy()
        if "timestamp" in reference.columns:
            reference["timestamp"] = pd.to_datetime(reference["timestamp"], errors="coerce")
            reference = reference.sort_values("timestamp", kind="stable")
        self.meter_baseline = {}
        for (site_id, resource_type), group in reference.groupby(["site_id", "resource_type"]):
            meter_ids = group["meter_id"].dropna().astype(str).str.strip()
            if not meter_ids.empty:
                self.meter_baseline[(self._key(site_id), self._key(resource_type))] = meter_ids.iloc[0]

        x = np.log1p(clean[FEATURES].astype(float).clip(lower=0))
        self.model.fit(self.scaler.fit_transform(x))
        self.fitted = True
        return self

    def predict_one(self, row):
        if not self.fitted:
            raise RuntimeError("Call fit() before predict_one().")

        x = pd.DataFrame([{k: float(row.get(k, 0) or 0) for k in FEATURES}])
        score = float(
            self.model.decision_function(
                self.scaler.transform(np.log1p(x.clip(lower=0)))
            )[0]
        )

        reasons = []
        resource_type = self._key(row.get("resource_type", ""))
        site_id = self._key(row.get("site_id", ""))
        value = float(row.get("consumption", 0) or 0)

        stats = self.group_stats[
            (self.group_stats.site_id.astype(str) == site_id)
            & (self.group_stats.resource_type.astype(str) == resource_type)
        ]
        if not stats.empty:
            median = float(stats.iloc[0]["median"])
            mad = float(stats.iloc[0]["mad"])
            robust_z = abs(value - median) / (1.4826 * mad + 1e-9)
            if robust_z > 5:
                reasons.append(
                    f"Consumption is {robust_z:.1f} robust deviations from site baseline"
                )

        if resource_type == "diesel" and not bool(row.get("generator_log_present", True)):
            reasons.append("Diesel generator log is missing")

        observed_meter = self._key(row.get("meter_id", ""))
        baseline_meter = self.meter_baseline.get((site_id, resource_type))
        if observed_meter and baseline_meter and observed_meter != baseline_meter:
            reasons.append(
                f"Meter ID changed from {baseline_meter} to {observed_meter}; reconcile meter master data"
            )

        if bool(row.get("duplicate_invoice_flag", False)):
            reasons.append("Potential duplicate monthly invoice")

        if score < -0.08:
            reasons.append("Multivariate Isolation Forest anomaly")

        flagged = bool(reasons)
        high_risk = flagged and (
            len(reasons) >= 2 or any("duplicate" in reason.lower() for reason in reasons)
        )
        return {
            "flagged": flagged,
            "risk_level": "High" if high_risk else ("Medium" if flagged else "Low"),
            "anomaly_score": round(score, 4),
            "reasons": reasons or ["No material anomaly detected"],
            "recommended_action": (
                "Review source record and supporting evidence before adjustment"
                if flagged
                else "Continue routine monitoring"
            ),
        }


def prepare_readings(path):
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["generator_log_present"] = df["generator_log_present"].fillna(False).astype(bool)
    return df


def deduplicate_invoices(invoices):
    duplicated = invoices[invoices.duplicated("invoice_id", keep=False)].copy()
    return invoices.drop_duplicates("invoice_id", keep="first").copy(), duplicated
