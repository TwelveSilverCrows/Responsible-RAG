#!/usr/bin/env python3
"""
stress_test_tei.py — Stress-test the TEI embedding server
===========================================================
Simulates realistic backend workloads:
  - Queries (embed_query): single texts, like RAG retrieval calls
  - Document batches (embed_documents): varying sizes, like chunking + ingestion
  - Concurrent mixed traffic: multiple "users" and "ingestion jobs"

Usage
-----
    uv run python scripts/stress_test_tei.py
"""

import logging
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("stress_test")

# ── Config ───────────────────────────────────────────────────────────────────
EMBED_URL = "http://ec2-35-182-89-189.ca-central-1.compute.amazonaws.com:8080/embed"
BATCH_SIZES = [1, 2, 4, 8, 16, 32, 64]
QUERY_COUNT = 200          # Total query requests
DOC_BATCH_COUNT = 50       # Total document-batch requests (combined across sizes)
CONCURRENT_WORKERS = 16    # Simulates backend thread pool + concurrent users
TIMEOUT_SEC = 120

# Sample texts mimicking real backend usage
SAMPLE_QUERIES = [
    "What health services are available for Indigenous youth in Canada?",
    "How do I apply for Canadian citizenship as a refugee?",
    "What are the side effects of antidepressants for teenagers?",
    "Where can I find LGBTQ+ friendly healthcare in rural areas?",
    "What is the Non-Insured Health Benefits program?",
    "How does the Canada Health Act protect patients?",
    "What mental health resources exist for post-secondary students?",
    "Can I access healthcare in Canada without a provincial health card?",
]

SAMPLE_DOCUMENTS = [
    "Canada's healthcare system is a publicly funded system that provides universal coverage for medically necessary services. Each province and territory administers its own health insurance plan, following national standards set by the Canada Health Act.",
    "Indigenous Services Canada provides health programs and services through the Non-Insured Health Benefits program, which covers a range of health services not covered by provincial or territorial plans.",
    "The Canadian Charter of Rights and Freedoms guarantees certain rights, including legal rights, equality rights, and language rights for all citizens and permanent residents.",
    "Mental health services in Canada include community-based programs, crisis intervention services, and hospital-based care. Many provinces have specific youth mental health initiatives.",
    "The Social Determinants of Health framework identifies income, education, employment, housing, and social support networks as key factors influencing health outcomes.",
    "Immigration, Refugees and Citizenship Canada (IRCC) processes applications for permanent residence, citizenship, refugee protection, and temporary stays.",
    "Canadian environmental regulations under the Canadian Environmental Protection Act address pollution prevention, climate change, and biodiversity conservation.",
    "The education system in Canada is managed by provincial and territorial governments, with funding, curriculum, and assessment varying across jurisdictions.",
    "Indigenous data sovereignty principles, including OCAP (Ownership, Control, Access, Possession), guide research and data collection involving First Nations communities.",
    "The Canadian pharmaceutical market includes both brand-name and generic drugs, with the Patented Medicine Prices Review Board regulating prices of patented medicines.",
]


def call_embed(texts: list[str]) -> dict | None:
    """Make a single embed API call and return timing info."""
    start = time.monotonic()
    try:
        is_single = isinstance(texts, str) or len(texts) == 1
        payload = {
            "inputs": texts if isinstance(texts, list) else texts,
            "normalize": True,
        }
        resp = httpx.post(
            EMBED_URL,
            json=payload,
            timeout=TIMEOUT_SEC,
        )
        resp.raise_for_status()
        data = resp.json()
        elapsed = time.monotonic() - start

        # Validate
        if is_single and isinstance(texts, str):
            vec = data if isinstance(data[0], (int, float)) else data[0]
            dim = len(vec) if isinstance(vec, list) else 0
        else:
            dim = len(data[0]) if data else 0

        return {
            "ok": True,
            "elapsed": elapsed,
            "texts": len(texts) if isinstance(texts, list) else 1,
            "dim": dim,
        }
    except Exception as exc:
        elapsed = time.monotonic() - start
        return {
            "ok": False,
            "elapsed": elapsed,
            "texts": len(texts) if isinstance(texts, list) else 1,
            "error": str(exc)[:80],
        }


