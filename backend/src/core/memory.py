""" Memory helper module for RAGChain. """
from __future__ import annotations

import json
import re
from operator import itemgetter
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.core.config import get_settings

DEFAULT_RECENT_TURNS = 8
MAX_FACTS = 10
_REFRESH_EVERY = 1

_SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    "You are a memory assistant that updates a concise session summary based "
    "on the user's conversation history. The summary should capture the user's "
    "goals, preferences, topics, and any stated health or disability details."
    "\n\nExisting summary:\n{existing_summary}\n\n"
    "Recent conversation:\n{recent_turns}\n\n"
    "Produce a short summary in 2-3 sentences. If the existing summary already "
    "captures the context, preserve it and only add new, relevant details."
)

_FACTS_PROMPT = ChatPromptTemplate.from_template(
    "You are a memory assistant that extracts explicit user facts from the "
    "conversation history. Only include user statements; do not include assistant text. "
    "Return a JSON array of strings only, with each string in one of these canonical forms: "
    "\"Health condition: ...\" , \"Disability: ...\" , \"Location: ...\" , \"Preference: ...\" , \"Goal: ...\" , \"Topic: ...\" .\n\n"
    "Conversation:\n{recent_turns}\n\n"
    "If there are no extractable facts, return an empty array: []."
)


class MemoryAgent:
    #helps initialise, update and generate summaries and facts from chat transcripts


    def __init__(self) -> None:
        self._settings = get_settings()
        self._llm = None
        self._summary_chain = None
        self._facts_chain = None

    def _get_llm(self):
        """ This function initialises the chat model for memory purposes."""
        if self._llm is None:
            self._llm = init_chat_model(
                model = self._settings.llm_model,
                temperature = self._settings.llm_temperature,
            )
        return self._llm

    def _get_summary_chain(self):
        """
        This function initialises the summary chain.
        Summaries of chat transcripts enable short-term memory.
        """
        if self._summary_chain is None:
            #itemgetter used for efficiency
            self._summary_chain = (
                {
                    "existing_summary": itemgetter("existing_summary"),
                    "recent_turns": itemgetter("recent_turns")
                }
                | _SUMMARY_PROMPT
                | self._get_llm()
                | StrOutputParser()
            )
        return self._summary_chain

    def _get_facts_chain(self):
        """ 
        This functions intialises facts chain.
        Fact extraction enables long-term memory.
        """
        if self._facts_chain is None:
            self._facts_chain = (
                {"recent_turns": itemgetter("recent_turns")}
                |_FACTS_PROMPT
                |self._get_llm()
                |StrOutputParser()
            )
        return self._facts_chain

    def _update_summary(self, existing_summary: str, recent_turns:str) -> str:
        """Update the summary with the latest question and answer."""
        if not recent_turns.strip():
            return existing_summary.strip()
        summary = self._get_summary_chain().invoke(
            {"existing_summary": existing_summary or "", "recent_turns": recent_turns}
        )
        return summary.strip()

    def _extract_memory_facts(self, recent_turns:str) -> list[str]:
        """Extraction of facts from chats enables long-term memory about the user's goals, relevant medical conditions, etc."""
        if not recent_turns.strip():
            return []
        raw = self._get_facts_chain().invoke({"recent_turns": recent_turns})
        return format_facts(parse_json_array(raw))

############## Helper functions

def init_memory(now: str) -> dict[str, Any]:
    """Initialise a new memory document with default values."""
    return {
        "enabled": True,
        "summary": "",
        "facts": [],
        "recent_turns": [],
        "last_refreshed_at": now,
        "last_refreshed_turn_count": 0,
    }

def trim_recent_turns(recent_turns: list[dict[str, str]], limit: int = DEFAULT_RECENT_TURNS) -> list[dict[str, str]]:
    """Trim the recent turns list to the specified limit."""
    return recent_turns[-limit:]

def format_recent_turns(recent_turns: list[dict[str,str]])->str:
    """
    Helper function: adds new line between turns in chat.
    """
    return "\n".join(
        f"{turn['role'].title()}:{turn['content']}"
        for turn in recent_turns
    )

