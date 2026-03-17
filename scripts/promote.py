#!/usr/bin/env python3
import mlflow
import argparse
import subprocess
import os
import sys

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio.mlflow.svc.cluster.local:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin123"

mlflow.set_tracking_uri("http://10.43.250.197:80")
client = mlflow.MlflowClient()

def promote(model_name, version, to_stage):
    print(f"Promoting {model_name} v{version} to {to_stage}...")

    current = client.get_latest_versions(model_name, stages=[to_stage])
    if current:
        print(f"Archiving current {to_stage} version {current[0].version}...")
        client.transition_model_version_stage(
            name=model_name,
            version=current[0].version,
            stage="Archived"
        )

    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage=to_stage
    )
    print(f"Successfully promoted {model_name} v{version} to {to_stage}")

    if to_stage == "Production":
        print("Restarting Ray Serve to load new model...")
        result = subprocess.run(
            ["kubectl", "rollout", "restart", "deployment/xgboost-serve", "-n", "ray"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("Ray Serve restarting...")
            subprocess.run(
                ["kubectl", "rollout", "status", "deployment/xgboost-serve", "-n", "ray", "--timeout=120s"],
                text=True
            )
            print("Rollout complete. New model is live.")
        else:
            print(f"Error restarting Ray Serve: {result.stderr}")
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model name")
    parser.add_argument("--version", required=True, help="Version number")
    parser.add_argument("--stage", default="Production", choices=["Staging", "Production"])
    args = parser.parse_args()
    promote(args.model, args.version, args.stage)
