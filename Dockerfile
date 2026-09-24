# ─── Stage 1: Builder ────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Build wheels for dependencies to install quickly in the runner stage
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ─── Stage 2: Runner ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime dependencies:
#   libpq5 — required by psycopg2-binary
#   curl   — required by Docker healthcheck (curl -f http://localhost:8000/healthz)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Install wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY . /app/

# Create export directory for Celery worker shared files
RUN mkdir -p /app/exports

# Expose ports for FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501

# Default command (overridden by docker-compose per service)
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
