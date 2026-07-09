import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
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

model = None
tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, tokenizer
    logger.info("Loading Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    logger.info(f"Loading OpenVINO INT8 Model from {OV_MODEL_PATH}...")
    # device="CPU" ensures it uses the Xeon's AVX-512/AMX instructions
    model = OVModelForFeatureExtraction.from_pretrained(
    OV_MODEL_PATH, 
    device="CPU",
    ov_config={
        "PERFORMANCE_HINT": "THROUGHPUT",
        "NUM_STREAMS": "2",             # ⬅️ Changed from "1" to "2" (One stream per vCPU)
        "INFERENCE_NUM_THREADS": "2",   # ⬅️ Changed from "1" to "2"
        "ENABLE_CPU_PINNING": "YES",    
    }
)
    logger.info("Model loaded and compiled for Intel Xeon!")
    yield

app = FastAPI(lifespan=lifespan)

class EmbedRequest(BaseModel):
    texts: list[str]
    is_query: bool = False

def cls_pooling(last_hidden_state: torch.Tensor) -> np.ndarray:
    """Extract the [CLS] token (first token) for BGE models."""
    return last_hidden_state[:, 0, :].cpu().numpy()

def normalize(embeddings: np.ndarray) -> np.ndarray:
    """L2 normalize the embeddings."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / np.maximum(norms, 1e-12)

@app.post("/embed")
async def embed(req: EmbedRequest):
    instruction = QUERY_INSTRUCTION if req.is_query else DOC_INSTRUCTION
    texts = [f"{instruction}{t}" for t in req.texts]
    
    # Tokenize
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    
    # Inference
    with torch.no_grad():
        outputs = model(**encoded)
        
    # optimum-intel returns a tuple or object depending on version
    if isinstance(outputs, tuple):
        last_hidden_state = outputs[0]
    else:
        last_hidden_state = outputs.last_hidden_state

    # Pool & Normalize
    embeddings = cls_pooling(last_hidden_state)
    embeddings = normalize(embeddings)
    
    return {"embeddings": embeddings.tolist()}

@app.get("/health")
async def health():
    return {"status": "ok", "backend": "openvino", "model": MODEL_ID}