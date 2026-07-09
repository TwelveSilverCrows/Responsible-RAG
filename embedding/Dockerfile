# ============================================================
# STAGE 1 — Builder: install deps + export model (with build tools)
# ============================================================
FROM python:3.12-slim AS builder

# Build tools — only in this stage, stripped from final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install all Python dependencies (CPU-only torch, no CUDA)
RUN uv pip install --system \
    "fastapi==0.111.0" \
    "uvicorn==0.30.1" \
    "optimum-intel[openvino]>=1.27,<2" \
    "transformers>=4.41,<5" \
    "torch>=2.4,<3" \
    "numpy>=1.26,<2" \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --index-strategy unsafe-best-match \
    --no-cache

# EXPORT THE MODEL TO INT8
# Shrinks the model from 1.3GB (FP32) to ~350MB (INT8)
# and pre-compiles it so the server starts instantly.
RUN optimum-cli export openvino \
    --model BAAI/bge-large-en-v1.5 \
    --weight-format int8 \
    --task feature-extraction \
    /models/bge-large-ov

# Clean up ~1.3GB of HuggingFace model cache (original FP32 weights no longer needed)
RUN rm -rf /root/.cache/huggingface

# ============================================================
# STAGE 2 — Runtime: minimal Python, no build tools
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Copy Python packages + binaries from builder (includes uvicorn, optimum-cli, etc.)
COPY --from=builder /usr/local /usr/local
# Copy the exported INT8 model (~350MB)
COPY --from=builder /models /models
# Copy the app
COPY main.py .

# Run with Uvicorn.
# 1 worker because OpenVINO handles internal CPU threading automatically via NUM_STREAMS="AUTO".
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]