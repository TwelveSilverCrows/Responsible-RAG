FROM python:3.10-slim

# Install system dependencies for OpenVINO, build tools, and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install Python dependencies via uv (pyproject.toml + uv.lock)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache --no-dev

# EXPORT THE MODEL TO INT8 DURING BUILD
# This is CRITICAL: It shrinks the model from 1.3GB (FP32) to ~350MB (INT8)
# and pre-compiles it so the server starts instantly and fits in low-RAM environments.
RUN uv run optimum-cli export openvino \
    --model BAAI/bge-large-en-v1.5 \
    --weight-format int8 \
    --task feature-extraction \
    /models/bge-large-ov

COPY main.py .

# Run with Uvicorn. 
# We use 1 worker because OpenVINO handles internal CPU threading automatically via NUM_STREAMS="AUTO".
# Multiple Uvicorn workers would just fight for the same CPU cores and RAM.
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]