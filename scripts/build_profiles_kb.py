#!/usr/bin/env python3
"""
build_profiles_kb.py — Build a dedicated vector store for profile generation
==============================================================================
Ingests PDFs and web links from ``resources/profiles/`` into a Qdrant
collection (``rag_profiles_collection``) using the TEI embedding server
(BAAI/bge-large-en-v1.5).

Usage
-----
    uv run python scripts/build_profiles_kb.py

What it does
------------
1. **PDFs** — extracts full text + metadata (author, year, title, DOI) via
   PyMuPDF and heuristic parsing.
2. **Web links** — fetches each URL, extracts page title & main content via
   BeautifulSoup, along with visible metadata.
3. **Chunking** — uses the project's ``SmartChunker`` (semantic → recursive
   fallback).
4. **Embeddings** — TEI server (BAAI/bge-large-en-v1.5).
5. **Storage** — all chunks + metadata upserted into a Qdrant collection.
"""

import argparse
import concurrent.futures
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# ── Ensure backend/src is on sys.path ─────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# ── Load .env for API tokens (HuggingFace, etc.) ─────────────────────────
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_profiles_kb")


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Paths (relative to project root)
PDF_DIR = PROJECT_ROOT.parent / "storage" / "resources" / "profiles" / "pdf"
LINKS_FILE = PROJECT_ROOT.parent / "storage" / "resources" / "profiles" / "links.txt"

# Embedding model
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
EMBEDDING_DEVICE = "GPU"

# Chunking
USE_SEMANTIC_CHUNKING = False  # CPU-only: disable semantic (no GPU for chunking)
FALLBACK_CHUNK_SIZE = 800
CHUNK_OVERLAP = 300
MAX_CHUNK_SIZE = 2000

# URL fetch timeout (seconds)
URL_TIMEOUT = 15


# ═══════════════════════════════════════════════════════════════════════════════
# PDF extraction
# ═══════════════════════════════════════════════════════════════════════════════

def extract_pdf_metadata(filepath: Path) -> dict:
    """
    Extract metadata from a PDF using PyMuPDF.

    Returns a dict with keys: title, authors, year, doi, source_type.
    Heuristics are applied when the PDF's internal metadata is sparse.
    """
    import fitz  # PyMuPDF

    meta: dict = {
        "title": "",
        "authors": [],
        "year": "",
        "doi": "",
        "source_type": "pdf",
    }

    doc = fitz.open(str(filepath))
    try:
        # ── Internal PDF metadata ─────────────────────────────────────────────
        pdf_meta = doc.metadata or {}
        raw_title = (pdf_meta.get("title") or "").strip()
        raw_author = (pdf_meta.get("author") or "").strip()
        raw_subject = (pdf_meta.get("subject") or "").strip()

        if raw_title:
            meta["title"] = raw_title
        if raw_author:
            # Split multiple authors by semicolon, comma, or " and "
            authors = re.split(r"[;,]\s*|\s+and\s+", raw_author)
            meta["authors"] = [a.strip() for a in authors if a.strip()]

        # ── Heuristic: first page text for title & DOI ─────────────────────
        if not meta["title"] or not meta["doi"]:
            first_page = doc[0]
            text = first_page.get_text("text")[:2000]

            # Title: first non-empty, non-short line on page 1
            if not meta["title"]:
                for line in text.split("\n"):
                    line = line.strip()
                    if len(line) > 15 and not line.startswith(("http", "DOI", "doi", "©")):
                        meta["title"] = line[:300]
                        break

            # DOI
            doi_match = re.search(
                r"(?:doi|DOI|Doi)[:\s]*+(10\.\d{4,}/[^\s,;]+)",
                text,
            )
            if doi_match:
                meta["doi"] = doi_match.group(1).rstrip(".")

        # ── Year from filename (common pattern: YYYY or article number) ────
        if not meta["year"]:
            stem = filepath.stem
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", stem)
            if year_match:
                meta["year"] = year_match.group(1)

        # ── Fallback: filename as title ────────────────────────────────────
        if not meta["title"]:
            meta["title"] = filepath.stem

        # ── Context lines (total pages, word count) ────────────────────────
        meta["page_count"] = doc.page_count
        full_text = "".join(page.get_text("text") for page in doc)
        meta["word_count"] = len(full_text.split())

    finally:
        doc.close()

    return meta


