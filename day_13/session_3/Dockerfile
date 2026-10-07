# ==============================================================================
# Multi-Stage Secure Dockerfile for OpsSentinel Agent Service
# ==============================================================================
# Security Best Practices:
#   1. Minimal footprint via python:3.12-slim
#   2. Multi-stage build to isolate build tools from production runtime
#   3. Execution as non-root user (appuser, UID 10001)
#   4. Built-in HEALTHCHECK instruction
#   5. ZERO secrets or credentials baked into image layers
# ==============================================================================

# STAGE 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies to temporary virtual environment
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# STAGE 2: Production Distroless/Slim Runtime
FROM python:3.12-slim AS runtime

# Create dedicated non-root application user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Copy isolated virtualenv from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source code with proper non-root ownership
COPY --chown=appuser:appgroup . /app

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    APP_ENV=production

# Switch to non-privileged user
USER appuser

# Expose service port
EXPOSE 8000

# Container liveness healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start production ASGI server with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
