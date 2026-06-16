FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        ffmpeg \
    && update-ca-certificates --fresh \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ── Dependencies (cached separately from source) ──────────────────────────────
FROM base AS deps
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN mkdir -p src && uv pip install --system --no-cache -e .

# ── Application ───────────────────────────────────────────────────────────────
FROM deps AS app
WORKDIR /app
COPY backend/app.py .
COPY backend/src/ ./src/
RUN mkdir -p /app/resources /app/vectordb

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/api/v1/health || exit 1

RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--no-server-header", \
     "--loop", "uvloop"]
