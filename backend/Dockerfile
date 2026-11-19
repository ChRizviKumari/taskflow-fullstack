FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV TASKFLOW_DB=/data/taskflow.db
RUN mkdir -p /data
EXPOSE 5000
# Single worker + threads: SQLite allows one writer at a time anyway.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "wsgi:app"]
