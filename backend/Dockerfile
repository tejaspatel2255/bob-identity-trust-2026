# Base Image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for caching optimization
COPY requirements.txt /app/

# Install Python package dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
# We expect to run docker build from the workspace root or from the backend directory.
# This copy covers copying the backend directory.
COPY . /app/backend/

# Expose FastAPI default port
EXPOSE 8000

# Start command running Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