def run_query_worker(worker_id: int) -> list[dict]:
    """Simulate a user making sequential query embeddings."""
    results = []
    for i in range(QUERY_COUNT // CONCURRENT_WORKERS):
        text = random.choice(SAMPLE_QUERIES)
        r = call_embed(text)
        r["worker"] = worker_id
        r["seq"] = i
        r["type"] = "query"
        results.append(r)
    return results


def run_batch_worker(worker_id: int) -> list[dict]:
    """Simulate an ingestion job embedding document batches of various sizes."""
    results = []
    for batch_size in BATCH_SIZES:
        count = DOC_BATCH_COUNT // (len(BATCH_SIZES) * CONCURRENT_WORKERS // 4) + 1
        for _ in range(count):
            texts = [random.choice(SAMPLE_DOCUMENTS) for _ in range(batch_size)]
            r = call_embed(texts)
            r["worker"] = worker_id
            r["type"] = f"batch-{batch_size}"
            results.append(r)
    return results


def main() -> None:
    logger.info("=" * 60)
    logger.info("TEI Embedding Stress Test")
    logger.info("  Server:          %s", EMBED_URL)
    logger.info("  Workers:         %d", CONCURRENT_WORKERS)
    logger.info("  Query requests:  %d", QUERY_COUNT)
    logger.info("  Batch sizes:     %s", BATCH_SIZES)
    logger.info("=" * 60)

    start_time = time.monotonic()
    all_results: list[dict] = []

    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as pool:
        futures = []

        # Submit query workers (simulate concurrent users)
        for w in range(CONCURRENT_WORKERS // 2):
            futures.append(pool.submit(run_query_worker, w))

        # Submit batch workers (simulate concurrent ingestion jobs)
        for w in range(CONCURRENT_WORKERS // 2):
            futures.append(pool.submit(run_batch_worker, CONCURRENT_WORKERS // 2 + w))

        done = 0
        total = len(futures)
        for f in as_completed(futures):
            done += 1
            results = f.result()
            all_results.extend(results)
            logger.info("  Worker completed: %d / %d", done, total)

    total_time = time.monotonic() - start_time

    # ── Analyze ──────────────────────────────────────────────────────────
    succeeded = [r for r in all_results if r["ok"]]
    failed = [r for r in all_results if not r["ok"]]
    durations = [r["elapsed"] for r in succeeded]
    durations.sort()

    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("  Total time:      %.1f s", total_time)
    logger.info("  Total requests:  %d", len(all_results))
    logger.info("  Succeeded:       %d", len(succeeded))
    logger.info("  Failed:          %d", len(failed))
    if durations:
        logger.info("  Requests/sec:    %.1f", len(succeeded) / total_time if total_time > 0 else 0)
        logger.info("  Latency p50:     %.3f s", durations[len(durations) // 2])
        logger.info("  Latency p95:     %.3f s", durations[int(len(durations) * 0.95)])
        logger.info("  Latency p99:     %.3f s", durations[int(len(durations) * 0.99)])
        logger.info("  Min:             %.3f s", durations[0])
        logger.info("  Max:             %.3f s", durations[-1])

    # Per type breakdown
    by_type: dict[str, list[float]] = {}
    for r in succeeded:
        t = r["type"] if "batch" not in r["type"] else "batch"
        by_type.setdefault(t, []).append(r["elapsed"])
    for t, durs in sorted(by_type.items()):
        durs.sort()
        logger.info(
            "  %s: count=%d  p50=%.3fs  p95=%.3fs",
            t, len(durs), durs[len(durs) // 2], durs[int(len(durs) * 0.95)],
        )

    if failed:
        logger.warning("⚠️  %d FAILED requests (first 3 shown):", len(failed))
        for f in failed[:3]:
            logger.warning("    worker=%s type=%s texts=%s error=%s",
                           f.get("worker"), f.get("type"), f.get("texts"), f.get("error"))
        sys.exit(1)
    else:
        logger.info("✅ All requests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
