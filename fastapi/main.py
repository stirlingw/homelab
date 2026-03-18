from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app
import urllib.request
import json
import time
import psycopg2
import os

app = FastAPI()

request_counter = Counter(
    "fastapi_requests_total",
    "Total number of requests",
    ["endpoint"]
)

prediction_latency = Histogram(
    "fastapi_prediction_latency_seconds",
    "Prediction request latency"
)

error_counter = Counter(
    "fastapi_errors_total",
    "Total number of errors",
    ["endpoint"]
)

RAY_SERVE_URL = "http://xgboost-serve.ray.svc.cluster.local:8000/predict"

DB_CONFIG = {
    "host": "postgresql.mlflow.svc.cluster.local",
    "port": 5432,
    "database": "mlflow",
    "user": "mlflow",
    "password": os.environ.get("POSTGRES_PASSWORD", "mlflow123")
}

def log_prediction(features, prediction, probability):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO predictions (feature1, feature2, prediction, probability) VALUES (%s, %s, %s, %s)",
            (features[0], features[1], prediction, probability)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to log prediction: {e}")

@app.get("/health")
def health():
    request_counter.labels(endpoint="/health").inc()
    return {"status": "ok"}

@app.post("/predict")
def predict(data: dict):
    request_counter.labels(endpoint="/predict").inc()
    start = time.time()
    try:
        payload = json.dumps(data).encode()
        req = urllib.request.Request(
            RAY_SERVE_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        response = urllib.request.urlopen(req).read().decode()
        result = json.loads(response)
        prediction_latency.observe(time.time() - start)
        log_prediction(
            data["features"],
            result["prediction"],
            result["probability"]
        )
        return result
    except Exception as e:
        error_counter.labels(endpoint="/predict").inc()
        raise e

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
