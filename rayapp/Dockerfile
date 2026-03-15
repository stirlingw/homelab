FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    ray[serve]==2.40.0 \
    xgboost==2.1.0 \
    fastapi==0.115.0 \
    uvicorn==0.30.0 \
    numpy==1.26.4

# Copy model code
COPY xgboost_serve.py .

# Expose Ray Serve port
EXPOSE 8000

# Start Ray Serve
CMD ["python", "xgboost_serve.py"]
