FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY sdk /app/sdk
COPY service /app/service
COPY docs /app/docs
COPY docker /app/docker

RUN uv sync
RUN chmod +x /app/docker/api/start-api.sh

EXPOSE 8000

CMD ["/app/docker/api/start-api.sh"]
