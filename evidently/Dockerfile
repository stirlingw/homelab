FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir \
    evidently==0.4.33 \
    psycopg2-binary==2.9.9 \
    pandas==2.1.0 \
    numpy==1.26.4
COPY drift_monitor.py .
CMD ["python", "drift_monitor.py"]
