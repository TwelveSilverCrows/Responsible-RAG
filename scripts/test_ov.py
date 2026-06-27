"""Quick test: verify OpenVINO model loads and produces embeddings."""
import sys, time
sys.path.insert(0, "backend")
from langchain_community.embeddings import OpenVINOBgeEmbeddings

t0 = time.time()
emb = OpenVINOBgeEmbeddings(
    model_name_or_path="BAAI/bge-large-en-v1.5",
    model_kwargs={"device": "GPU"},
    encode_kwargs={"normalize_embeddings": True, "batch_size": 4},
    query_instruction="Represent this query for searching relevant passages: ",
    embed_instruction="Represent this document for retrieval: ",
)
print(f"Model loaded in {time.time()-t0:.1f}s")

result = emb.embed_query("test query about health literacy")
print(f"Embedding dimension: {len(result)}")
print("OK")
