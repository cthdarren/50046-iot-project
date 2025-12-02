# syntax=docker/dockerfile:1.5
FROM python:3.14-bookworm AS base
ENV AVAILABILITY_SERVICE_URL="http://availability-service"
ENV AVAILABILITY_SERVICE_PORT=$AVAILABILITY_SERVICE_PORT
# set working directory inside the container to /app
WORKDIR /app
# Install system dependencies (psycopg, uvicorn performance)
RUN apt-get update && \
    apt-get install -y libpq-dev build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Copy shared code to container
COPY shared/ ./shared
# copy application files from /app to container's working directory
COPY analytics-service/app/ .
# Copy requirements.txt to container
COPY analytics-service/requirements.txt .
# Use build cache for faster pip installs
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt
# start application with uvicorn on image start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]