#!/usr/bin/env python3
"""
stress_test_embedding.py — Stress-test the OpenVINO embedding server
=====================================================================
Sends 1000 embedding requests (32 concurrent) with long texts to
validate throughput, stability, and correctness.

Usage
-----
    uv run python scripts/stress_test_embedding.py
"""

import asyncio
import json
import logging
import sys
import time
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
TOTAL_REQUESTS = 1000
CONCURRENCY = 32
TIMEOUT_SEC = 120

# A long text to simulate realistic usage (~1 KB each)
LONG_TEXT = """
Canada's healthcare system is a publicly funded system that provides universal
coverage for medically necessary services. Known as Medicare, it is guided by
the Canada Health Act which establishes five key principles: public administration,
comprehensiveness, universality, portability, and accessibility. Each province
and territory administers its own health insurance plan, following these national
standards. The system covers visits to doctors, hospital stays, and diagnostic
tests, while dental care, prescription drugs (outside hospitals), and
vision care are often not covered and may require private insurance or
out-of-pocket payment. Recent discussions have focused on expanding coverage
for pharmacare, dental care, and mental health services to create a more
comprehensive universal healthcare system that meets the evolving needs of
Canada's diverse population. Indigenous communities have specific health
programs and services administered through Indigenous Services Canada,
including the Non-Insured Health Benefits program which provides coverage
for a range of health services not covered by provincial or territorial
plans. The COVID-19 pandemic highlighted both strengths and vulnerabilities
in the system, accelerating the adoption of virtual care and telehealth
services while exposing gaps in public health infrastructure and the need
for better integration between primary care, public health, and social
services. Healthcare workforce shortages, particularly in rural and remote
areas, remain a significant challenge, with various strategies being
implemented to recruit and retain healthcare professionals including
increased training positions, international recruitment, and scope-of-practice
expansions for nurse practitioners and pharmacists.
"""


async def send_embed_request(
    client: httpx.AsyncClient,
    texts: list[str],
    index: int,
) -> tuple[int, float, bool]:
    """Send a single embed request and return (index, duration_sec, success)."""
    start = time.monotonic()
    try:
        resp = await client.post(
            EMBED_URL,
            json={"texts": texts, "is_query": False},
            timeout=TIMEOUT_SEC,
        )
        resp.raise_for_status()
        data = resp.json()
        duration = time.monotonic() - start

        # Validate the response
        if "embeddings" not in data:
            logger.warning("  Request #%d: response missing 'embeddings'", index)
            return index, duration, False

        emb = data["embeddings"]
        if not emb or len(emb) != len(texts):
            logger.warning("  Request #%d: expected %d embeddings, got %d", index, len(texts), len(emb))
            return index, duration, False

        # Check for corruption (all zeros or NaN)
        for i, vec in enumerate(emb):
            if all(v == 0.0 for v in vec):
                logger.warning("  Request #%d text[%d]: all-zero vector", index, i)
                return index, duration, False

        return index, duration, True

    except Exception as exc:
        duration = time.monotonic() - start
        logger.error("  Request #%d failed after %.1fs: %s", index, duration, exc)
        return index, duration, False


async def run_stress_test() -> None:
    """Run the stress test with controlled concurrency."""
    logger.info("=" * 60)
    logger.info("OpenVINO Embedding Stress Test")
    logger.info("  Server:      %s", EMBED_URL)
    logger.info("  Requests:    %d", TOTAL_REQUESTS)
    logger.info("  Concurrency: %d", CONCURRENCY)
    logger.info("  Texts/req:   %d", 2)
    logger.info("=" * 60)

    # Build all request payloads upfront
    texts_batch = [LONG_TEXT, "What health services are available to Indigenous youth in Canada?"]
    payloads = [texts_batch] * TOTAL_REQUESTS

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def bounded_request(index: int) -> tuple[int, float, bool]:
        async with semaphore:
            async with httpx.AsyncClient(timeout=TIMEOUT_SEC) as client:
                return await send_embed_request(client, payloads[index], index)

    start_time = time.monotonic()
    completed = 0
    succeeded = 0
    failed = 0
    durations: list[float] = []

    # Process in chunks to show progress
    chunk_size = 100
    for chunk_start in range(0, TOTAL_REQUESTS, chunk_size):
        chunk_end = min(chunk_start + chunk_size, TOTAL_REQUESTS)
        indices = list(range(chunk_start, chunk_end))

        tasks = [bounded_request(i) for i in indices]
        results = await asyncio.gather(*tasks)

        for idx, dur, ok in results:
            completed += 1
            durations.append(dur)
            if ok:
                succeeded += 1
            else:
                failed += 1

        pct = completed / TOTAL_REQUESTS * 100
        avg_dur = sum(durations[-chunk_size:]) / max(len(results), 1)
        logger.info(
            "  Progress: %3d / %d (%5.1f%%)  |  OK=%d  FAIL=%d  |  "
            "chunk avg %.2fs  |  overall avg %.2fs",
            completed, TOTAL_REQUESTS, pct,
            succeeded, failed, avg_dur,
            sum(durations) / max(len(durations), 1),
        )

    total_time = time.monotonic() - start_time

    # ── Summary ───────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("RESULTS")
    logger.info("  Total time:      %.1f s", total_time)
    logger.info("  Requests/sec:    %.1f", TOTAL_REQUESTS / total_time if total_time > 0 else 0)
    logger.info("  Succeeded:       %d / %d", succeeded, TOTAL_REQUESTS)
    logger.info("  Failed:          %d", failed)

    if durations:
        durations.sort()
        logger.info("  Latency (p50):   %.3f s", durations[len(durations) // 2])
        logger.info("  Latency (p95):   %.3f s", durations[int(len(durations) * 0.95)])
        logger.info("  Latency (p99):   %.3f s", durations[int(len(durations) * 0.99)])
        logger.info("  Min latency:     %.3f s", durations[0])
        logger.info("  Max latency:     %.3f s", durations[-1])
    logger.info("=" * 60)

    if failed > 0:
        logger.warning("⚠️  %d requests FAILED — check server logs", failed)
    else:
        logger.info("✅ All requests passed!")

    return failed == 0


def main() -> None:
    success = asyncio.run(run_stress_test())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
