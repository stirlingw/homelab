import xgboost as xgb
import mlflow
import mlflow.xgboost
import numpy as np
import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://10.43.109.100:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin123"
os.environ["GIT_PYTHON_REFRESH"] = "quiet"

mlflow.set_tracking_uri("http://10.43.250.197:80")
mlflow.set_experiment("xgboost-homelab")

X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([0, 1, 0, 1])
dtrain = xgb.DMatrix(X, label=y)

params = {
    "max_depth": 2,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
}
num_boost_round = 10

with mlflow.start_run():
    mlflow.log_params(params)
    mlflow.log_param("num_boost_round", num_boost_round)

    model = xgb.train(params, dtrain, num_boost_round=num_boost_round)

    preds = model.predict(dtrain)
    accuracy = float(np.mean((preds > 0.5) == y))
    mlflow.log_metric("train_accuracy", accuracy)

    mlflow.xgboost.log_model(
        model,
        artifact_path="model",
        registered_model_name="XGBoostHomeLab"
    )

    print(f"Training complete.")
    print(f"Accuracy: {accuracy}")
    print(f"Model registered as XGBoostHomeLab")
