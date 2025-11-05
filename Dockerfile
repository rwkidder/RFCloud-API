# =============================
# Stage 1: Build environment
# =============================
FROM python:3.12-slim AS build

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install build dependencies (for psycopg/asyncpg compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files first for caching
COPY requirements.txt .

# Install Python dependencies into /opt/venv
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# =============================
# Stage 2: Runtime image
# =============================
FROM python:3.12-slim

# Copy virtualenv from builder
COPY --from=build /opt/venv /opt/venv

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Set workdir
WORKDIR /app

# Copy app source
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Default command — use multiple workers for async
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
