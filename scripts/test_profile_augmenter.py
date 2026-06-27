#!/usr/bin/env python3
"""
test_profile_augmenter.py — Real RAG-powered profile test
============================================================
Loads ``vectordb_profiles/``, queries each demographic field with a
retriever + DeepSeek LLM, and builds a tailored communication-rules
prompt.  Only non-default fields trigger a store lookup.

Usage
-----
    uv run python scripts/test_profile_augmenter.py
"""

import logging
import sys
from pathlib import Path
from operator import itemgetter

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from turbovec.langchain import TurboQuantVectorStore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from src.core.config import get_settings
from src.core.embeddings import EmbeddingFactory
from src.core.profiles import DYNAMIC_PROFILE_TEMPLATE

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  SET YOUR TEST PROFILE HERE  (edit these variables manually)
# ═══════════════════════════════════════════════════════════════════════════════

TEST_PROFILE: dict[str, str] = {
    "sex_at_birth": "female",
    "gender": "non_binary",
    "age_group": "teen",
    "primary_language": "English",
    "education_level": "high school",
    "citizen_status": "Canadian citizen",
    "indigenous_status": "First Nations",
    "disability_status": "cognitive disability",
}

TEST_QUERY = "What health services are available to me in Canada?"

# ═══════════════════════════════════════════════════════════════════════════════
# 2.  Standard defaults  (same as in profiles.py)
# ═══════════════════════════════════════════════════════════════════════════════

_STANDARD: dict[str, str] = {
    "sex_at_birth": "Male",
    "gender": "Queer",
    "age_group": "Adult (18\u201364 years)",
    "primary_language": "English",
    "education_level": "Some post-secondary education",
    "citizen_status": "Canadian citizen / Permanent resident",
    "indigenous_status": "Non-Indigenous",
    "disability_status": "ADHD",
}

_STANDARD_RULES: dict[str, str] = {
    "age_group_rules": "Use clear, direct language suitable for a general adult audience. Avoid patronising or overly complex explanations.",
    "language_rules": "Use plain English. Define any technical terms on first use. Avoid idioms or culturally specific references without explanation.",
    "education_rules": "Assume general literacy. Explain specialised terms but avoid oversimplifying core concepts.",
    "indigenous_rules": "No specific Indigenous considerations indicated. If the topic relates to Indigenous peoples, include a note that diverse First Nations, Inuit, and M\u00e9tis perspectives exist.",
    "disability_rules": "No specific disability considerations indicated. Use clear, accessible formatting. Offer alternative formats on request.",
    "gender_rules": "Use gender-neutral language unless the user's gender is known. Use 'they/them' as the default pronoun.",
    "citizen_rules": "No specific immigration or citizenship considerations indicated. Provide general Canadian context.",
}

_QUERIES: dict[str, str] = {
    "sex_at_birth": "sex at birth biological differences health communication Canada",
    "gender": "gender identity non-binary two-spirit LGBTQ inclusion communication",
    "age_group": "teen youth adolescent developmental considerations communication",
    "primary_language": "language barriers English proficiency newcomers immigrants healthcare",
    "education_level": "high school health literacy plain language communication",
    "citizen_status": "Canadian citizen rights healthcare access",
    "indigenous_status": "First Nations Indigenous data sovereignty OCAP TRC reconciliation",
    "disability_status": "cognitive disability accessibility inclusive communication accommodations",
}

_RULE_PROMPT = ChatPromptTemplate.from_template(
    "You are a communication-strategy expert.\n\n"
    "A user has the following demographic attribute:\n"
    "  {field_name}: {field_value}\n\n"
    "Below is research content from academic sources about this group:\n"
    "{context}\n\n"
    "Write 3\u20134 concise, actionable communication-adaptation rules (plain text, "
    "no markdown) for an AI assistant to follow when interacting with someone "
    "from this group. Cover: preferred language, tone, safety considerations, "
    "and specific do/don\u2019t. If the context is not relevant, fall back to "
    "general best practices for respectful communication."
)


def build_field_rule(
    field_key: str,
    field_value: str,
    field_chain,
    logger: logging.Logger,
) -> str:
    """Query the vector store + LLM to produce a tailored rule, or return standard."""
    standard_val = _STANDARD.get(field_key, "")
    if field_value == standard_val:
        logger.info("  %s = '%s' (default) \u2192 using standard rule", field_key, field_value)
        return _STANDARD_RULES.get(f"{field_key}_rules", _STANDARD_RULES.get(field_key, ""))

    query = _QUERIES.get(field_key, field_value)
    logger.info("  \u23f3 Querying RAG for %s = '%s' ...", field_key, field_value)
    try:
        result = field_chain.invoke({
            "query": query,
            "field_name": field_key.replace("_", " ").title(),
            "field_value": field_value,
        })
        return result.strip()
    except Exception as exc:
        logger.warning("  RAG failed for %s: %s \u2014 using standard rule", field_key, exc)
        return _STANDARD_RULES.get(f"{field_key}_rules", "")


