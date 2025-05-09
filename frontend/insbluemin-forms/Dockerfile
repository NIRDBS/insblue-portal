# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.11
#FROM python:${PYTHON_VERSION}-slim as base
FROM python:${PYTHON_VERSION}-alpine as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Install system dependencies (including git, build dependencies, and CA certificates)
RUN apk update && apk add --no-cache git ca-certificates


WORKDIR /app

# Copy the custom CA certificates into the container
COPY certs/cacert.pem /etc/ssl/certs/cacert.pem

# Update the CA certificates bundle
RUN cat /etc/ssl/certs/cacert.pem >> /etc/ssl/certs/ca-certificates.crt

# Set the environment variable to use custom CA certificates globally
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/cacert.pem
ENV SSL_CERT_FILE=/etc/ssl/certs/cacert.pem

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
#ARG UID=10001
ARG UID=1000
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser


# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
COPY requirements.txt requirements.txt
RUN ls -l requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
# COPY ./client .


# Expose the port that the application listens on.
EXPOSE 5000

# Set the Flask app's entry point to be run.py
ENV FLASK_APP=run.py

# Run the application.
# CMD fastapi run main.py --port 8000 --host=0.0.0.0
#CMD ["flask", "run", "--host=0.0.0.0"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]