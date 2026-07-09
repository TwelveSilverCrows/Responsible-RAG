## Quick Start (uv)

```bash
# Install dependencies
uv sync

# Activate the environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Run the server (model must be exported first — see Dockerfile)
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1
```

## Docker Build (recommended for production)

The model is exported to INT8 during the Docker build — this shrinks it from
~1.3 GB (FP32) to ~350 MB and pre-compiles it for instant startup.

```bash
# Build the image (The model export will take ~2-3 minutes during build)
docker build -t bge-openvino-xeon .

# Run it
docker run -d --name bge-xeon --restart always -p 8080:8080 bge-openvino-xeon
```