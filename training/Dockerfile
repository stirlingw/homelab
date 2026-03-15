FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    ray[train]==2.40.0 \
    xgboost-ray==0.1.19 \
    mlflow==2.19.0 \
    numpy==1.26.4 \
    boto3==1.35.0
COPY train.py .
CMD ["python", "train.py"]
