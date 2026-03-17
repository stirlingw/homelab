from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app
import urllib.request
import json
import time

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
        return result
    except Exception as e:
        error_counter.labels(endpoint="/predict").inc()
        raise e

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
# updated
# pipeline test
# pipeline test 2
# pipeline test 2
# self-hosted runner test
