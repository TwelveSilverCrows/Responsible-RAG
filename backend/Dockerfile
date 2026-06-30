# =============================================================================
# Dockerfile — Backend (FastAPI)
# =============================================================================
# Multi-stage: builder has build-essential for compiling deps;
# the runtime stage is a clean slim image with only what's needed.
# =============================================================================

FROM python:3.12-slim AS builder

# Build-time deps (compilers, etc.) — NOT in the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN mkdir -p src && uv pip install --system --no-cache -e .

# ── Runtime ───────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS app

# Only runtime-needed apt packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        ffmpeg \
    && update-ca-certificates --fresh \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder (includes compiled .so files)
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app
COPY backend/app.py .
COPY backend/src/ ./src/
RUN mkdir -p /app/resources /app/vectordb

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/api/v1/health || exit 1

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--no-server-header", \
     "--loop", "uvloop"]
