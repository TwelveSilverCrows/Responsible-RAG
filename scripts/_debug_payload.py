"""Quick debug: see how QdrantVectorStore interprets stored payloads."""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore, FastEmbedSparse, RetrievalMode
from src.core.config import get_settings
from src.core.embeddings import EmbeddingFactory

settings = get_settings()
embeddings = EmbeddingFactory.create(settings)

client = QdrantClient(
    url=f"http://{settings.qdrant_host}:{settings.qdrant_port}",
    timeout=120,
)

# Raw Qdrant payload
result = client.scroll(
    settings.qdrant_profiles_collection_name, limit=1, with_payload=True,
)
pt = result[0][0]
print("=== Raw payload keys ===")
print(list(pt.payload.keys()))
print("text[:200]:", pt.payload.get("text", "")[:200])

# LangChain vector store (HYBRID mode, matching build_profiles_kb.py)
vs = QdrantVectorStore(
    client=client,
    collection_name=settings.qdrant_profiles_collection_name,
    embedding=embeddings,
    sparse_embedding=FastEmbedSparse(
        model_name="Qdrant/bm42-all-minilm-l6-v2-attentions",
    ),
    retrieval_mode=RetrievalMode.HYBRID,
)
retriever = vs.as_retriever(search_kwargs={"k": 3})
docs = retriever.invoke("gender identity")

print(f"\n=== Docs returned: {len(docs)} ===")
for i, d in enumerate(docs):
    print(f"\nDoc {i}:")
    print(f"  page_content length: {len(d.page_content)}")
    print(f"  page_content[:150]: {d.page_content[:150]!r}")
    print(f"  metadata keys: {list(d.metadata.keys())}")
    print(f"  source_id: {d.metadata.get('source_id', 'N/A')}")
    print(f"  title: {d.metadata.get('title', 'N/A')}")
