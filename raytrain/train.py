import ray
from ray.train import ScalingConfig, RunConfig
from ray.train.xgboost import XGBoostTrainer
import mlflow
import mlflow.xgboost
import xgboost as xgb
import numpy as np
import pandas as pd
import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio.mlflow.svc.cluster.local:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin123"
os.environ["GIT_PYTHON_REFRESH"] = "quiet"

mlflow.set_tracking_uri("http://10.43.250.197:80")
mlflow.set_experiment("xgboost-ray-train")

df = pd.DataFrame({
    "feature1": [1, 3, 5, 7],
    "feature2": [2, 4, 6, 8],
    "label":    [0, 1, 0, 1],
})
dataset = ray.data.from_pandas(df)

params = {
    "max_depth": 2,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
}
num_boost_round = 10

with mlflow.start_run():
    mlflow.log_params(params)
    mlflow.log_param("num_boost_round", num_boost_round)
    mlflow.log_param("num_workers", 1)

    trainer = XGBoostTrainer(
        scaling_config=ScalingConfig(
            num_workers=1,
            use_gpu=False,
            resources_per_worker={"CPU": 0.5},
            trainer_resources={"CPU": 0.5},
        ),
        run_config=RunConfig(
            storage_path="/tmp/ray_results",
        ),
        label_column="label",
        params=params,
        datasets={"train": dataset},
        num_boost_round=num_boost_round,
    )

    result = trainer.fit()
    mlflow.log_metric("train_logloss", result.metrics["train-logloss"])

    with result.checkpoint.as_directory() as checkpoint_path:
        model_path = os.path.join(checkpoint_path, "model.ubj")
        model = xgb.Booster()
        model.load_model(model_path)
        mlflow.xgboost.log_model(
            model,
            artifact_path="model",
            registered_model_name="XGBoostRayTrain"
        )

    print(f"Training complete. Metrics: {result.metrics}")
    print(f"Model registered as XGBoostRayTrain")
