"""
app.py — Streamlit chat page controller
=========================================
:class:`ChatView` is the single Streamlit page controller.  It:

* owns and guards the session-state history list
* delegates all HTML rendering to :mod:`src.ui.components`
* dispatches user interactions (send / clear) to :class:`RAGChain`
* never contains business logic — it is purely presentation + orchestration

This module is imported and called by the root ``app.py`` entry point.
"""

import streamlit as st

from src.core.profiles import RAGPopulation
from src.core.rag_chain import RAGChain
from src.ui.components import render_auto_scroll, render_chat_window, render_header
from src.ui.styles import APP_STYLES

# History entry schema: {"question": str, "group": str, "answer": str, "sources": list[str]}
_HistoryEntry = dict[str, str | list[str]]


class ChatView:
    """
    Streamlit chat page controller.

    Instantiate once per Streamlit rerun (``ChatView`` itself holds no mutable
    state — all persistence lives in ``st.session_state``).

    Parameters
    ----------
    rag_chain:
        A fully initialised :class:`RAGChain` instance (typically cached via
        ``@st.cache_resource`` in the entry-point module).
    """

    _HISTORY_KEY: str = "chat_history"

    def __init__(self, rag_chain: RAGChain) -> None:
        self._chain = rag_chain
        self._ensure_session_state()

    # ── Public API ────────────────────────────────────────────────────────────

    def render(self) -> None:
        """Render the full page.  Called once per Streamlit rerun."""
        st.markdown(APP_STYLES, unsafe_allow_html=True)
        render_header()
        render_chat_window(self._history)
        render_auto_scroll()
        self._render_controls()

    # ── Session-state helpers ─────────────────────────────────────────────────

    def _ensure_session_state(self) -> None:
        """Initialise the history list on the first run of a session."""
        if self._HISTORY_KEY not in st.session_state:
            st.session_state[self._HISTORY_KEY] = []

    @property
    def _history(self) -> list[_HistoryEntry]:
        """Convenience accessor for the session-state history list."""
        return st.session_state[self._HISTORY_KEY]

    # ── Controls rendering ────────────────────────────────────────────────────

    def _render_controls(self) -> None:
        """Render the audience selector, question input, and action buttons."""
        group_keys = RAGPopulation.get_valid_keys()

        st.markdown('<p class="field-label">Audience group</p>', unsafe_allow_html=True)
        selected_key: str = st.selectbox(
            "Audience group",
            options=group_keys,
            label_visibility="collapsed",
        )
        selected_prompt: str = RAGPopulation[selected_key].value

        st.markdown('<p class="field-label">Your question</p>', unsafe_allow_html=True)
        question: str = st.text_input(
            "Your question",
            placeholder="e.g. How does predictive policing affect minority communities?",
            label_visibility="collapsed",
        )

        col_send, col_clear = st.columns([5, 1])
        with col_send:
            send_clicked = st.button("Send  ➤", use_container_width=True)
        with col_clear:
            clear_clicked = st.button("Clear", use_container_width=True)

        if send_clicked:
            self._handle_send(question.strip(), selected_key, selected_prompt)

        if clear_clicked:
            self._handle_clear()

    # ── Event handlers ────────────────────────────────────────────────────────

    def _handle_send(
        self,
        question: str,
        group_key: str,
        group_prompt: str,
    ) -> None:
        """Validate, invoke the RAG chain, append to history, and rerun."""
        if not question:
            st.warning("Please enter a question before sending.")
            return

        with st.spinner("Thinking…"):
            try:
                result = self._chain.invoke(question, group_prompt)
                self._history.append(
                    {
                        "question": question,
                        "group": group_key,
                        "answer": result.answer,
                        "sources": result.sources,
                    }
                )
            except Exception as exc:
                st.error(f"Error generating answer: {exc}")
                return

        st.rerun()

    def _handle_clear(self) -> None:
        """Clear the conversation history and rerun."""
        self._history.clear()
        st.rerun()
