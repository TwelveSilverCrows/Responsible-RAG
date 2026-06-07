# =============================================================================
# Dockerfile — Production image for the RAG Chatbot
# =============================================================================
# Build:  docker build -t rag-chatbot -f backend/Dockerfile .
# Run:    docker run -p 8501:8501 --env-file .env rag-chatbot
# =============================================================================

# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

LABEL maintainer="your-team@example.com"
LABEL description="Canadian Academic RAG Chatbot — Streamlit UI"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
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
RUN mkdir -p /app/resources /app/chroma_db

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run as non-root for security
RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

# ── Entrypoint ────────────────────────────────────────────────────────────────
# STREAMLIT_ROOT_PATH allows serving behind a reverse proxy subpath
# e.g. STREAMLIT_ROOT_PATH=/backend → accessible at /backend/
ENTRYPOINT ["/bin/sh", "-c", " \
  base=\"${STREAMLIT_ROOT_PATH:+--server.baseUrlPath=$STREAMLIT_ROOT_PATH}\"; \
  exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    $base \
"]
