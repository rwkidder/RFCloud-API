# ----------------------------
# Stage 1: lightweight Python base
# ----------------------------
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files & enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system packages required by asyncpg & matplotlib
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# Stage 2: install dependencies
# ----------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------
# Stage 3: copy source code
# ----------------------------
COPY . .

# Expose FastAPI port
EXPOSE 8000

# ----------------------------
# Stage 4: start FastAPI
# ----------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
