import ray
from ray import train
from ray.train import ScalingConfig
from ray.train.xgboost import XGBoostTrainer
import mlflow
import numpy as np
import os

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio.mlflow.svc.cluster.local:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin123"

mlflow.set_tracking_uri("http://mlflow.mlflow.svc.cluster.local:80")
mlflow.set_experiment("xgboost-homelab")

ray.init(address="ray://ray-kuberay-head-svc.ray.svc.cluster.local:10001")

import ray.data
X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([0, 1, 0, 1])
data = np.column_stack([X, y])
dataset = ray.data.from_numpy(data)

def train_func():
    with mlflow.start_run():
        trainer = XGBoostTrainer(
            scaling_config=ScalingConfig(
                num_workers=1,
                use_gpu=False,
            ),
            label_column="2",
            params={
                "max_depth": 2,
                "objective": "binary:logistic",
                "eval_metric": "logloss",
            },
            datasets={"train": dataset},
            num_boost_round=10,
        )
        result = trainer.fit()

        mlflow.log_params({
            "max_depth": 2,
            "num_boost_round": 10,
        })
        mlflow.log_metric("train_loss", result.metrics["train-logloss"])

        mlflow.register_model(
            f"runs:/{mlflow.active_run().info.run_id}/model",
            "XGBoostHomeLab"
        )
        print(f"Training complete. Metrics: {result.metrics}")

train_func()
