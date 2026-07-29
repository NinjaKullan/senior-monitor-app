FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY kettle ./kettle
COPY scripts ./scripts
COPY migrations ./migrations

EXPOSE 8080

CMD ["uvicorn", "kettle.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