def extract_pdf_content(filepath: Path) -> str:
    """
    Convert a PDF to clean markdown, stripping reference/bibliography sections.

    Uses ``pymupdf4llm`` for structure-preserving extraction (headings, lists)
    which yields better embeddings than raw ``page.get_text("text")``.
    Reference sections common in academic PDFs are removed to avoid polluting
    the vector store with citation noise.
    """
    import fitz  # PyMuPDF
    import pymupdf4llm
    import re

    doc = fitz.open(str(filepath))
    try:
        md = pymupdf4llm.to_markdown(
            doc,
            header=False,
            footer=False,
            page_separators=True,
            ignore_images=True,
            write_images=False,
            image_path=None,
        )
    finally:
        doc.close()

    # ── Strip reference / bibliography sections ────────────────────────────
    ref_patterns = (
        r'^#{1,3}\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY'
        r'|Works\s+Cited|WORKS\s+CITED'
        r'|References\s+and\s+Notes|REFERENCES\s+AND\s+NOTES'
        r'|Cited\s+References|CITED\s+REFERENCES'
        r'|References\s+and\s+Further\s+Reading'
        r'|Reference\s+List|REFERENCE\s+LIST)\s*$'
    )

    lines = md.split("\n")
    ref_start = None
    for i, line in enumerate(lines):
        if re.match(ref_patterns, line.strip()):
            ref_start = i
            break

    if ref_start is not None:
        md = "\n".join(lines[:ref_start])

    # Clean surrogate characters
    md = md.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="ignore")

    return md.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# Webpage extraction (via WebBaseLoader)
# ═══════════════════════════════════════════════════════════════════════════════

