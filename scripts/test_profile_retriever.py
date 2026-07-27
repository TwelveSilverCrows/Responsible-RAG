#!/usr/bin/env python3
"""
test_profile_retriever.py — Isolated test for ProfileAugmenter's RAG retriever
================================================================================
Tests whether the profile knowledge base in Qdrant can be queried and returns
evidence snippets used to build a dynamic system prompt.

Usage
-----
    uv run python scripts/test_profile_retriever.py
    # or:  python scripts/test_profile_retriever.py

What it does
------------
1. Connects to Qdrant and checks the rag_profiles_collection.
2. Instantiates ProfileAugmenter with the HF Inference API embedding function.
3. Calls _get_retriever() to verify the retriever is created.
4. Calls _retrieve_for_field() for each demographic field and prints evidence.
5. Builds a full DYNAMIC_PROFILE_TEMPLATE prompt with a dummy user profile.
6. Reports source titles used.
"""

import logging
import sys
import textwrap
from pathlib import Path

# ── Ensure backend/src is on sys.path ─────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_profile_retriever")


def main():
    # ── 1. Settings ───────────────────────────────────────────────────────
    from src.core.config import get_settings

    settings = get_settings()
    logger.info("Qdrant: %s:%s", settings.qdrant_host, settings.qdrant_port)
    logger.info("Profiles collection: %s", settings.qdrant_profiles_collection_name)
    logger.info("Embedding model: %s", settings.embedding_model)

    # Check HF token is set
    if not settings.huggingfacehub_api_token:
        logger.error("HUGGINGFACEHUB_API_TOKEN not set in .env")
        sys.exit(1)
    logger.info("HF token: %s...", settings.huggingfacehub_api_token[:8])

    # ── 2. Embedding function ──────────────────────────────────────────────
    from src.core.embeddings import EmbeddingFactory

    logger.info("Creating embedding function...")
    embeddings = EmbeddingFactory.create(settings)
    logger.info("Embedding function created: %s", type(embeddings).__name__)

    # ── 3. ProfileAugmenter ────────────────────────────────────────────────
    from src.core.profiles import ProfileAugmenter, _FIELD_QUERIES, _STANDARD_PROFILE, DYNAMIC_PROFILE_TEMPLATE

    augmenter = ProfileAugmenter(embedding_function=embeddings)
    logger.info("ProfileAugmenter instantiated")

    # ── 4. Test _get_retriever() ───────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  STEP 1: _get_retriever() — lazy-load the Qdrant retriever")
    print("=" * 72)

    retriever = augmenter._get_retriever(k=3)
    if retriever is None:
        print("  ❌ Retriever is None — collection missing or connection failed.")
        print("  Check that Qdrant is running and build_profiles_kb.py was executed.")
        sys.exit(1)
    print(f"  ✅ Retriever created: {type(retriever).__name__}")
    print(f"     search_kwargs: {retriever.search_kwargs}")

    # ── 5. Test _retrieve_for_field() for each field ───────────────────────
    print("\n" + "=" * 72)
    print("  STEP 2: _retrieve_for_field() — query evidence for each demographic")
    print("=" * 72)

    all_evidence: dict[str, str] = {}
    for field_key, query in _FIELD_QUERIES.items():
        print(f"\n  ── Field: {field_key}")
        print(f"      Query: {query!r}")
        try:
            evidence = augmenter._retrieve_for_field(field_key, query)
            if evidence:
                # Truncate for display
                preview = evidence[:300].replace("\n", "\\n")
                print(f"      ✅ Retrieved ({len(evidence)} chars): {preview}...")
            else:
                print(f"      ⚠️  No evidence returned (empty string)")
        except Exception as e:
            print(f"      ❌ Error: {e}")
        all_evidence[field_key] = evidence

    print(f"\n  Source titles used: {augmenter.last_source_titles}")

    # ── 6. Test build_prompt() with dummy profile ──────────────────────────
    print("\n" + "=" * 72)
    print("  STEP 3: build_prompt() — generate a dummy profile prompt")
    print("=" * 72)

    dummy_profile = {
        "sex_at_birth": "Female",
        "gender": "Non-binary",
        "age_group": "Teen (13–17 years)",
        "primary_language": "Spanish",
        "education_level": "High school (in progress)",
        "citizen_status": "Recent immigrant / Refugee claimant",
        "indigenous_status": "First Nations",
        "disability_status": "Visual impairment",
    }

    dummy_query = "What are my rights regarding gender identity at school?"
    dummy_context = (
        "[From: Canadian Human Rights Act]\n"
        "The Canadian Human Rights Act prohibits discrimination based on gender identity "
        "and gender expression in all areas under federal jurisdiction.\n\n"
        "[From: Provincial Education Act]\n"
        "Students have the right to a safe, inclusive learning environment free from "
        "discrimination and harassment."
    )

    try:
        prompt = augmenter.build_prompt(
            user_profile=dummy_profile,
            user_query=dummy_query,
            retrieved_documents=dummy_context,
        )
        print("  ✅ Prompt built successfully! Length:", len(prompt), "chars")
        print("\n  ──── BEGIN PROMPT ────")
        # Show first 1500 chars as preview
        print(prompt[:1500])
        if len(prompt) > 1500:
            print(f"\n  ... [truncated, {len(prompt) - 1500} more chars]")
        print("  ──── END PROMPT ────")
        print(f"\n  Source titles used: {augmenter.last_source_titles}")
    except Exception as e:
        print(f"  ❌ build_prompt() failed: {e}")
        import traceback
        traceback.print_exc()

    # ── 7. Test with empty profile (defaults only) ─────────────────────────
    print("\n" + "=" * 72)
    print("  STEP 4: build_prompt() — with default (empty) profile")
    print("=" * 72)

    try:
        prompt_default = augmenter.build_prompt(
            user_profile={},
            user_query="Tell me about Canadian healthcare.",
            retrieved_documents="No specific context retrieved.",
        )
        print("  ✅ Default prompt built! Length:", len(prompt_default), "chars")
        print("\n  ──── BEGIN DEFAULT PROMPT (first 800 chars) ────")
        print(prompt_default[:800])
        print("\n  ──── END DEFAULT PROMPT ────")
    except Exception as e:
        print(f"  ❌ Default build_prompt() failed: {e}")

    # ── 8. Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  Retriever creation:     ✅" if retriever else "  ❌")
    fields_with_evidence = sum(1 for v in all_evidence.values() if v)
    print(f"  Fields with evidence:   {fields_with_evidence}/{len(_FIELD_QUERIES)}")
    print(f"  All source titles:      {augmenter.last_source_titles}")
    print("  ✅ Test complete!")


if __name__ == "__main__":
    main()
