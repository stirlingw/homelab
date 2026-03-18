import psycopg2
import pandas as pd
import numpy as np
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
import os
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

DB_CONFIG = {
    "host": "postgresql.mlflow.svc.cluster.local",
    "port": 5432,
    "database": "mlflow",
    "user": "mlflow",
    "password": os.environ.get("POSTGRES_PASSWORD", "mlflow123")
}

PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "pushgateway-prometheus-pushgateway.monitoring.svc.cluster.local:9091")

def get_reference_data():
    return pd.DataFrame({
        "feature1": [1, 3, 5, 7],
        "feature2": [2, 4, 6, 8],
        "prediction": [0, 1, 0, 1],
        "probability": [0.3, 0.7, 0.3, 0.7]
    })

def get_current_data(hours=24):
    conn = psycopg2.connect(**DB_CONFIG)
    query = f"""
        SELECT feature1, feature2, prediction, probability
        FROM predictions
        WHERE timestamp > NOW() - INTERVAL '{hours} hours'
        ORDER BY timestamp DESC
        LIMIT 1000
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def push_metrics(drift_detected, drift_share, predictions_count):
    registry = CollectorRegistry()

    g_drift = Gauge(
        "evidently_drift_detected",
        "Whether dataset drift was detected (1=yes, 0=no)",
        registry=registry
    )
    g_share = Gauge(
        "evidently_drift_share",
        "Share of drifted columns",
        registry=registry
    )
    g_count = Gauge(
        "evidently_predictions_analyzed",
        "Number of predictions analyzed",
        registry=registry
    )

    g_drift.set(1 if drift_detected else 0)
    g_share.set(drift_share)
    g_count.set(predictions_count)

    push_to_gateway(PUSHGATEWAY_URL, job="drift-monitor", registry=registry)
    print(f"Metrics pushed to Pushgateway at {PUSHGATEWAY_URL}")

def run_drift_report():
    reference = get_reference_data()
    current = get_current_data(hours=24)

    if len(current) < 5:
        print(f"Not enough data for drift detection: {len(current)} rows")
        return

    print(f"Running drift detection on {len(current)} predictions...")

    report = Report(metrics=[
        DataDriftPreset(),
        DataQualityPreset(),
    ])

    report.run(reference_data=reference, current_data=current)
    report.save_html("/tmp/drift_report.html")

    result = report.as_dict()
    drift_detected = result["metrics"][0]["result"]["dataset_drift"]
    drift_share = result["metrics"][0]["result"]["share_of_drifted_columns"]

    print(f"Dataset drift detected: {drift_detected}")
    print(f"Share of drifted columns: {drift_share:.2%}")
    print(f"Predictions analyzed: {len(current)}")

    push_metrics(drift_detected, drift_share, len(current))

    if drift_detected:
        print("WARNING: Data drift detected!")
    else:
        print("No significant drift detected.")

if __name__ == "__main__":
    run_drift_report()