def build_memory_context(memory:dict[str,Any], recent_turns: list[dict[str,str]]) -> str:
    """Build a context string from the memory summary, facts, and recent turns."""

    if not memory or not memory.get("enabled", True):
        return ""

    pieces = []

    summary = memory.get("summary", "").strip()
    if summary:
        pieces.append(f"Summary:\n{summary}")

    facts = [fact.strip() for fact in memory.get("facts", []) if fact and fact.strip()]
    if facts:
        pieces.append(f"Facts:\n" + "\n".join(f"- {fact}" for fact in facts))

    recent_text = format_recent_turns(recent_turns)
    if recent_text:
        pieces.append(f"Recent conversation:\n" + recent_text)

    return "\n\n".join(pieces)

def should_update_memory(memory: dict[str, Any], total_turn_count: int) -> bool:
    """
    Returns True if enough turns have passed to justify refreshing memory.
    total_turn_count is the STABLE total number of messages in the
    conversation (from db.count_documents), not a truncated in-memory list.
    """
    if total_turn_count <= 0:
        return False

    # Always refresh once if there is no summary yet
    if not memory.get("summary", "").strip():
        return True

    last_refreshed_turn_count = memory.get("last_refreshed_turn_count", 0)
    return (total_turn_count - last_refreshed_turn_count) >= _REFRESH_EVERY



def update_memory(
    memory: dict,
    user_question: str,
    assistant_answer: str,
    recent_turns: list[dict],
    now: str,
    agent: MemoryAgent,
    total_turn_count: int,
) -> dict:
    """Update the memory document with the latest exchange and refreshed summary/facts."""
    recent_turns = trim_recent_turns(recent_turns)
    recent_text = format_recent_turns(recent_turns)

    summary = agent._update_summary(memory.get("summary", ""), recent_text)
    extracted = agent._extract_memory_facts(recent_text)
    facts = update_facts(memory.get("facts", []), extracted)

    return {
        "enabled": memory.get("enabled", True),
        "summary": summary,
        "facts": facts,
        "recent_turns": recent_turns,
        "last_refreshed_at": now,
        "last_refreshed_turn_count": total_turn_count,   # stable, matches next turn's count
    }



def update_facts(existing: list[str], new_facts: list[str]) -> list[str]:
    """
    Helper function that updates old facts with new ones.
    """
    existing = [fact.strip() for fact in existing if fact and fact.strip()]
    merged = list(dict.fromkeys(existing + [fact for fact in new_facts if fact and fact.strip()]))
    return merged[-MAX_FACTS:]


def format_facts(facts: list[Any]) -> list[str]:
    """
    Helper function that cleans up facts before adding to memory.
    """
    normalised: list[str] = []
    seen: set[str] = set()
    for fact in facts:
        if not isinstance(fact, str):
            continue
        text = fact.strip()
        if not text:
            continue
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        normalised.append(text)
        if len(normalised) >= MAX_FACTS:
            break
    return normalised


def parse_json_array(raw: str) -> list[str]:
    """
    Takes output from llm and tries to extract json of facts to put into the mongoDB, else does line extraction.
    This function is to ensure that output from llm is processed correctly.
    """
    candidate = raw.strip()
    candidate = re.sub(r"^```(?:json)?\n", "", candidate, flags=re.I)
    candidate = re.sub(r"\n```$", "", candidate)

    json_start = candidate.find("[")
    json_end = candidate.rfind("]")
    if json_start != -1 and json_end != -1 and json_end > json_start:
        candidate = candidate[json_start : json_end + 1]

    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    return []

def fetch_recent_turns(db, conversation_id: str, limit: int = 8) -> list[dict]:
    """
    Helper function to return the limit-th most recent entries in the conversation.
    """
    if db is None:
        return []

    cursor = db["messages"] \
        .find({"conversation_id": conversation_id}) \
        .sort("created_at", -1) \
        .limit(limit)

    turns = [
        {
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
            "created_at": msg.get("created_at", ""),
        }
        for msg in cursor
    ]
    return list(reversed(turns))