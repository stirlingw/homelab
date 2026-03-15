import ray
from ray import serve
import xgboost as xgb
import mlflow
import mlflow.xgboost
import numpy as np
from fastapi import FastAPI
import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://10.43.109.100:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin123"
os.environ["GIT_PYTHON_REFRESH"] = "quiet"

app = FastAPI()

@serve.deployment
@serve.ingress(app)
class XGBoostModel:
    def __init__(self):
        mlflow.set_tracking_uri("http://10.43.250.197:80")
        print("Loading model from MLflow registry...")
        self.model = mlflow.xgboost.load_model(
            "models:/XGBoostHomeLab/1"
        )
        print("Model loaded successfully")

    @app.post("/predict")
    async def predict(self, data: dict):
        features = np.array(data["features"]).reshape(1, -1)
        dmatrix = xgb.DMatrix(features)
        probability = self.model.predict(dmatrix)
        prediction = int(probability[0] > 0.5)
        return {
            "prediction": prediction,
            "probability": float(probability[0]),
            "model_version": "XGBoostHomeLab/1"
        }

if __name__ == "__main__":
    ray.init(ignore_reinit_error=True)
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    entrypoint = XGBoostModel.bind()
    serve.run(entrypoint)
    import time
    while True:
        time.sleep(1)
