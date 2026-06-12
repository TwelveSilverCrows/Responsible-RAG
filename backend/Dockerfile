# =============================================================================
# Dockerfile — Production image for the RAG Chatbot API
# =============================================================================
# Build:  docker build -t rag-chatbot -f backend/Dockerfile .
# Run:    docker run -p 8000:8000 --env-file .env rag-chatbot
# =============================================================================

# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="your-team@example.com"
LABEL description="Canadian Academic RAG Chatbot — FastAPI"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ── Dependency layer (cached separately from source code) ─────────────────────
FROM base AS deps

WORKDIR /app

# Copy only the files uv needs to resolve & install dependencies
COPY pyproject.toml uv.lock ./

# Create empty src/ so the hatchling editable install succeeds
# (dependencies get cached; real source is added in the app stage)
RUN mkdir -p src

# Install project dependencies into the system Python
RUN uv pip install --system --no-cache -e .

# ── Application layer ─────────────────────────────────────────────────────────
FROM deps AS app

WORKDIR /app

# Copy backend source (app.py and src/)
COPY backend/app.py .
COPY backend/src/ ./src/

# Create volume mount points
RUN mkdir -p /app/resources /app/vectordb

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8000/api/v1/health || exit 1

# Run as non-root for security
RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

# ── Entrypoint ────────────────────────────────────────────────────────────────
# Single worker — async handles many concurrent requests without extra processes.
# Workers=1 keeps memory usage minimal.
# --no-server-header saves a few bytes per response (minor but free).
CMD ["uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--no-server-header", \
     "--loop", "uvloop"]
