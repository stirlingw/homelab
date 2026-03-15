FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    xgboost==2.1.0 \
    mlflow==2.19.0 \
    numpy==1.26.4 \
    boto3==1.35.0
COPY train.py .
CMD ["python", "train.py"]
