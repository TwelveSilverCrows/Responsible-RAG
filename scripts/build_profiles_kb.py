#!/usr/bin/env python3
"""
build_profiles_kb.py — Build a dedicated vector store for profile generation
==============================================================================
Ingests PDFs and web links from ``resources/profiles/`` into a separate
TurboVec store (``vectordb_profiles/``) using local OpenVINO GPU-accelerated
embeddings (BAAI/bge-large-en-v1.5).

Usage
-----
    # 1. Install OpenVINO extras (one-time)
    pip install -e ".[openvino]"

    # 2. Run the script
    python scripts/build_profiles_kb.py

    # 3. Re-run anytime you add/change files in resources/profiles/

What it does
------------
1. **PDFs** — extracts full text + metadata (author, year, title, DOI) via
   PyMuPDF and heuristic parsing.
2. **Web links** — fetches each URL, extracts page title & main content via
   BeautifulSoup, along with visible metadata.
3. **Chunking** — uses the project's ``SmartChunker`` (semantic → recursive
   fallback).
4. **Embeddings** — ``OpenVINOBgeEmbeddings`` with GPU device (Intel GPU).
5. **Storage** — all chunks + metadata stored in ``vectordb_profiles/`` via
   ``TurboQuantVectorStore``.
"""

import argparse
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
VECTORDB_DIR = PROJECT_ROOT.parent / "storage" / "vectordb_profiles"

# Embedding model
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
EMBEDDING_DEVICE = "GPU"

# Chunking
USE_SEMANTIC_CHUNKING = False  # CPU-only: disable semantic (no GPU for chunking)
FALLBACK_CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
MAX_CHUNK_SIZE = 1600

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
    """Extract full text content from a PDF."""
    import fitz

    doc = fitz.open(str(filepath))
    try:
        pages = [page.get_text("text") for page in doc]
        return "\n\n".join(pages)
    finally:
        doc.close()


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
# Embedding factory (local OpenVINO GPU)
# ═══════════════════════════════════════════════════════════════════════════════

def _batch_embed(embed_fn, texts: list[str], batch_size: int = 16,
                 max_retries: int = 3) -> list[list[float]]:
    """
    Embed *texts* in small batches with retry logic.

    The HF Inference API can timeout on large batches, so we split into
    smaller chunks and retry transient errors (504, 503).
    """
    all_vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(max_retries):
            try:
                vectors = embed_fn(batch)
                all_vectors.extend(vectors)
                logger.debug("  Embedded batch %d/%d (%d texts)",
                             i // batch_size + 1,
                             (len(texts) + batch_size - 1) // batch_size,
                             len(batch))
                break
            except Exception as exc:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 5
                    logger.warning("  Embedding batch failed (%s), retrying in %ds...", exc, wait)
                    time.sleep(wait)
                else:
                    raise
    return all_vectors


class _ResilientEmbeddings:
    """Wrapper that adds batching + retry to any embedding model."""

    def __init__(self, inner, batch_size: int = 16):
        self._inner = inner
        self._batch_size = batch_size

    def embed_query(self, text: str) -> list[float]:
        return self._inner.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return _batch_embed(self._inner.embed_documents, texts,
                            batch_size=self._batch_size)


def create_embeddings(device: str = "GPU"):
    """
    Create a **local** OpenVINO BGE embedding model running on the
    specified device (GPU by default).  No remote API calls.

    The model is downloaded from Hugging Face Hub on first run and
    cached locally in ``~/.cache/huggingface/``.
    """
    try:
        from langchain_community.embeddings import OpenVINOBgeEmbeddings
    except ImportError:
        print(
            "[ERROR] OpenVINO dependencies not installed.\n"
            "   Run:  pip install -e '.[openvino]'"
        )
        sys.exit(1)

    logger.info(
        "Loading BAAI/bge-large-en-v1.5 via OpenVINO (device=%s) ...", device,
    )
    logger.info("  (First run compiles the model — may take a minute)")

    t0 = time.time()
    raw = OpenVINOBgeEmbeddings(
        model_name_or_path=EMBEDDING_MODEL,
        model_kwargs={"device": device},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 8,
        },
        query_instruction="Represent this query for searching relevant passages: ",
        embed_instruction="Represent this document for retrieval: ",
    )
    elapsed = time.time() - t0
    logger.info("OpenVINO embedding model ready (%.1f s)", elapsed)
    return _ResilientEmbeddings(raw, batch_size=16)


# ═══════════════════════════════════════════════════════════════════════════════
# Vector store
# ═══════════════════════════════════════════════════════════════════════════════

