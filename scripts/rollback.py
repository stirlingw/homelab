#!/usr/bin/env python3
import mlflow
import subprocess
import os
import sys

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio.mlflow.svc.cluster.local:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin123"

mlflow.set_tracking_uri("http://10.43.250.197:80")
client = mlflow.MlflowClient()

def rollback(model_name):
    print(f"Rolling back {model_name}...")

    current_production = client.get_latest_versions(model_name, stages=["Production"])
    if not current_production:
        print("No Production model found. Nothing to roll back.")
        sys.exit(1)

    current_version = int(current_production[0].version)
    print(f"Current Production version: {current_version}")

    archived = client.get_latest_versions(model_name, stages=["Archived"])
    if not archived:
        print("No Archived versions found. Cannot roll back.")
        sys.exit(1)

    previous_version = max(archived, key=lambda x: int(x.version))
    print(f"Rolling back to version: {previous_version.version}")

    print(f"Archiving current Production v{current_version}...")
    client.transition_model_version_stage(
        name=model_name,
        version=str(current_version),
        stage="Archived"
    )

    print(f"Promoting v{previous_version.version} back to Production...")
    client.transition_model_version_stage(
        name=model_name,
        version=previous_version.version,
        stage="Production"
    )

    print("Restarting Ray Serve...")
    result = subprocess.run(
        ["kubectl", "rollout", "restart", "deployment/xgboost-serve", "-n", "ray"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        subprocess.run(
            ["kubectl", "rollout", "status", "deployment/xgboost-serve", "-n", "ray", "--timeout=120s"],
            text=True
        )
        print(f"Rollback complete. Now serving v{previous_version.version}")
    else:
        print(f"Error restarting Ray Serve: {result.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model name")
    args = parser.parse_args()
    rollback(args.model)
