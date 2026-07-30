""" Memory helper module for RAGChain. """

from typing import Any

DEFAULT_RECENT_TURNS = 8
MAX_FACTS = 10

def _init_memory_doc(now: str) -> dict[str, Any]:
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


def _build_memory_context(memory:dict, recent_turns: list[dict])-> str:
    """Build a context string from the memory summary, facts, and recent turns."""
    if not memory or not memory.get("enabled", True):
        return ""

    summary = memory.get("summary", "").strip()
    facts = memory.get("facts", [])
    recent_turns_text = "\n".join(
        f"{turn['role'].title()}: {turn['content']}"
        for turn in recent_turns
    )
    pieces = []
    if summary:
        pieces.append(f"Summary of conversation so far:\n{summary}")
    if facts:
        pieces.append(f"Facts:\n" + "\n".join(f"- {fact}" for fact in facts))
    if recent_turns_text:
        pieces.append(f"Recent conversation:\n" + recent_turns_text)

    return "\n\n".join(pieces)

def _update_memory_facts(
    current_facts: list[str],
    user_question: str,
    assistant_answer: str,
) -> list[str]:
    facts = list(dict.fromkeys(current_facts))
    lower = user_question.lower()

    if "student loan" in lower and not any("student loan" in fact.lower() for fact in facts):
        facts.append("Topic: Canadian student loans")

    if "concise" in lower or "short" in lower:
        if not any("concise" in fact.lower() for fact in facts):
            facts.append("Prefers concise explanations")

    # Keep the list bounded
    return facts[-MAX_FACTS:]


def _update_memory(memory:dict, user_question:str, assistant_answer:str, recent_turns:list[dict], now:str) -> dict:
    """Update the memory document with new summary, facts, and recent turns."""
    # Extract facts from the user question and assistant answer
    new_facts = _extract_memory_facts(memory, user_question, assistant_answer)
    updated_facts = _update_memory_facts(memory.get("facts", []), user_question, assistant_answer)

    # Update recent turns
    updated_recent_turns = recent_turns[-10:]  # Keep only the last 10 turns

    # Update summary 
    #TODO: Implement a more sophisticated summary update, possibly using an LLM to summarise the conversation so far
    if memory.get("summary"):
        updated_summary = memory.get("summary", "") + f"\nUser: {user_question}\nAssistant: {assistant_answer}"
    else:
        updated_summary = f"User: {user_question}\nAssistant: {assistant_answer}" # have to set the summary to something to break out of the empty state

    return {
        "enabled": memory.get("enabled", True),
        "summary": updated_summary.strip(),
        "facts": updated_facts,
        "recent_turns": updated_recent_turns,
        "last_refreshed_at": now,
        "last_refreshed_turn_count": len(updated_recent_turns),
    }

def _extract_memory_facts(memory: dict, user_question: str, assistant_answer: str) -> list[str]:
    # Minimal first version: keep previous facts, add any new obvious fact
    memory_facts = memory.get("facts", [])
    #TODO: Implement a more sophisticated fact extraction from the user question and assistant answer
    return memory_facts

def _fetch_recent_turns(db, conversation_id: str, limit: int = 5) -> list[dict]:
    """Fetch the most recent turns (user + assistant messages) for a conversation."""
    cursor = db["messages"].find({"conversation_id": conversation_id})
    cursor = cursor.sort("created_at", -1).limit(limit * 2)  # Fetch more to account for both roles
    turns = [{"role": m["role"], "content": m["content"], "created_at": m["created_at"]} for m in cursor]
    return list (reversed(turns))  # Return in chronological order, turns is a stack of messages, so we reverse it to get the correct order

