# syntax=docker/dockerfile:1.5
FROM python:3.12-slim AS base
# set working directory inside the container to /app
WORKDIR /app
# Install system dependencies (psycopg, uvicorn performance)
RUN apt-get update && apt-get install -y build-essential libpq-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# copy requirements.txt to working directory in container
COPY requirements.txt .
# Use build cache for faster pip installs
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
# copy application files from /app to container's working directory
COPY app/ .
# start application with uvicorn on image start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]