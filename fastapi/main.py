from fastapi import FastAPI
import urllib.request
import json

app = FastAPI()

RAY_SERVE_URL = "http://xgboost-serve.ray.svc.cluster.local:8000/predict"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(data: dict):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(
        RAY_SERVE_URL,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    response = urllib.request.urlopen(req).read().decode()
    return json.loads(response)
