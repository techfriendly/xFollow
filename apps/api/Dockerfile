FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/apps/api

WORKDIR /app

COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY apps/api /app/apps/api
COPY infra /app/infra

RUN mkdir -p /app/data/evidence

EXPOSE 8100

CMD ["uvicorn", "xfollow_api.main:app", "--host", "0.0.0.0", "--port", "8100"]
