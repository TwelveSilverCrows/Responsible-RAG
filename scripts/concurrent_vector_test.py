#!/usr/bin/env python3
"""
concurrent_vector_test.py — [LEGACY] Stress-test comparison of TurboVec vs Qdrant
==================================================================================
**This script is kept for reference.** The project now uses Qdrant exclusively
as its vector database. Qdrant handles concurrency correctly out of the box
(point-level locking, no lost-update problem).

The original purpose of this test was to demonstrate the lost-update bug in
TurboVec's on-disk persistence model when multiple KnowledgeBase instances
write concurrently. Qdrant (external service with ACID semantics) does not
have this issue.

Usage
-----
    uv run python scripts/concurrent_vector_test.py
"""

import logging
import os
import shutil
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from pydantic_settings import BaseSettings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
# Silence noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

logger = logging.getLogger("concurrent_test")


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  Local embedding wrapper (SentenceTransformer via LangChain interface)
# ═══════════════════════════════════════════════════════════════════════════════

class LocalEmbeddings(Embeddings):
    """Wrap a SentenceTransformer model as a LangChain Embeddings instance."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        logger.info("Loading local model '%s' …", model_name)
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_sentence_embedding_dimension()
        logger.info("Model loaded (dim=%d).", self._dim)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        emb = self._model.encode(texts, normalize_embeddings=True)
        return emb.tolist()

    def embed_query(self, text: str) -> list[float]:
        emb = self._model.encode([text], normalize_embeddings=True)
        return emb[0].tolist()

    @property
    def dim(self) -> int:
        return self._dim


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  Generate three long text sequences (50 lines ≈ 400–600 words each)
# ═══════════════════════════════════════════════════════════════════════════════

TOPIC_1_LINES = [
    "Canada's healthcare system is a publicly funded universal system",
    "established under the Canada Health Act of 1984, which sets five",
    "key principles: public administration, comprehensiveness, universality,",
    "portability, and accessibility. Each province and territory manages",
    "its own health insurance plan, resulting in regional variations in",
    "coverage and service delivery. The system covers medically necessary",
    "hospital and physician services, but does not typically include",
    "prescription drugs, dental care, or vision care for adults. This has",
    "led to a growing debate about the need for a national pharmacare",
    "program to address the high cost of medications for Canadians.",
    "Wait times for specialized procedures remain a significant challenge,",
    "particularly for diagnostic imaging and elective surgeries. The",
    "Canadian Institute for Health Information reports that median wait",
    "times for hip replacements range from 20 to 52 weeks depending on",
    "the province. Telehealth services have expanded rapidly since 2020,",
    "improving access for rural and remote communities across the country.",
    "Indigenous health services fall under federal jurisdiction through",
    "Indigenous Services Canada, creating a distinct parallel system.",
    "The healthcare workforce is facing shortages of family physicians and",
    "nurses, with approximately 4.8 million Canadians lacking a regular",
    "primary care provider. Innovative models like team-based primary care",
    "and nurse practitioner-led clinics are being piloted in several provinces.",
    "Mental health coverage varies widely; some provinces offer limited",
    "counselling services while others have expanded access through",
    "community-based programs. The COVID-19 pandemic exposed vulnerabilities",
    "in public health infrastructure and accelerated the adoption of",
    "digital health technologies. Long-term care reform has become a",
    "national priority following reports of systemic failures during",
    "the pandemic. Home care and palliative care services are managed",
    "differently across jurisdictions, creating inequities in access.",
    "Health Canada regulates food safety, pharmaceutical approvals, and",
    "medical device standards at the federal level. The Patented Medicine",
    "Prices Review Board works to keep drug costs reasonable while",
    "maintaining incentives for pharmaceutical innovation. Medical tourism",
    "brings approximately 200,000 visitors annually for procedures ranging",
    "from cosmetic surgery to orthopedic treatments. Electronic medical",
    "record adoption has been uneven, with some provinces achieving near",
    "universal coverage while others lag significantly behind. Interprovincial",
    "licensing portability for healthcare professionals is being pursued",
    "through the Canadian Free Trade Agreement. The Health Accord between",
    "federal and provincial governments determines transfer payments and",
    "funding priorities for the next decade. Preventive health programs",
    "focus on chronic disease management, vaccination campaigns, and",
    "health promotion in schools and workplaces. Artificial intelligence",
    "is being deployed for medical imaging analysis, drug discovery, and",
    "predictive analytics in population health management. The healthcare",
    "sustainability challenge requires balancing rising costs with aging",
    "demographics and increasing demand for services across all regions.",
    "Community health centres play a vital role in serving underserved",
    "populations, including recent immigrants and low-income families.",
]

TOPIC_2_LINES = [
    "Responsible artificial intelligence requires a multidisciplinary",
    "approach that combines technical robustness with ethical principles.",
    "The OECD's AI Principles, adopted in 2019, establish five value-based",
    "principles: inclusive growth, human-centred values, transparency,",
    "robustness and safety, and accountability. These principles have been",
    "endorsed by over 40 countries and serve as a reference for national",
    "AI strategies worldwide. Algorithmic bias can arise from unbalanced",
    "training data, flawed model design, or inappropriate application of",
    "AI systems in contexts different from those they were developed for.",
    "Frameworks like fairness metrics, adversarial debiasing, and",
    "counterfactual fairness analysis help identify and mitigate such",
    "biases throughout the machine learning lifecycle. Explainable AI (XAI)",
    "methods including SHAP, LIME, and attention visualization provide",
    "insights into model decision-making processes for stakeholders.",
    "Privacy-preserving machine learning techniques such as differential",
    "privacy, federated learning, and homomorphic encryption allow",
    "organizations to train models without compromising individual privacy.",
    "The European Union's AI Act categorizes AI systems by risk level,",
    "imposing strict requirements on high-risk applications in critical",
    "domains like healthcare, transportation, and law enforcement. Canada's",
    "proposed Artificial Intelligence and Data Act (AIDA) would establish",
    "requirements for responsible AI development and deployment across",
    "federally regulated sectors. Model cards, datasheets, and system",
    "cards provide structured documentation that improves transparency",
    "and enables informed decision-making by users and regulators. Impact",
    "assessments for algorithmic systems help organizations identify",
    "potential harms before deployment, particularly for vulnerable",
    "populations. Continuous monitoring of deployed AI systems is essential",
    "to detect concept drift, performance degradation, or emergent biases",
    "over time. Human-in-the-loop systems maintain human oversight for",
    "high-stakes decisions while leveraging AI efficiency for routine",
    "tasks. Environmental sustainability of AI is an emerging concern,",
    "with large model training consuming significant energy and water",
    "resources. Green AI initiatives promote efficient model architectures,",
    "knowledge distillation, and renewable energy for data centres.",
    "Synthetic data generation offers a promising approach for training",
    "models while protecting sensitive information and addressing data",
    "scarcity in specialized domains. Auditing frameworks for AI systems",
    "are being developed by standards organizations including ISO and IEEE.",
    "The concept of algorithmic recourse ensures individuals can understand",
    "and challenge automated decisions that affect their rights or",
    "opportunities. Multi-stakeholder governance models bring together",
    "governments, industry, civil society, and academia to shape AI policy.",
    "Workforce transition strategies must address job displacement while",
    "creating new opportunities through reskilling and lifelong learning.",
    "Cultural diversity in AI development teams improves product outcomes",
    "and reduces the risk of culturally insensitive or inappropriate",
    "system behaviour. Open-source AI tools and frameworks democratize",
    "access to advanced capabilities while enabling community scrutiny",
    "of algorithms and training methodologies. International cooperation",
    "on AI safety research, including alignment and control problems,",
    "is critical as capabilities advance toward artificial general intelligence.",
    "Value alignment ensures AI systems understand and respect human",
    "preferences, cultural norms, and ethical boundaries across different",
    "contexts and applications. The responsible AI field continues to evolve",
    "rapidly as new capabilities emerge and societal understanding deepens.",
]

TOPIC_3_LINES = [
    "Vector databases are specialized storage systems designed to handle",
    "high-dimensional embedding vectors generated by machine learning models.",
    "They enable efficient similarity search across millions or billions of",
    "vectors using approximate nearest neighbour (ANN) algorithms such as",
    "HNSW (Hierarchical Navigable Small World), IVF (Inverted File Index),",
    "and product quantization. Popular vector database solutions include",
    "Qdrant, Pinecone, Weaviate, Milvus, Chroma, and TurboVec, each offering",
    "different trade-offs between speed, accuracy, cost, and scalability.",
    "Retrieval-Augmented Generation (RAG) combines vector search with large",
    "language models to ground AI responses in verifiable external knowledge.",
    "A typical RAG pipeline consists of document ingestion, chunking,",
    "embedding generation, vector storage, query retrieval, and LLM-based",
    "answer synthesis with source attribution. Chunking strategy significantly",
    "impacts retrieval quality; semantic chunking uses embedding similarity",
    "to find natural boundaries while fixed-size chunking offers simplicity.",
    "Hybrid retrieval systems combine dense vector search with sparse keyword",
    "methods like BM25 to capture both semantic meaning and exact term matches.",
    "Ensemble retrievers use reciprocal rank fusion to balance contributions",
    "from multiple retrieval strategies with configurable weights. Metadata",
    "filtering allows vector databases to restrict search to specific",
    "document collections, time ranges, or other categorical attributes.",
    "Concurrent access patterns in vector databases require careful locking",
    "strategies to prevent data corruption during simultaneous writes from",
    "multiple threads or processes. TurboVec uses a quantization-based",
    "approach that reduces memory footprint while maintaining high search",
    "accuracy, making it suitable for deployment on resource-constrained",
    "environments. Qdrant supports both in-memory and on-disk modes with",
    "REST and gRPC interfaces for flexible deployment architectures.",
    "Index building time and memory usage are critical considerations when",
    "choosing between different ANN algorithms for production systems.",
    "Multi-tenancy support allows vector databases to serve multiple",
    "applications or users with isolated data partitions and access controls.",
    "Real-time ingestion requires balancing write throughput with query",
    "latency, often achieved through incremental index updates and background",
    "optimization processes. The embedding model selection affects both",
    "retrieval quality and operational costs, with smaller models offering",
    "faster inference at the cost of some accuracy. Document re-ranking",
    "using cross-encoders can significantly improve final result quality by",
    "applying more computationally expensive scoring to top-k candidates.",
    "Context window limitations of LLMs constrain how many retrieved",
    "documents can be included in the prompt, necessitating careful ranking.",
    "Evaluation metrics for RAG systems include retrieval precision, recall,",
    "mean reciprocal rank, and answer faithfulness measured against human",
    "annotations. Monitoring vector database health involves tracking index",
    "size, query latency percentiles, cache hit ratios, and write throughput.",
    "Cloud vector database services provide managed infrastructure with",
    "automatic scaling, backup, and disaster recovery capabilities.",
    "Local vector databases are preferred for development, testing, and",
    "privacy-sensitive applications where data must remain on premises.",
    "The choice between sparse, dense, and hybrid retrieval depends on the",
    "nature of the corpus and the types of queries the system must handle.",
    "Adversarial robustness of retrieval systems is an active research area,",
    "focusing on defending against manipulation of indexed documents to",
    "influence search results. Versioning and rollback capabilities enable",
    "safe deployment of embedding model updates and index rebuilds in",
    "production environments without service interruption.",
]

TOPICS: dict[str, list[str]] = {
    "canadian_healthcare": TOPIC_1_LINES,
    "responsible_ai": TOPIC_2_LINES,
    "vector_databases": TOPIC_3_LINES,
}


def make_chunks(source_id: str, lines: list[str], chunk_size: int = 10) -> list[Document]:
    """Split a topic into multiple Document chunks (simulating real chunking)."""
    chunks: list[Document] = []
    for i in range(0, len(lines), chunk_size):
        chunk_text = "\n".join(lines[i:i + chunk_size])
        chunks.append(Document(
            page_content=chunk_text,
            metadata={
                "source_id": source_id,
                "chunk_index": i // chunk_size,
                "total_chunks": (len(lines) + chunk_size - 1) // chunk_size,
            },
        ))
    return chunks


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  TurboVec test — replicates FastAPI multi-instance pattern
# ═══════════════════════════════════════════════════════════════════════════════

def test_turbovec_concurrent(embedder: LocalEmbeddings) -> dict:
    """
    Stress-test KnowledgeBase (TurboVec) by simulating concurrent uploads.

    **Real-world scenario:**

    FastAPI creates one ``KnowledgeBase`` instance **per request**.  When N
    uploads happen concurrently, N instances each:

      1. Load the store from disk into their own in-memory copy
      2. Insert chunks into their private copy
      3. Persist their private copy to disk

    If instance B loaded *before* instance A persisted, B's in-memory state
    is stale — B doesn't know about A's documents.  When B persists, it
    overwrites A's data on disk.  This is the **lost-update** bug.

    This test:
      - Creates N ``KnowledgeBase`` instances (one per source).
      - Each instance inserts a unique source with multiple chunks.
      - After all finish, a **fresh** instance loads the store and checks
        how many sources / chunks survived.
    """
    result: dict = {
        "passed": False,
        "errors": [],
        "final_source_count": 0,
        "final_chunk_count": 0,
        "expected_sources": 0,
        "expected_chunks": 0,
        "surviving_sources": [],
        "missing_sources": [],
    }

    work_dir = Path(tempfile.mkdtemp(suffix="_turbovec_kb_test"))
    storage_dir = work_dir / "vectordb"
    storage_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("TurboVec — KnowledgeBase multi-instance test")
    logger.info("  storage_dir: %s", storage_dir)
    logger.info("=" * 60)

    # Build a minimal Settings object pointing at our temp directory
    class _TestSettings(BaseSettings):
        vectordb_dir: str = str(storage_dir)
        use_semantic_chunking: bool = False
        fallback_chunk_size: int = 1000
        chunk_overlap: int = 0
        max_chunk_size: int = 2000

        model_config = {"extra": "ignore"}

    settings = _TestSettings()
    CHUNK_SIZE = 10  # lines per chunk

    # Pre-compute chunks per source
    source_chunks: dict[str, list[Document]] = {}
    for sid, lines in TOPICS.items():
        source_chunks[sid] = make_chunks(sid, lines, chunk_size=CHUNK_SIZE)
        result["expected_sources"] += 1
        result["expected_chunks"] += len(source_chunks[sid])

    logger.info(
        "Expected: %d sources, %d total chunks",
        result["expected_sources"],
        result["expected_chunks"],
    )

    # ═════════════════════════════════════════════════════════════════════
    #  A.  Sequential baseline  (one KnowledgeBase, serial inserts)
    # ═════════════════════════════════════════════════════════════════════
    logger.info("─── A. Sequential baseline ───")
    seq_errors = 0
    try:
        from src.core.vector_store import KnowledgeBase as KB

        kb_seq = KB(settings, embedder)
        for sid, chunks in source_chunks.items():
            try:
                kb_seq.add_documents(
                    source_id=sid,
                    source_metadata={"title": f"Sequential: {sid}"},
                    docs=chunks,
                )
            except Exception as exc:
                logger.error("Sequential insert %s FAILED: %s", sid, exc)
                seq_errors += 1

        seq_count = kb_seq.source_count()
        logger.info("  Sequential: %d sources, %d errors", seq_count, seq_errors)
        if seq_errors:
            result["errors"].append(f"SEQ_BASELINE: {seq_errors} errors")
        del kb_seq
    except Exception as exc:
        logger.error("Sequential baseline crashed: %s", exc)
        result["errors"].append(f"SEQ_CRASH: {exc}")

    # Re-create a fresh KB to verify baseline persistence
    try:
        from src.core.vector_store import KnowledgeBase as KB
        kb_check = KB(settings, embedder)
        persisted_count = kb_check.source_count()
        logger.info("  After reload: %d sources persisted", persisted_count)
        if persisted_count != result["expected_sources"]:
            result["errors"].append(
                f"SEQ_PERSIST: expected {result['expected_sources']} sources, "
                f"got {persisted_count}"
            )
        del kb_check
    except Exception as exc:
        logger.error("Sequential reload crashed: %s", exc)
        result["errors"].append(f"SEQ_RELOAD_CRASH: {exc}")

    # ═════════════════════════════════════════════════════════════════════
    #  B.  Concurrent — each thread creates its OWN KnowledgeBase instance
    #      (exactly like FastAPI does per request)
    # ═════════════════════════════════════════════════════════════════════
    logger.info("─── B. Concurrent (N instances, no external lock) ───")

    # Delete the store so we start fresh
    for f in storage_dir.iterdir():
        if f.is_file():
            f.unlink()
        elif f.is_dir():
            shutil.rmtree(f)

    NUM_CONCURRENT = len(TOPICS)

    def insert_via_separate_kb(
        sid: str, chunks: list[Document]
    ) -> tuple[str, int, int]:
        """
        Simulate a FastAPI upload request:
          * Create a brand-new KnowledgeBase instance (loads from disk)
          * Add documents
          * Return (source_id, chunk_count, error_count)
        """
        from src.core.vector_store import KnowledgeBase as KB
        kb = KB(settings, embedder)
        try:
            chunk_ids = kb.add_documents(
                source_id=sid,
                source_metadata={"title": f"Concurrent: {sid}"},
                docs=chunks,
            )
            return sid, len(chunk_ids), 0
        except Exception as exc:
            logger.error("  KB insert %s FAILED: %s", sid, exc)
            return sid, 0, 1
        finally:
            del kb

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT) as pool:
        futures = [
            pool.submit(insert_via_separate_kb, sid, source_chunks[sid])
            for sid in TOPICS
        ]
        for future in as_completed(futures):
            try:
                sid, n_chunks, n_err = future.result(timeout=120)
                if n_err:
                    result["errors"].append(f"{sid}: insert failed")
                logger.debug("  %s → %d chunks inserted", sid, n_chunks)
            except Exception as exc:
                result["errors"].append(str(exc))

    elapsed = time.perf_counter() - t0
    logger.info(
        "  Finished in %.2fs — %d concurrent inserts, %d errors",
        elapsed,
        NUM_CONCURRENT,
        len(result["errors"]),
    )

    # ═════════════════════════════════════════════════════════════════════
    #  C.  Verify — fresh KnowledgeBase, count surviving sources/chunks
    # ═════════════════════════════════════════════════════════════════════
    logger.info("─── C. Verification ───")
    try:
        from src.core.vector_store import KnowledgeBase as KB
        kb_final = KB(settings, embedder)
        result["final_source_count"] = kb_final.source_count()
        surviving = kb_final.list_sources()
        result["surviving_sources"] = [s.get("source_id", "?") for s in surviving]
        total_chunks = 0
        for s in surviving:
            sid = s.get("source_id", "")
            total_chunks += kb_final.chunk_count(sid)
        result["final_chunk_count"] = total_chunks

        for sid in TOPICS:
            if sid not in result["surviving_sources"]:
                result["missing_sources"].append(sid)

        logger.info(
            "  Surviving: %d / %d sources, %d / %d chunks",
            result["final_source_count"],
            result["expected_sources"],
            result["final_chunk_count"],
            result["expected_chunks"],
        )
        if result["missing_sources"]:
            logger.error(
                "  MISSING sources (lost update!): %s",
                result["missing_sources"],
            )
        del kb_final
    except Exception as exc:
        logger.error("Verification crashed: %s", exc)
        result["errors"].append(f"VERIFY_CRASH: {exc}")

    # ── Pass / fail ────────────────────────────────────────────────────
    if (not result["errors"]
            and result["final_source_count"] == result["expected_sources"]
            and result["final_chunk_count"] == result["expected_chunks"]):
        result["passed"] = True
        logger.info(">>> TurboVec: PASSED — all data survived.")
    elif result["missing_sources"]:
        logger.warning(
            ">>> TurboVec: LOST UPDATE — %d source(s) missing!",
            len(result["missing_sources"]),
        )
    else:
        logger.warning(
            ">>> TurboVec: PARTIAL — %d / %d sources, %d / %d chunks",
            result["final_source_count"],
            result["expected_sources"],
            result["final_chunk_count"],
            result["expected_chunks"],
        )

    # Cleanup
    shutil.rmtree(work_dir, ignore_errors=True)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 3b. TurboVec FIX demonstration  —  shared singleton KnowledgeBase
# ═══════════════════════════════════════════════════════════════════════════════

def test_turbovec_fixed(embedder: LocalEmbeddings) -> dict:
    """
    Prove the fix: use a **shared singleton** KnowledgeBase (or external lock
    around KB creation) so all concurrent writers mutate the same in-memory
    store and only one ``_persist()`` call happens at the end.

    In FastAPI this means making ``SourceService`` (or ``KnowledgeBase``) a
    dependency-scoped singleton rather than creating a new instance per request.
    """
    result: dict = {
        "passed": False,
        "errors": [],
        "final_source_count": 0,
        "final_chunk_count": 0,
        "expected_sources": 0,
        "expected_chunks": 0,
        "surviving_sources": [],
        "missing_sources": [],
    }

    work_dir = Path(tempfile.mkdtemp(suffix="_turbovec_fixed_test"))
    storage_dir = work_dir / "vectordb"
    storage_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("TurboVec — FIXED: shared singleton KnowledgeBase")
    logger.info("  storage_dir: %s", storage_dir)
    logger.info("=" * 60)

    class _TestSettings(BaseSettings):
        vectordb_dir: str = str(storage_dir)
        use_semantic_chunking: bool = False
        fallback_chunk_size: int = 1000
        chunk_overlap: int = 0
        max_chunk_size: int = 2000
        model_config = {"extra": "ignore"}

    settings = _TestSettings()
    CHUNK_SIZE = 10

    source_chunks: dict[str, list[Document]] = {}
    for sid, lines in TOPICS.items():
        source_chunks[sid] = make_chunks(sid, lines, chunk_size=CHUNK_SIZE)
        result["expected_sources"] += 1
        result["expected_chunks"] += len(source_chunks[sid])

    logger.info("Expected: %d sources, %d chunks", result["expected_sources"], result["expected_chunks"])

    # ── Shared lock around KB instantiation ────────────────────────────
    # In production this could be a singleton KB, or a request-scoped lock
    # that ensures only one KnowledgeBase instance exists at a time.
    from src.core.vector_store import KnowledgeBase as KB
    _kb_lock = threading.Lock()
    _shared_kb: "KB | None" = None

    def get_kb() -> "KB":
        nonlocal _shared_kb
        if _shared_kb is None:
            with _kb_lock:
                if _shared_kb is None:  # double-checked locking
                    _shared_kb = KB(settings, embedder)
        return _shared_kb

    # Concurrent inserts — but all share the SAME KnowledgeBase
    logger.info("─── Concurrent inserts (shared singleton KB) ───")

    def insert_via_shared_kb(sid: str, chunks: list[Document]) -> tuple[str, int, int]:
        kb = get_kb()
        try:
            chunk_ids = kb.add_documents(
                source_id=sid,
                source_metadata={"title": f"Shared: {sid}"},
                docs=chunks,
            )
            return sid, len(chunk_ids), 0
        except Exception as exc:
            logger.error("  Shared KB insert %s FAILED: %s", sid, exc)
            return sid, 0, 1

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(TOPICS)) as pool:
        futures = [
            pool.submit(insert_via_shared_kb, sid, source_chunks[sid])
            for sid in TOPICS
        ]
        for future in as_completed(futures):
            try:
                sid, n_chunks, n_err = future.result(timeout=120)
                if n_err:
                    result["errors"].append(f"{sid}: insert failed")
                logger.debug("  %s → %d chunks", sid, n_chunks)
            except Exception as exc:
                result["errors"].append(str(exc))

    elapsed = time.perf_counter() - t0
    logger.info("  Finished in %.2fs — %d inserts, %d errors",
                elapsed, len(TOPICS), len(result["errors"]))

    # ── Verify ─────────────────────────────────────────────────────────
    logger.info("─── Verification ───")
    try:
        kb_final = get_kb()
        result["final_source_count"] = kb_final.source_count()
        surviving = kb_final.list_sources()
        result["surviving_sources"] = [s.get("source_id", "?") for s in surviving]
        total_chunks = 0
        for s in surviving:
            sid = s.get("source_id", "")
            total_chunks += kb_final.chunk_count(sid)
        result["final_chunk_count"] = total_chunks

        for sid in TOPICS:
            if sid not in result["surviving_sources"]:
                result["missing_sources"].append(sid)

        logger.info("  Surviving: %d / %d sources, %d / %d chunks",
                    result["final_source_count"], result["expected_sources"],
                    result["final_chunk_count"], result["expected_chunks"])
        if result["missing_sources"]:
            logger.error("  MISSING: %s", result["missing_sources"])
    except Exception as exc:
        logger.error("Verification crashed: %s", exc)
        result["errors"].append(f"VERIFY_CRASH: {exc}")

    if (not result["errors"]
            and result["final_source_count"] == result["expected_sources"]
            and result["final_chunk_count"] == result["expected_chunks"]):
        result["passed"] = True
        logger.info(">>> TurboVec FIX: PASSED — all data survived!")
    else:
        logger.warning(">>> TurboVec FIX: STILL FAILING")

    shutil.rmtree(work_dir, ignore_errors=True)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  Qdrant concurrent test — same multi-instance pattern
# ═══════════════════════════════════════════════════════════════════════════════

def test_qdrant_concurrent(embedder: LocalEmbeddings) -> dict:
    """
    Stress-test Qdrant local-mode with the same concurrent-instance pattern.

    Each thread creates its own ``QdrantClient`` pointing to the same
    storage directory.  Qdrant's local-mode uses a ``.lock`` file to
    prevent concurrent access — this test verifies that:

      * Sequential access works perfectly.
      * Concurrent access is **cleanly rejected** (no silent corruption).
      * An external lock serialises access successfully.
      * Storage remains intact and queryable after all writes.
    """
    result: dict = {
        "passed": False,
        "errors": [],
        "concurrent_error_count": 0,
        "concurrent_error_type": "",
        "final_count": 0,
        "final_source_ids": [],
        "expected_count": 0,
        "storage_files": {},
    }

    work_dir = Path(tempfile.mkdtemp(suffix="_qdrant_test"))
    data_dir = work_dir / "qdrant_data"
    logger.info("=" * 60)
    logger.info("Qdrant concurrent test  (data_dir=%s)", data_dir)
    logger.info("=" * 60)

    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        PointStruct,
        VectorParams,
    )

    COLLECTION = "concurrent_test"
    DIM = embedder.dim

    # Pre-compute embeddings
    source_texts = {sid: "\n".join(lines) for sid, lines in TOPICS.items()}
    source_vectors = {sid: embedder.embed_query(text) for sid, text in source_texts.items()}
    SIDS = list(TOPICS.keys())
    expected_points = len(SIDS)
    result["expected_count"] = expected_points
    logger.info("Pre-computed embeddings for %d sources.", len(source_vectors))

    # ═════════════════════════════════════════════════════════════════════
    #  A.  Sequential baseline
    # ═════════════════════════════════════════════════════════════════════
    logger.info("─── A. Sequential baseline ───")
    try:
        client = QdrantClient(path=str(data_dir))
        if client.collection_exists(COLLECTION):
            client.delete_collection(COLLECTION)
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
            shard_number=4
        )
        base_errors = 0
        for idx, sid in enumerate(SIDS, start=1):
            try:
                client.upsert(
                    collection_name=COLLECTION,
                    points=[PointStruct(
                        id=idx, vector=source_vectors[sid],
                        payload={"source_id": sid, "text": source_texts[sid][:200]},
                    )],
                )
            except Exception as exc:
                logger.error("Seq upsert %d (%s) FAILED: %s", idx, sid, exc)
                base_errors += 1
        base_count = client.count(COLLECTION).count
        logger.info("  → %d points, %d errors", base_count, base_errors)
        if base_errors:
            result["errors"].append(f"SEQ_BASELINE: {base_errors} errors")
        client.close()

        c2 = QdrantClient(path=str(data_dir))
        c2c = c2.count(COLLECTION).count
        logger.info("  After reopen: %d points", c2c)
        if c2c != expected_points:
            result["errors"].append(f"SEQ_PERSIST: expected {expected_points}, got {c2c}")
        c2.close()
    except Exception as exc:
        logger.error("Sequential baseline crashed: %s", exc)
        result["errors"].append(f"SEQ_CRASH: {exc}")

    # ═════════════════════════════════════════════════════════════════════
    #  B.  Concurrent — each thread creates its OWN QdrantClient
    # ═════════════════════════════════════════════════════════════════════
    logger.info("─── B. Concurrent (N clients, no lock) ───")
    client = QdrantClient(path=str(data_dir))
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
    )
    client.close()

    import itertools
    _counter = itertools.count(1)

    def upsert_source(sid: str, vec: list[float]) -> str:
        c = QdrantClient(path=str(data_dir), shard_number=4)
        try:
            pid = next(_counter)
            c.upsert(
                collection_name=COLLECTION,
                points=[PointStruct(
                    id=pid, vector=vec,
                    payload={"source_id": sid, "text": source_texts[sid][:200]},
                )],
            )
            return f"ok:{pid}"
        finally:
            c.close()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(SIDS)) as pool:
        futures = [pool.submit(upsert_source, sid, source_vectors[sid]) for sid in SIDS]
        for future in as_completed(futures):
            try:
                future.result(timeout=30)
            except Exception as exc:
                result["errors"].append(str(exc))

    elapsed = time.perf_counter() - t0
    result["concurrent_error_count"] = len(result["errors"])
    error_types = set()
    for e in result["errors"]:
        error_types.add(e.split(".")[0] if "." in e else e[:80])
    result["concurrent_error_type"] = "; ".join(sorted(error_types))
    logger.info(
        "  → %d tasks, %.2fs, %d errors",
        len(SIDS), elapsed, len(result["errors"]),
    )

    # ═════════════════════════════════════════════════════════════════════
    #  C.  Lock-guarded serialised
    # ═════════════════════════════════════════════════════════════════════
    logger.info("─── C. Lock-guarded serialised ───")
    _write_lock = threading.Lock()
    _counter2 = itertools.count(100)
    lock_errors = 0

    def upsert_locked(sid: str, vec: list[float]) -> str:
        with _write_lock:
            c = QdrantClient(path=str(data_dir), shard_number=4)
            try:
                pid = next(_counter2)
                c.upsert(
                    collection_name=COLLECTION,
                    points=[PointStruct(
                        id=pid, vector=vec,
                        payload={"source_id": sid, "text": source_texts[sid][:200]},
                    )],
                )
                return f"ok:{pid}"
            finally:
                c.close()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(SIDS)) as pool:
        futures = [pool.submit(upsert_locked, sid, source_vectors[sid]) for sid in SIDS]
        for future in as_completed(futures):
            try:
                future.result(timeout=30)
            except Exception as exc:
                logger.error("Lock-guarded upsert FAILED: %s", exc)
                lock_errors += 1
    elapsed = time.perf_counter() - t0
    if lock_errors:
        result["errors"].append(f"LOCK_FAILED: {lock_errors} errors")
    logger.info("  → %d tasks, %.2fs, %d errors",
                len(SIDS), elapsed, lock_errors)

    # ═════════════════════════════════════════════════════════════════════
    #  D.  Storage integrity check
    # ═════════════════════════════════════════════════════════════════════
    logger.info("─── D. Integrity check ───")
    try:
        check = QdrantClient(path=str(data_dir), shard_number=4)
        count = check.count(COLLECTION).count
        result["final_count"] = count
        logger.info("  Collection count: %d", count)

        try:
            sr = check.query_points(
                collection_name=COLLECTION,
                query=source_vectors[SIDS[0]], limit=10,
            )
            result["final_source_ids"] = [
                (h.id, h.payload.get("source_id"), round(h.score, 4))
                for h in sr.points
            ]
            logger.info("  Search: %d hits", len(sr.points))
        except Exception as exc:
            logger.error("Search FAILED: %s", exc)
            result["errors"].append(f"SEARCH: {exc}")

        try:
            pts, _ = check.scroll(COLLECTION, limit=500)
            logger.info("  Scroll: %d points", len(pts))
            bad = [p.id for p in pts if not p.payload or not p.payload.get("source_id")]
            if bad:
                result["errors"].append(f"CORRUPT_PAYLOADS: {len(bad)} points")
        except Exception as exc:
            logger.error("Scroll FAILED: %s", exc)
            result["errors"].append(f"SCROLL: {exc}")

        for f in sorted(data_dir.rglob("*")):
            if f.is_file():
                result["storage_files"][f.name] = f.stat().st_size
        logger.info("  Files: %s", {k: f"{v:,} bytes" for k, v in result["storage_files"].items()})
        check.close()
    except Exception as exc:
        logger.error("Integrity crashed: %s", exc)
        result["errors"].append(f"INTEGRITY: {exc}")

    # ── Pass / fail ────────────────────────────────────────────────────
    real_errors = [e for e in result["errors"] if "already accessed" not in e]
    if not real_errors and result["final_count"] >= result["expected_count"]:
        result["passed"] = Truewki
        logger.info(">>> Qdrant: PASSED (no corruption).")
    elif real_errors:
        logger.warning(">>> Qdrant: %d unexpected error(s)", len(real_errors))
    else:
        logger.warning(">>> Qdrant: FAIL")

    shutil.rmtree(work_dir, ignore_errors=True)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  Main
# ═══════════════════════════════════════════════════════════════════════════════

def print_separator(title: str) -> None:
    width = 70
    pad = (width - len(title) - 2) // 2
    print()
    print("╔" + "═" * width + "╗")
    print(f"║{' ' * pad} {title} {' ' * (width - pad - len(title) - 2)}║")
    print("╚" + "═" * width + "╝")
    print()


def main() -> int:
    print_separator("CONCURRENT VECTOR-STORE STRESS TEST")
    print("Local embeddings · Multi-instance pattern (like FastAPI)")
    print()

    embedder = LocalEmbeddings()

    # ── 1. TurboVec ────────────────────────────────────────────────────
    print_separator("TurboVec — multi-instance test")
    tv = test_turbovec_concurrent(embedder)
    print()
    print(f"  Passed:             {tv['passed']}")
    print(f"  Errors:             {len(tv['errors'])}")
    if tv['errors']:
        for e in tv['errors'][:5]:
            print(f"    · {e}")
    print(f"  Expected sources:   {tv['expected_sources']}")
    print(f"  Surviving sources:  {tv['final_source_count']}")
    print(f"  Expected chunks:    {tv['expected_chunks']}")
    print(f"  Surviving chunks:   {tv['final_chunk_count']}")
    if tv['missing_sources']:
        print(f"  ❌ LOST UPDATES:    {tv['missing_sources']}")
    else:
        print(f"  ✅ All sources accounted for")

    # ── 1b. TurboVec FIX (shared singleton KB) ─────────────────────────
    print_separator("TurboVec — FIX (shared singleton KB)")
    tv_fixed = test_turbovec_fixed(embedder)
    print()
    print(f"  Passed:             {tv_fixed['passed']}")
    print(f"  Errors:             {len(tv_fixed['errors'])}")
    if tv_fixed['errors']:
        for e in tv_fixed['errors'][:5]:
            print(f"    · {e}")
    print(f"  Expected sources:   {tv_fixed['expected_sources']}")
    print(f"  Surviving sources:  {tv_fixed['final_source_count']}")
    print(f"  Expected chunks:    {tv_fixed['expected_chunks']}")
    print(f"  Surviving chunks:   {tv_fixed['final_chunk_count']}")
    if tv_fixed['missing_sources']:
        print(f"  ❌ STILL LOST:      {tv_fixed['missing_sources']}")
    else:
        print(f"  ✅ All sources accounted for")

    # ── 2. Qdrant ──────────────────────────────────────────────────────
    print_separator("Qdrant — multi-instance test")
    qd = test_qdrant_concurrent(embedder)
    print()
    print(f"  Passed:             {qd['passed']}")
    print(f"  Errors:             {len(qd['errors'])}")
    if qd['errors']:
        for e in qd['errors'][:5]:
            print(f"    · {e}")
    print(f"  Expected points:    {qd['expected_count']}")
    print(f"  Final points:       {qd['final_count']}")

    # ── Summary ────────────────────────────────────────────────────────
    print_separator("SUMMARY")
    tv_status = "✅ PASS" if tv["passed"] else "❌ FAIL"
    tv_fixed_status = "✅ PASS" if tv_fixed["passed"] else "❌ FAIL"
    qd_status = "✅ PASS" if qd["passed"] else "❌ FAIL"

    print(f"  TurboVec (multi-instance) → {tv_status}")
    print(f"     Sources: {tv['final_source_count']}/{tv['expected_sources']}  "
          f"Chunks: {tv['final_chunk_count']}/{tv['expected_chunks']}")
    if tv['missing_sources']:
        print(f"     ❌ Lost updates: {tv['missing_sources']}")
    print()
    print(f"  TurboVec (shared singleton) → {tv_fixed_status}")
    print(f"     Sources: {tv_fixed['final_source_count']}/{tv_fixed['expected_sources']}  "
          f"Chunks: {tv_fixed['final_chunk_count']}/{tv_fixed['expected_chunks']}")
    print()
    print(f"  Qdrant (local) → {qd_status}")
    print(f"     Points: {qd['final_count']}/{qd['expected_count']}")
    print()
    return 0


if __name__ == "__main__":
    main()
