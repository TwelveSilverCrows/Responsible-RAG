FROM python:3.10-slim

# Install system dependencies for OpenVINO and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install all Python dependencies.
# Uses the CPU-only PyTorch index as PRIMARY so torch is pulled WITHOUT
# CUDA/NVIDIA libraries (~2 GB saved). Everything else falls back to PyPI.
RUN uv pip install --system \
    fastapi==0.111.0 \
    uvicorn==0.30.1 \
    "optimum-intel[openvino]==1.18.0" \
    optimum==1.20.0 \
    transformers==4.41.2 \
    "torch==2.3.1+cpu" \
    numpy==1.26.4 \
    openvino==2024.6.0 \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple \
    --no-cache

# EXPORT THE MODEL TO INT8 DURING BUILD
# This is CRITICAL: It shrinks the model from 1.3GB (FP32) to ~350MB (INT8)
# and pre-compiles it so the server starts instantly and fits in low-RAM environments.
RUN optimum-cli export openvino \
    --model BAAI/bge-large-en-v1.5 \
    --weight-format int8 \
    --task feature-extraction \
    /models/bge-large-ov

COPY main.py .

# Run with Uvicorn.
# We use 1 worker because OpenVINO handles internal CPU threading automatically via NUM_STREAMS="AUTO".
# Multiple Uvicorn workers would just fight for the same CPU cores and RAM.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]