def build_vector_store(embeddings, chunker, docs: list, force: bool = False):
    """
    Create or replace the TurboQuantVectorStore at VECTORDB_DIR.

    Parameters
    ----------
    embeddings:
        OpenVINOBgeEmbeddings instance.
    chunker:
        SmartChunker instance.
    docs:
        List of LangChain Document objects (one per source file).
    force:
        If True, delete existing store first.
    """
    from turbovec.langchain import TurboQuantVectorStore

    if force and VECTORDB_DIR.exists():
        import shutil
        shutil.rmtree(VECTORDB_DIR)
        logger.info("Removed existing vector store at %s", VECTORDB_DIR)

    VECTORDB_DIR.mkdir(parents=True, exist_ok=True)

    index_file = VECTORDB_DIR / "index.tvim"
    id_map_file = VECTORDB_DIR / "id_map.json"

    if index_file.exists() and not force:
        logger.info("Loading existing store at %s", VECTORDB_DIR)
        store = TurboQuantVectorStore.load(
            str(VECTORDB_DIR), embedding=embeddings,
        )
        id_map: dict[str, list[str]] = {}
        if id_map_file.exists():
            id_map = json.loads(id_map_file.read_text())
    else:
        logger.info("Creating new TurboQuantVectorStore (bit_width=4)")
        store = TurboQuantVectorStore(
            embedding=embeddings,
            bit_width=4,
        )
        id_map = {}

    # ── Chunk and index ───────────────────────────────────────────────────────
    total_chunks = 0
    for doc in docs:
        source_id = doc.metadata.get("source_id", "unknown")
        title = doc.metadata.get("title", source_id)
        logger.info("  Chunking: %s", title)

        chunks = chunker.chunk([doc])
        if not chunks:
            logger.warning("    No chunks produced — skipping")
            continue

        # Attach metadata to every chunk
        for chunk in chunks:
            chunk.metadata["source_id"] = source_id
            chunk.metadata["chunk_index"] = chunks.index(chunk)
            chunk.metadata["total_chunks"] = len(chunks)
            # Copy all source-level metadata
            for k, v in doc.metadata.items():
                if k not in chunk.metadata or not chunk.metadata[k]:
                    chunk.metadata[k] = v

        # Store in TurboVec
        ids = store.add_documents(chunks)
        id_map.setdefault(source_id, []).extend(ids)
        total_chunks += len(chunks)
        logger.info("    → %d chunks stored", len(chunks))

    # ── Persist ───────────────────────────────────────────────────────────────
    store.dump(str(VECTORDB_DIR))
    id_map_file.write_text(json.dumps(id_map, indent=2))
    logger.info(
        "✅ Done! %d source(s), %d chunk(s) stored in %s",
        len(id_map), total_chunks, VECTORDB_DIR,
    )

    return store, id_map


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
    logger.info("  Output:     %s", VECTORDB_DIR)
    logger.info("  Device:     %s", args.device)
    logger.info("  Semantic:   %s", not args.no_semantic)
    logger.info("=" * 60)

    # ── 1. Embeddings ─────────────────────────────────────────────────────────
    embeddings = create_embeddings(device=args.device)

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
    from langchain_core.documents import Document

    all_docs: list[Document] = []

    # ── 3a. PDFs ──────────────────────────────────────────────────────────────
    if PDF_DIR.is_dir():
        pdf_files = sorted(PDF_DIR.glob("*.pdf"))
        logger.info("Found %d PDF(s)", len(pdf_files))

        for pdf_path in pdf_files:
            logger.info("  Extracting: %s", pdf_path.name)
            meta = extract_pdf_metadata(pdf_path)
            content = extract_pdf_content(pdf_path)

            if not content.strip():
                logger.warning("    Empty content — skipping")
                continue

            meta["source_id"] = f"pdf_{pdf_path.stem}"
            meta["filename"] = pdf_path.name
            meta["file_path"] = str(pdf_path.relative_to(PDF_DIR.parent.parent.parent))  # storage/
            meta["ingested_at"] = datetime.now().isoformat()

            doc = Document(
                page_content=content,
                metadata=meta,
            )
            all_docs.append(doc)
            logger.info(
                "    ✓ %s | %s | %s",
                meta.get("title", "?"),
                meta.get("authors", ["?"])[0] if meta.get("authors") else "?",
                meta.get("year", "?"),
            )

    # ── 3b. Web links ─────────────────────────────────────────────────────────
    if LINKS_FILE.is_file():
        urls = [
            line.strip()
            for line in LINKS_FILE.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        logger.info("Found %d URL(s)", len(urls))

        for url in urls:
            logger.info("  Fetching: %s", url)
            docs = fetch_webpage_docs(url, timeout=URL_TIMEOUT)
            if docs is None:
                continue

            for doc in docs:
                content = doc.page_content.strip()
                if not content or len(content) < 50:
                    logger.warning("    No readable content — skipping")
                    continue

                doc.metadata["source_id"] = f"web_{urlparse(url).netloc}_{len(all_docs)}"
                doc.metadata["ingested_at"] = datetime.now().isoformat()
                all_docs.append(doc)

                logger.info(
                    "    ✓ %s | %s",
                    doc.metadata.get("title", "?"),
                    doc.metadata.get("domain", "?"),
                )

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
    logger.info("  Store location:  %s", VECTORDB_DIR)
    logger.info("")
    logger.info("Next step: use this store in profile generation with:")
    logger.info("  store = TurboQuantVectorStore.load('%s', embedding=embeddings)", VECTORDB_DIR)
    logger.info("  retriever = store.as_retriever(k=5)")


if __name__ == "__main__":
    main()
