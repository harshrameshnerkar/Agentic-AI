# ==============================================================================
# OpsSentinel Enterprise Agent - Production Multi-Stage Container Image (Day 15)
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY day_15/requirements.txt .
RUN pip install --user -r requirements.txt

# Final Minimal Runtime Stage
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    ENVIRONMENT=production \
    API_PORT=8000 \
    DASHBOARD_PORT=8501

RUN useradd -u 10001 -m -s /bin/bash appuser

COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY day_15 /app/day_15

# Ensure directory permissions for SQLite WAL & audit trail
RUN mkdir -p /app/day_15/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command launches the FastAPI production microservice
CMD ["python", "-m", "uvicorn", "day_15.session_1.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
