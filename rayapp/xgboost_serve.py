import ray
from ray import serve
from xgboost import XGBClassifier
import numpy as np
from fastapi import FastAPI

app = FastAPI()

@serve.deployment
@serve.ingress(app)
class XGBoostModel:
    def __init__(self):
        # Train a simple toy model on startup
        self.model = XGBClassifier()
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])
        self.model.fit(X, y)
        print("Model trained and ready")

    @app.post("/predict")
    async def predict(self, data: dict):
        features = np.array(data["features"]).reshape(1, -1)
        prediction = self.model.predict(features)
        probability = self.model.predict_proba(features)
        return {
            "prediction": int(prediction[0]),
            "probability": probability[0].tolist()
        }

entrypoint = XGBoostModel.bind()
