"""
components.py — Reusable Streamlit HTML components
====================================================
Pure rendering helpers — no business logic, no session-state reads.
Every function receives its data as arguments and calls ``st.markdown``
or ``st.components.v1.html`` to render it.

These are intentionally kept as module-level functions (not a class) so they
can be imported individually and composed in any page without coupling to a
specific view controller.
"""

import streamlit as st
import streamlit.components.v1 as components

# ── Static HTML snippets ──────────────────────────────────────────────────────

_EMPTY_STATE_HTML: str = (
    '<div class="empty-state">'
    '  <span class="empty-icon">💬</span>'
    '  <span>Your conversation will appear here</span>'
    "</div>"
)

_CHAT_WINDOW_TEMPLATE: str = '<div class="chat-window" id="chat-window">{inner}</div>'

_AUTO_SCROLL_JS: str = """
<script>
  const panel = window.parent.document.getElementById("chat-window");
  if (panel) panel.scrollTop = panel.scrollHeight;
</script>
"""


# ── Public rendering functions ────────────────────────────────────────────────


def render_header() -> None:
    """Render the application title and subtitle."""
    st.markdown('<p class="app-title">🔍 RAG Chatbot</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="app-subtitle">Context-aware answers — tailored to any audience</p>',
        unsafe_allow_html=True,
    )


def render_chat_window(history: list[dict]) -> None:
    """
    Render the scrollable chat window.

    Parameters
    ----------
    history:
        Conversation history — a list of dicts with keys
        ``"question"``, ``"group"``, and ``"answer"``.
    """
    if not history:
        inner = _EMPTY_STATE_HTML
    else:
        rows: list[str] = []
        for idx, entry in enumerate(history):
            if idx > 0:
                rows.append('<hr class="exchange-divider">')
            rows.append(_build_message_pair(entry))
        inner = "\n".join(rows)

    st.markdown(_CHAT_WINDOW_TEMPLATE.format(inner=inner), unsafe_allow_html=True)


def render_auto_scroll() -> None:
    """Inject a zero-height JS snippet that scrolls the chat window to the bottom."""
    components.html(_AUTO_SCROLL_JS, height=0)


def render_source_tooltip(sources: list[str]) -> str:
    """
    Render a hoverable source indicator with tooltip showing all source files.

    Parameters
    ----------
    sources:
        List of source file paths used to generate the answer.

    Returns
    -------
    str
        HTML string for the source indicator with tooltip.
    """
    if not sources:
        return ""

    # Build the tooltip content - show each source on a new line
    tooltip_content = "<br>".join(
        f"{i + 1}. {source}" for i, source in enumerate(sources)
    )

    return (
        f'<span class="source-tooltip" data-tooltip="{tooltip_content}">'
        f'📄 Sources ({len(sources)})'
        f"</span>"
    )


# ── Private HTML builders ─────────────────────────────────────────────────────


def _build_message_pair(entry: dict) -> str:
    """
    Build the HTML for a single user question + assistant answer exchange.

    Parameters
    ----------
    entry:
        Dict with keys ``"question"`` (str), ``"group"`` (str), ``"answer"`` (str), ``"sources"`` (list[str]).

    Returns
    -------
    str
        Raw HTML string for the message pair.
    """
    sources = entry.get("sources", [])
    source_html = render_source_tooltip(sources) if sources else ""

    return (
        f'<div class="msg-row user">'
        f'  <div class="msg-meta">YOU</div>'
        f'  <div class="bubble">{entry["question"]}</div>'
        f"</div>"
        f'<div class="msg-row bot">'
        f'  <div class="msg-meta">ASSISTANT'
        f'    <span class="badge">{entry["group"]}</span>'
        f"    {source_html}"
        f"  </div>"
        f'  <div class="bubble">{entry["answer"]}</div>'
        f"</div>"
    )
