# 🔍 RAG Chatbot — Canadian Academic Assistant

A **Retrieval-Augmented Generation (RAG)** chatbot tailored for Canadian academic contexts.  It combines a hybrid ensemble retriever (dense vector + BM25) with audience-specific system prompts so the same knowledge base can communicate appropriately to 2SLGBTQI+ teens, seniors, Indigenous community leaders, and disabled adults.

---

## Features

- **Hybrid retrieval** — ensemble of TurboVec (vector similarity) + BM25 (keyword), weighted 70/30
- **Smart chunking** — semantic-first via `SemanticChunker`, with automatic recursive fallback
- **Population profiles** — four research-cited system-prompt personas (`RAGPopulation`)
- **Cloud embeddings** — Hugging Face Inference API (same BAAI/bge-large-en-v1.5 model, zero local deps)
- **Clean architecture** — UI, core logic, profiles, and config are fully decoupled
- **Docker-ready** — full `docker compose` setup for the entire stack
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

### 3a. Run locally (backend only)

Requires a running MongoDB instance.  The easiest way is via Docker:

```bash
docker run -d --name rag-mongo \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=rag \
  -e MONGO_INITDB_ROOT_PASSWORD=ragpassword \
  -e MONGO_INITDB_DATABASE=responsible_rag \
  mongo:7
```

Then start the backend:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

Open [http://localhost:8000/docs](http://localhost:8000/docs).

For the frontend, see `frontend/package.json` scripts (requires Bun or Node):

```bash
cd frontend
bun install    # or npm install
bun run dev    # or npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3b. Run via Docker

Build and start all services (MongoDB, backend, frontend, and optionally Caddy):

```bash
docker compose up --build
```

Open the frontend at [http://localhost:3000](http://localhost:3000) and the backend API at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Docker Compose Reference

The stack consists of three services:

| Service   | Container         | Port(s)  | Tech                          |
|-----------|-------------------|----------|-------------------------------|
| MongoDB   | `rag-mongo`       | 27017    | MongoDB 7 (host-persisted)    |
| Frontend  | `rag-frontend`    | 3000     | Vite + React (Bun)            |
| Backend   | `rag-backend`     | 8000     | FastAPI (Python)              |

> **Note:** MongoDB data is stored on the host at `./data/mongo/` so it survives container restarts and rebuilds. An initialisation script (`./data/mongo/init.js`) runs automatically on first start to create the database, user, and indexes.

### Common commands

| Action | Command |
|---|---|
| **Build & start** | `docker compose up --build` |
| **Start in background** | `docker compose up --build -d` |
| **Stop** | `docker compose down` |
| **Stop & delete volumes** | `docker compose down -v` |
| **Rebuild a single service** | `docker compose build frontend` (or `backend`) |
| **Restart a service** | `docker compose restart frontend` |
| **View logs (all)** | `docker compose logs -f` |
| **View logs (one service)** | `docker compose logs -f backend` (or `mongo`) |
| **View running containers** | `docker compose ps` |
| **Shell into a container** | `docker compose exec mongo mongosh --quiet` |

---

## Project Structure

```
rag-chatbot/
├── docker-compose.yml             # Orchestrates MongoDB + frontend + backend
├── .env.example                   # Copy to .env and configure
│
├── data/
│   └── mongo/
│       ├── init.js                # First-run DB/user/index creation
│       └── ...                    # MongoDB data files (gitignored)
│
├── backend/
│   ├── Dockerfile                 # Multi-stage build (uv + hatchling)
│   ├── app.py                     # Streamlit entry point (wiring only)
│   └── src/
│       ├── config/
│       │   └── settings.py        # Pydantic-settings; all env vars in one place
│       │
│       ├── core/                  # ⚡ Framework-agnostic business logic
│       │   ├── chunker.py         # SmartChunker (semantic → recursive fallback)
│       │   ├── embeddings.py      # EmbeddingFactory (OpenVINO | Nomic)
│       │   ├── profiles.py        # Audience-specific prompts
│       │   ├── rag_chain.py       # RAGChain (full pipeline, invocable)
│       │   ├── retrievers.py      # RetrieverFactory (ensemble BM25 + vector)
│       │   └── vector_store.py    # TurboVec lifecycle
│       └── ui/
│           ├── app.py             # ChatView — Streamlit page controller
│           ├── components.py      # Stateless HTML rendering helpers
│           └── styles.py          # APP_STYLES CSS constant
│
├── frontend/
│   ├── Dockerfile                 # Multi-stage Vite build (Bun)
│   ├── package.json
│   ├── vite.config.ts
│   └── src/                       # React app (see frontend/src/)
│
├── resources/                     # ← drop knowledge-base documents here
└── vectordb/                      # ← auto-generated vector store (gitignored)
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
| `MONGO_URI` | — | MongoDB connection string (local Docker or external) |
| `MONGO_DB` | `responsible_rag` | MongoDB database name |
| `MONGO_ROOT_USER` | `rag` | MongoDB root username (Docker init only) |
| `MONGO_ROOT_PASSWORD` | `ragpassword` | MongoDB root password (Docker init only) |
| `MONGO_APP_USER` | `rag` | MongoDB app user (created by init.js) |
| `MONGO_APP_PASSWORD` | `ragpassword` | MongoDB app user password |

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

`backend/src/core` contains zero UI or framework dependencies.  To expose the same pipeline via a REST API:

```
backend/src/
└── api/                           # New package — add when ready
    ├── __init__.py
    ├── main.py                    # FastAPI app
    ├── routers/
    │   └── chat.py                # POST /chat  →  RAGChain.invoke()
    └── schemas.py                 # Pydantic request / response models
```

Then add a third service in `docker-compose.yml`.

---

## Contributing

1. Fork → feature branch → PR against `main`
2. Follow existing module docstring conventions
3. Run `ruff check .` and `mypy src/` before opening a PR

---

## License

MIT — see `LICENSE` for details.