_WEB_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_webpage_docs(url: str, timeout: int = 15) -> Optional[list]:
    """
    Fetch a URL using ``WebBaseLoader`` and return LangChain Documents.

    Returns a list of :class:`Document` objects (one per page) with
    ``page_content`` (full text) and ``metadata`` (source, title,
    description, language).  Returns ``None`` on failure.
    """
    from langchain_community.document_loaders import WebBaseLoader

    try:
        loader = WebBaseLoader(
            web_paths=[url],
            header_template=_WEB_HEADERS,
            requests_kwargs={"timeout": timeout},
            raise_for_status=False,
            # Strip nav, footer, etc. for cleaner content
            bs_kwargs={"parse_only": None},
            bs_get_text_kwargs={"strip": True},
        )
        docs = loader.load()
        if not docs:
            logger.warning("  No content returned from %s", url)
            return None

        # Enrich metadata with domain & source_type
        for doc in docs:
            doc.metadata["domain"] = urlparse(url).netloc
            doc.metadata["url"] = url
            doc.metadata["source_type"] = "webpage"
            # Convert "language" html attr to "year" if it looks like a year
            lang = doc.metadata.get("language", "")
            if lang and lang.isdigit() and len(lang) == 4:
                doc.metadata["year"] = lang
                doc.metadata["language"] = ""

        return docs
    except Exception as exc:
        logger.warning("  Failed to fetch %s: %s", url, exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Embedding factory (TEI server)
# ═══════════════════════════════════════════════════════════════════════════════

def create_embeddings():
    """Create a TEI embedding client pointing at the remote server."""
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
    from src.core.config import get_settings
    from src.core.embeddings import TEIEmbeddings

    settings = get_settings()
    url = settings.local_embedding_url
    if not url:
        print("[ERROR] LOCAL_EMBEDDING_URL is not set in .env")
        sys.exit(1)

    logger.info("Using TEI server (url=%s)", url)
    return TEIEmbeddings(api_url=url)


# ═══════════════════════════════════════════════════════════════════════════════
# Vector store (Qdrant)
# ═══════════════════════════════════════════════════════════════════════════════

QDRANT_HOST = os.getenv("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
COLLECTION_NAME = os.getenv("QDRANT_PROFILES_COLLECTION_NAME", "rag_profiles_collection")


def build_vector_store(embeddings, chunker, docs: list, force: bool = False):
    """
    Upsert documents into the profiles Qdrant collection using LangChain's
    ``QdrantVectorStore`` for proper embedding generation, payload layout,
    and hybrid (dense + sparse) retrieval support.

    Parameters
    ----------
    embeddings:
        Dense embeddings instance (e.g. OpenVINOBgeEmbeddings).
    chunker:
        SmartChunker instance.
    docs:
        List of LangChain Document objects (one per source file).
    force:
        If True, delete and recreate the collection first — also enables
        hybrid (dense + sparse) mode.
    """
    from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
    from qdrant_client import QdrantClient

    client = QdrantClient(url=QDRANT_URL, timeout=120)

    # ── Sparse embeddings for hybrid search ───────────────────────────────────
    sparse_embedding = FastEmbedSparse(
        model_name="Qdrant/bm42-all-minilm-l6-v2-attentions",
    )

    # ── (Re)create collection with hybrid support ─────────────────────────────
    if force:
        try:
            client.delete_collection(collection_name=COLLECTION_NAME)
            logger.info("Deleted existing collection '%s'", COLLECTION_NAME)
        except Exception:
            pass

    collections = client.get_collections().collections
    existing = {c.name for c in collections}

    if COLLECTION_NAME not in existing:
        logger.info(
            "Creating Qdrant collection '%s' with HYBRID (dense + sparse) support",
            COLLECTION_NAME,
        )
        from qdrant_client.models import (
            Distance,
            HnswConfigDiff,
            OptimizersConfigDiff,
            SparseVectorParams,
            VectorParams,
        )

        # Determine dense vector dimension from a probe
        probe_vector = embeddings.embed_query("probe")
        vector_size = len(probe_vector)

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
                hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
            ),
            sparse_vectors_config={
                "langchain-sparse": SparseVectorParams(),
            },
            optimizers_config=OptimizersConfigDiff(
                default_segment_number=2,
                indexing_threshold=10000,
            ),
        )
        logger.info(
            "Collection created (dense=%d, sparse=langchain-sparse)", vector_size,
        )
    else:
        logger.info("Using existing collection '%s'", COLLECTION_NAME)

    # ── Chunk all documents (parallel) ────────────────────────────────────────
    all_chunks: list[Document] = []

    def _chunk_single(doc: Document) -> list[Document]:
        """Chunk a single document and attach metadata."""
        source_id = doc.metadata.get("source_id", "unknown")
        chunks = chunker.chunk([doc])
        if not chunks:
            return []

        for idx, chunk in enumerate(chunks):
            chunk.metadata["source_id"] = source_id
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["total_chunks"] = len(chunks)
            for k, v in doc.metadata.items():
                if k not in chunk.metadata or not chunk.metadata[k]:
                    chunk.metadata[k] = v
        return chunks

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        chunk_futures = [executor.submit(_chunk_single, doc) for doc in docs]
        for future in concurrent.futures.as_completed(chunk_futures):
            chunks = future.result()
            all_chunks.extend(chunks)

    if not all_chunks:
        logger.warning("No chunks produced — nothing to index.")
        return client, None

    # ── Add chunks via QdrantVectorStore (hybrid mode) ────────────────────────
    # This properly embeds both dense + sparse vectors and stores the
    # payload in LangChain's standard layout:
    #   - "page_content" key → the document text  (LangChain default)
    #   - "metadata" key → all metadata fields (nested dict, LangChain default)
    logger.info("  Adding %d chunks via QdrantVectorStore (HYBRID mode)...", len(all_chunks))

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
        sparse_embedding=sparse_embedding,
        retrieval_mode=RetrievalMode.HYBRID,
    )

    # Batch in groups to avoid oversized requests
    BATCH_SIZE = 100
    total_added = 0
    for start in range(0, len(all_chunks), BATCH_SIZE):
        batch = all_chunks[start:start + BATCH_SIZE]
        ids = vector_store.add_documents(batch)
        total_added += len(ids)
        logger.debug("  Batch %d/%d: added %d chunks",
                     start // BATCH_SIZE + 1,
                     (len(all_chunks) + BATCH_SIZE - 1) // BATCH_SIZE,
                     len(ids))

    # ── Verify ────────────────────────────────────────────────────────────────
    collection_info = client.get_collection(COLLECTION_NAME)
    logger.info(
        "✅ Done! %d source(s), %d chunk(s) stored in Qdrant collection '%s' "
        "(total points: %d)",
        len(docs), total_added, COLLECTION_NAME,
        collection_info.points_count,
    )

    return client, vector_store


# ═══════════════════════════════════════════════════════════════════════════════
# Parallel helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _process_single_pdf(pdf_path: Path) -> Optional[Document]:
    """Extract metadata + content from a single PDF and return a Document."""
    try:
        meta = extract_pdf_metadata(pdf_path)
        content = extract_pdf_content(pdf_path)
        if not content.strip():
            logger.warning("    Empty content — skipping %s", pdf_path.name)
            return None

        meta["source_id"] = f"pdf_{pdf_path.stem}"
        meta["filename"] = pdf_path.name
        meta["file_path"] = str(pdf_path.relative_to(PDF_DIR.parent.parent.parent))
        meta["ingested_at"] = datetime.now().isoformat()
        return Document(page_content=content, metadata=meta)
    except Exception as exc:
        logger.warning("    Failed to process %s: %s", pdf_path.name, exc)
        return None


