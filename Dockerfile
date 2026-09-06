FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY plugins ./plugins
COPY security ./security
COPY sandbox ./sandbox

ENV PYTHONUNBUFFERED=1
ENV QUEUE_BACKEND=redis

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
