FROM python:3.11-slim

WORKDIR /app

COPY worker.py .

RUN pip install --no-cache-dir pika==1.3.2

ENV PYTHONUNBUFFERED=1

CMD ["python", "worker.py"]