def _process_single_url(url: str, timeout: int = URL_TIMEOUT) -> Optional[Document]:
    """Fetch a single URL and return the first Document."""
    docs = fetch_webpage_docs(url, timeout=timeout)
    if not docs:
        return None
    doc = docs[0]
    content = doc.page_content.strip()
    if not content or len(content) < 50:
        logger.warning("    No readable content — skipping %s", url)
        return None
    doc.metadata["source_id"] = f"web_{urlparse(url).netloc}"
    doc.metadata["ingested_at"] = datetime.now().isoformat()
    return doc


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Build a dedicated vector store for profile generation.",
    )
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Delete existing vectordb_profiles/ and rebuild from scratch.",
    )
    parser.add_argument(
        "--device", default=EMBEDDING_DEVICE,
        choices=["CPU", "GPU", "NPU", "AUTO"],
        help=f"OpenVINO device (default: {EMBEDDING_DEVICE}).",
    )
    parser.add_argument(
        "--no-semantic", action="store_true",
        help="Disable semantic chunking (always use recursive splitter).",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Building profiles knowledge base")
    logger.info("  PDFs:       %s", PDF_DIR)
    logger.info("  Links:      %s", LINKS_FILE)
    logger.info("  Qdrant:     %s | collection=%s", QDRANT_URL, COLLECTION_NAME)
    logger.info("  Device:     %s", args.device)
    logger.info("  Semantic:   %s", not args.no_semantic)
    logger.info("=" * 60)

    # ── 1. Embeddings ─────────────────────────────────────────────────────────
    embeddings = create_embeddings()

    # ── 2. Chunker ────────────────────────────────────────────────────────────
    from src.core.chunker import SmartChunker

    # When semantic chunking is disabled, no embedding function needed
    chunker = SmartChunker(
        use_semantic=not args.no_semantic,
        embedding_function=embeddings if not args.no_semantic else None,
        fallback_chunk_size=FALLBACK_CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        max_chunk_size=MAX_CHUNK_SIZE,
    )

    # ── 3. Collect documents ──────────────────────────────────────────────────
    all_docs: list[Document] = []

    # ── 3a. PDFs (parallel extraction) ────────────────────────────────────────
    pdf_files = list(PDF_DIR.glob("*.pdf")) if PDF_DIR.is_dir() else []
    logger.info("Found %d PDF(s)", len(pdf_files))

    if pdf_files:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_map = {executor.submit(_process_single_pdf, p): p for p in pdf_files}
            for future in concurrent.futures.as_completed(future_map):
                pdf_path = future_map[future]
                try:
                    doc = future.result()
                    if doc is not None:
                        all_docs.append(doc)
                        meta = doc.metadata
                        logger.info(
                            "    ✓ %s | %s | %s",
                            meta.get("title", pdf_path.name),
                            meta.get("authors", ["?"])[0] if meta.get("authors") else "?",
                            meta.get("year", "?"),
                        )
                    else:
                        logger.warning("    ✗ %s — no content extracted", pdf_path.name)
                except Exception as exc:
                    logger.warning("    ✗ %s — %s", pdf_path.name, exc)

    # ── 3b. Web links (parallel fetching) ─────────────────────────────────────
    urls: list[str] = []
    if LINKS_FILE.is_file():
        urls = [
            line.strip()
            for line in LINKS_FILE.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    logger.info("Found %d URL(s)", len(urls))

    if urls:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_map = {
                executor.submit(_process_single_url, url, URL_TIMEOUT): url
                for url in urls
            }
            for future in concurrent.futures.as_completed(future_map):
                url = future_map[future]
                try:
                    doc = future.result()
                    if doc is not None:
                        all_docs.append(doc)
                        logger.info(
                            "    ✓ %s | %s",
                            doc.metadata.get("title", url),
                            doc.metadata.get("domain", urlparse(url).netloc),
                        )
                    else:
                        logger.warning("    ✗ %s — no content", url)
                except Exception as exc:
                    logger.warning("    ✗ %s — %s", url, exc)

    # ── 4. Build the vector store ─────────────────────────────────────────────
    if not all_docs:
        logger.warning("No documents collected — nothing to index.")
        return

    logger.info("Total documents to index: %d", len(all_docs))
    build_vector_store(embeddings, chunker, all_docs, force=args.force)

    # ── 5. Quick summary ──────────────────────────────────────────────────────
    logger.info("")
    logger.info("Summary:")
    logger.info("  Sources indexed: %d", len(all_docs))
    logger.info("  Qdrant collection: %s @ %s", COLLECTION_NAME, QDRANT_URL)
    logger.info("")
    logger.info("Next step: the profiles retriever will connect to Qdrant automatically.")
    logger.info("  Ensure QDRANT_HOST is set correctly in your .env or environment.")


if __name__ == "__main__":
    main()
