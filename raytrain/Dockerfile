FROM stirlingw/ray-xgboost:2.41.0
WORKDIR /app
RUN pip install --no-cache-dir \
    mlflow==2.19.0 \
    boto3==1.35.0
COPY train.py .
CMD ["python", "train.py"]