# ═══════════════════════════════════════════════════════════════════════════════
# 3.  main()
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Run the profile-augmenter demo with TEST_PROFILE and TEST_QUERY."""
    load_dotenv(PROJECT_ROOT / ".env")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("test_augmenter")

    settings = get_settings()
    logger.info("Using LLM: %s", settings.llm_model)

    # ── Embedding model ───────────────────────────────────────────────────
    embeddings = EmbeddingFactory.create(settings)

    # ── Profiles vector store ─────────────────────────────────────────────
    PROFILES_DIR = PROJECT_ROOT / "vectordb_profiles"
    if not (PROFILES_DIR / "index.tvim").exists():
        logger.error(
            "vectordb_profiles not found at %s.\n"
            "Run:  uv run python scripts/build_profiles_kb.py --force",
            PROFILES_DIR,
        )
        sys.exit(1)

    logger.info("Loading profiles vector store from %s", PROFILES_DIR)
    store = TurboQuantVectorStore.load(str(PROFILES_DIR), embedding=embeddings)
    retriever = store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    # ── LLM ───────────────────────────────────────────────────────────────
    llm = init_chat_model(
        model=settings.llm_profile,
        temperature=settings.llm_temperature,
    )

    # ── Collect unique document titles across all RAG lookups ──────────
    all_titles: set[str] = set()

    def _format_docs_with_titles(docs) -> str:
        """Format docs while collecting unique source titles."""
        parts = []
        seen = set()
        for d in docs:
            src = d.metadata.get("title", d.metadata.get("source_id", "Unknown"))
            all_titles.add(src)
            if src not in seen:
                seen.add(src)
                parts.append(f"[From: {src}]\n{d.page_content[:600].strip()}")
        return "\n\n".join(parts[:5])

    # ── RAG chain ─────────────────────────────────────────────────────────
    field_chain = (
        {
            "context": itemgetter("query") | retriever | _format_docs_with_titles,
            "field_name": itemgetter("field_name"),
            "field_value": itemgetter("field_value"),
        }
        | _RULE_PROMPT
        | llm
        | StrOutputParser()
    )

    # ── Merge user profile with defaults ──────────────────────────────────
    profile = dict(_STANDARD)
    profile.update({k: v for k, v in TEST_PROFILE.items() if v and str(v).strip()})

    # ── Build rules for each field ────────────────────────────────────────
    field_to_rule_key = {
        "age_group": "age_group_rules",
        "primary_language": "language_rules",
        "education_level": "education_rules",
        "indigenous_status": "indigenous_rules",
        "disability_status": "disability_rules",
        "gender": "gender_rules",
        "citizen_status": "citizen_rules",
        "sex_at_birth": "gender_rules",
    }

    rules: dict[str, str] = {}
    for field_key, rule_key in field_to_rule_key.items():
        rule = build_field_rule(field_key, profile[field_key], field_chain, logger)
        rules[rule_key] = rule

    # Fill any missing rule keys with standard defaults
    for k, v in _STANDARD_RULES.items():
        rules.setdefault(k, v)

    # ── Render the template ───────────────────────────────────────────────
    prompt = DYNAMIC_PROFILE_TEMPLATE.format(
        sex_at_birth=profile["sex_at_birth"],
        gender=profile["gender"],
        age_group=profile["age_group"],
        primary_language=profile["primary_language"],
        education_level=profile["education_level"],
        citizen_status=profile["citizen_status"],
        indigenous_status=profile["indigenous_status"],
        disability_status=profile["disability_status"],
        age_group_rules=rules.get("age_group_rules", _STANDARD_RULES["age_group_rules"]),
        language_rules=rules.get("language_rules", _STANDARD_RULES["language_rules"]),
        education_rules=rules.get("education_rules", _STANDARD_RULES["education_rules"]),
        indigenous_rules=rules.get("indigenous_rules", _STANDARD_RULES["indigenous_rules"]),
        disability_rules=rules.get("disability_rules", _STANDARD_RULES["disability_rules"]),
        gender_rules=rules.get("gender_rules", _STANDARD_RULES["gender_rules"]),
        citizen_rules=rules.get("citizen_rules", _STANDARD_RULES["citizen_rules"]),
        retrieved_documents=(
            "=== SOURCE DOCUMENTS USED TO GENERATE THIS PROFILE ===\n"
            + "\n".join(f"  • {t}" for t in sorted(all_titles))
            if all_titles
            else "No documents were retrieved."
        ),
        user_query=TEST_QUERY,
    )

    # ── Print the result ──────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("FINAL PROMPT")
    print("=" * 72)
    print(prompt)
    print("=" * 72)

    # Summary
    fields_provided = {k: v for k, v in TEST_PROFILE.items() if v and v != _STANDARD.get(k, "")}
    fields_defaulted = {k: v for k, v in profile.items() if k not in fields_provided}
    print(f"\nProfile summary:")
    print(f"   Non-default fields: {len(fields_provided)} \u2192 {list(fields_provided.keys())}")
    print(f"   Defaulted fields:   {len(fields_defaulted)} \u2192 {list(fields_defaulted.keys())}")
    print(f"   Prompt length:      {len(prompt)} characters")

    remaining = [p for p in [
        "{sex_at_birth}", "{gender}", "{age_group}", "{primary_language}",
        "{education_level}", "{citizen_status}", "{indigenous_status}",
        "{disability_status}", "{age_group_rules}", "{language_rules}",
        "{education_rules}", "{indigenous_rules}", "{disability_rules}",
        "{gender_rules}", "{citizen_rules}", "{retrieved_documents}", "{user_query}",
    ] if p in prompt]
    if remaining:
        print(f"Unfilled placeholders: {remaining}")
    else:
        print("All placeholders filled!")


if __name__ == "__main__":
    main()
