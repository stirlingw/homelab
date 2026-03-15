import ray
from ray import serve
import xgboost as xgb
import numpy as np
from fastapi import FastAPI

app = FastAPI()

@serve.deployment
@serve.ingress(app)
class XGBoostModel:
    def __init__(self):
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])
        dtrain = xgb.DMatrix(X, label=y)
        params = {"max_depth": 2, "objective": "binary:logistic"}
        self.model = xgb.train(params, dtrain, num_boost_round=10)
        print("Model trained and ready")

    @app.post("/predict")
    async def predict(self, data: dict):
        features = np.array(data["features"]).reshape(1, -1)
        dmatrix = xgb.DMatrix(features)
        probability = self.model.predict(dmatrix)
        prediction = int(probability[0] > 0.5)
        return {
            "prediction": prediction,
            "probability": float(probability[0])
        }

if __name__ == "__main__":
    ray.init(ignore_reinit_error=True)
    serve.start(http_options={"host": "0.0.0.0", "port": 8000})
    entrypoint = XGBoostModel.bind()
    serve.run(entrypoint)
    import time
    while True:
        time.sleep(1)
