# 🔍 RAG Chatbot — Canadian Academic Assistant

A **Retrieval-Augmented Generation (RAG)** chatbot tailored for Canadian academic contexts.  It combines a hybrid ensemble retriever (dense vector + BM25) with audience-specific system prompts so the same knowledge base can communicate appropriately to 2SLGBTQI+ teens, seniors, Indigenous community leaders, and disabled adults.

---

## Features

- **Hybrid retrieval** — ensemble of Chroma (vector similarity) + BM25 (keyword), weighted 70/30
- **Smart chunking** — semantic-first via `SemanticChunker`, with automatic recursive fallback
- **Population profiles** — four research-cited system-prompt personas (`RAGPopulation`)
- **Swappable embeddings** — OpenVINO (Intel CPU/NPU) or Nomic Embed via a single env flag
- **Clean architecture** — UI, core logic, profiles, and config are fully decoupled
- **Docker-ready** — single `docker compose up` for local or production deployment
- **API-expansion-ready** — `src/core` is framework-agnostic; add FastAPI without touching business logic

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/your-org/rag-chatbot.git
cd rag-chatbot
cp .env.example .env
# Edit .env and set at minimum: DEEPSEEK_API_KEY
```

### 2. Add knowledge-base documents

Drop `.txt` or `.pdf` files into `resources/` (sub-directories are scanned recursively).  The index is built automatically on first launch.

### 3a. Run locally

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

### 3b. Run via Docker

```bash
docker compose up --build
```

---

## Project Structure

```
rag-chatbot/
├── app.py                         # Streamlit entry point (wiring only)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── resources/                     # ← drop knowledge-base documents here
├── chroma_db/                     # ← auto-generated vector store (gitignored)
│
└── src/
    ├── config/
    │   └── settings.py            # Pydantic-settings; all env vars in one place
    │
    ├── core/                      # ⚡ Framework-agnostic business logic
    │   ├── embeddings.py          # EmbeddingFactory (OpenVINO | Nomic)
    │   ├── chunker.py             # SmartChunker (semantic → recursive fallback)
    │   ├── knowledge_base.py      # KnowledgeBase (Chroma lifecycle)
    │   ├── retriever.py           # RetrieverFactory (ensemble BM25 + vector)
    │   └── rag_chain.py           # RAGChain (full pipeline, invocable)
    │
    ├── profiles/
    │   └── population_profiles.py # RAGPopulation StrEnum — audience prompts
    │
    └── ui/
        ├── styles.py              # APP_STYLES CSS constant
        ├── components.py          # Stateless HTML rendering helpers
        └── chat_view.py           # ChatView — Streamlit page controller
```

---

## Configuration Reference

All settings live in `.env`.  See `.env.example` for the full annotated list.

| Variable | Default | Description |
|---|---|---|
| `LLM_MODEL` | `deepseek-chat` | LangChain model string |
| `DEEPSEEK_API_KEY` | — | Required for DeepSeek |
| `EMBEDDING_DEVICE` | `CPU` | `CPU` \| `NPU` \| `GPU` |
| `USE_NOMIC` | `false` | Switch to Nomic Embed backend |
| `USE_SEMANTIC_CHUNKING` | `true` | Disable to always use recursive splitter |
| `VEC_WEIGHT` | `0.7` | Ensemble weight for vector retriever |

---

## Audience Profiles

| Key | Audience | Research baseline |
|---|---|---|
| `LGBT_CANADIAN_TEEN` | 2SLGBTQI+ youth | NIH PMC 12919746 · Egale Canada |
| `SENIOR_LOW_EDU_CANADA` | Older adults, limited schooling | Frontiers Digital Health 2026 |
| `INDIGENOUS_COMMUNITY_LEADER_CA` | First Nations / Inuit / Métis leaders | TRC AI Standards |
| `MIDAGED_DISABLED_CANADIAN` | Disabled mid-aged adults | Accessibility Standards Canada |

To add a profile: add a new `StrEnum` member in `src/profiles/population_profiles.py`.  The UI and API pick it up automatically.

---

## Expanding to an API

`src/core` contains zero UI or framework dependencies.  To expose the same pipeline via a REST API:

```
src/
└── api/                           # New package — add when ready
    ├── __init__.py
    ├── main.py                    # FastAPI app
    ├── routers/
    │   └── chat.py                # POST /chat  →  RAGChain.invoke()
    └── schemas.py                 # Pydantic request / response models
```

Then add a second service in `docker-compose.yml` (a commented scaffold is already included).

---

## Contributing

1. Fork → feature branch → PR against `main`
2. Follow existing module docstring conventions
3. Run `ruff check .` and `mypy src/` before opening a PR

---

## License

MIT — see `LICENSE` for details.
