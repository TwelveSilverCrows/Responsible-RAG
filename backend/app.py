"""
app.py — FastAPI application entry point
=========================================
Run locally:
    uvicorn app:app --reload --port 8000

Run via Docker:
    docker compose up

Low-memory notes:
    - RAG chain is loaded lazily (not at import time).
    - Use async endpoints so a single process handles many concurrent requests.
    - Avoid storing large objects in memory per-request.
"""

from dotenv import load_dotenv

load_dotenv()  # Must happen before any src imports that read env vars

from src.api import create_app

app = create_app()
