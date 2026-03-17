import ray
from ray import serve
import xgboost as xgb
import mlflow
import mlflow.xgboost
import numpy as np
from fastapi import FastAPI
import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio.mlflow.svc.cluster.local:9000"
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
os.environ["GIT_PYTHON_REFRESH"] = "quiet"

app = FastAPI()

@serve.deployment
@serve.ingress(app)
class XGBoostModel:
    def __init__(self):
        mlflow.set_tracking_uri("http://10.43.250.197:80")
        print("Loading Production model from MLflow registry...")
        self.model = mlflow.xgboost.load_model(
            "models:/XGBoostHomeLab/Production"
        )
        self.model_info = self._get_model_info()
        print(f"Model loaded: {self.model_info}")

    def _get_model_info(self):
        client = mlflow.MlflowClient()
        versions = client.get_latest_versions("XGBoostHomeLab", stages=["Production"])
        if versions:
            return f"XGBoostHomeLab/Production/v{versions[0].version}"
        return "XGBoostHomeLab/Production"

    @app.post("/predict")
    async def predict(self, data: dict):
        features = np.array(data["features"]).reshape(1, -1)
        dmatrix = xgb.DMatrix(features)
        probability = self.model.predict(dmatrix)
        prediction = int(probability[0] > 0.5)
        return {
            "prediction": prediction,
            "probability": float(probability[0]),
            "model_version": self.model_info
        }

    @app.get("/model-info")
    async def model_info(self):
        return {"model_version": self.model_info}

if __name__ == "__main__":
    ray.init(ignore_reinit_error=True)
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    entrypoint = XGBoostModel.bind()
    serve.run(entrypoint)
    import time
    while True:
        time.sleep(1)
