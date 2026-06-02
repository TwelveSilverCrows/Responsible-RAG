"""
app.py — Application entry point
==================================
Thin launcher: loads env vars, configures the Streamlit page, builds and
caches the RAG chain, then hands off entirely to ChatView.

Run locally:
    streamlit run app.py

Run via Docker:
    docker compose up
"""

from dotenv import load_dotenv

load_dotenv()  # Must happen before any src imports that read env vars

import streamlit as st  # noqa: E402 — must come after load_dotenv

from src.core.config import get_settings
from src.core.rag_chain import RAGChain
from src.ui.app import ChatView

# ── Streamlit page config (must be the first Streamlit call) ──────────────────
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🔍",
    layout="centered",
)


# ── Cached resource builder ───────────────────────────────────────────────────


@st.cache_resource(show_spinner=False)
def _init_rag_chain() -> RAGChain:
    """Build the full RAG pipeline once and cache it for the server lifetime."""
    return RAGChain(get_settings())


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    with st.spinner("⚙️  Loading knowledge base…"):
        try:
            chain = _init_rag_chain()
        except Exception as exc:
            st.error(f"Failed to initialise the knowledge base: {exc}")
            st.stop()

    ChatView(chain).render()


main()
