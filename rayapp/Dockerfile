FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    ray[serve]==2.40.0 \
    xgboost==2.1.0 \
    mlflow==2.19.0 \
    boto3==1.35.0 \
    fastapi==0.115.0 \
    uvicorn==0.30.0 \
    numpy==1.26.4
COPY xgboost_serve.py .
EXPOSE 8000
CMD ["python", "xgboost_serve.py"]
