import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import torch
from optimum.intel import OVModelForFeatureExtraction
from transformers import AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openvino-embedder")

MODEL_ID = "BAAI/bge-large-en-v1.5"
OV_MODEL_PATH = "/models/bge-large-ov"
DOC_INSTRUCTION = "Represent this document for retrieval: "
QUERY_INSTRUCTION = "Represent this query for searching relevant passages: "

MAX_BATCH_SIZE = 16

model = None
tokenizer = None
_model_lock = threading.Lock()  # protects model inference (not thread-safe)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    logger.info("Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    logger.info(f"Loading OpenVINO INT8 Model from {OV_MODEL_PATH}...")
    model = OVModelForFeatureExtraction.from_pretrained(
        OV_MODEL_PATH, 
        device="CPU",
        ov_config={
            "PERFORMANCE_HINT": "THROUGHPUT",
            "NUM_STREAMS": "2",
            "INFERENCE_NUM_THREADS": "2",
        },
    )
    logger.info("Model loaded and compiled for Intel Xeon!")
    yield

app = FastAPI(lifespan=lifespan)

class EmbedRequest(BaseModel):
    texts: list[str]
    is_query: bool = False


def _embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts (guaranteed <= MAX_BATCH_SIZE)."""
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    with _model_lock:
        with torch.no_grad():
            outputs = model(**encoded)

    if isinstance(outputs, tuple):
        last_hidden_state = outputs[0]
    else:
        last_hidden_state = outputs.last_hidden_state

    # CLS pooling + L2 normalize
    embeddings = last_hidden_state[:, 0, :].cpu().numpy()
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / np.maximum(norms, 1e-12)
    return embeddings.tolist()


@app.post("/embed")
def embed(req: EmbedRequest):
    if len(req.texts) == 0:
        raise HTTPException(400, "texts must not be empty")

    instruction = QUERY_INSTRUCTION if req.is_query else DOC_INSTRUCTION
    prefixed = [f"{instruction}{t}" for t in req.texts]

    # Process in sub-batches to avoid OOM on long documents
    all_embeddings: list[list[float]] = []
    for i in range(0, len(prefixed), MAX_BATCH_SIZE):
        batch = prefixed[i : i + MAX_BATCH_SIZE]
        all_embeddings.extend(_embed_batch(batch))

    return {"embeddings": all_embeddings}


@app.get("/health")
def health():
    return {"status": "ok", "backend": "openvino", "model": MODEL_ID}