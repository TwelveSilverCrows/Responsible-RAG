# Text Embeddings Inference (TEI) — CPU server

This directory holds the configuration for the **Hugging Face Text Embeddings Inference (TEI)** server that powers the RAG chatbot's embedding backend.

## Quick start

```bash
docker run -d --restart always \
  --name tei-embedder \
  --cpus 2 \
  -p 8080:80 \
  -v $PWD/data:/data \
  ghcr.io/huggingface/text-embeddings-inference:cpu-latest \
  --model-id BAAI/bge-large-en-v1.5 \
  --max-client-batch-size 128 \
  --max-concurrent-requests 64
```

This starts the TEI server on port **8080** using the same `BAAI/bge-large-en-v1.5` model used by the rest of the project.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (returns `200 OK` with no body) |
| `/embed` | POST | Returns normalized embeddings |

### Embed request

```json
{"inputs": "text to embed", "normalize": true}
{"inputs": ["text1", "text2"], "normalize": true}
```

### Embed response

TEI returns raw `[[float]]` — a list of embedding vectors.

## Configuration

The backend connects to TEI via the `.env` variables:

```
EMBEDDING_PROVIDER=tei
LOCAL_EMBEDDING_URL=http://<server-address>:8080/embed
```

See `example.env` at the project root for details.
