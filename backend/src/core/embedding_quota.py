"""
embedding_quota.py — Embedding API quota monitor with cooldown
================================================================
Monitors HuggingFace Inference API errors and manages a cooldown period
to avoid hammering the API when quota is exhausted or rate-limited.

The cooldown state is persisted to a JSON file so it survives server
restarts.  Admin alerts are logged and optionally stored in MongoDB
so the admin dashboard can surface them.

Usage
-----
    from src.core.embedding_quota import EmbeddingQuotaMonitor, EmbeddingCooldownError

    monitor = EmbeddingQuotaMonitor()
    if monitor.is_in_cooldown():
        print(f"Cooldown active — {monitor.get_cooldown_remaining():.0f}s remaining")

    try:
        result = embedding_fn.embed_documents(texts)
    except Exception as exc:
        monitor.record_error(exc)       # triggers cooldown if quota error
        raise
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Custom exception ──────────────────────────────────────────────────────────


class EmbeddingCooldownError(RuntimeError):
    """
    Raised when the embedding API is in cooldown and a call is attempted.

    Callers should catch this and respond with a degraded fallback or
    a 503 Service Unavailable with a ``Retry-After`` header.
    """


# ── Quota indicators ─────────────────────────────────────────────────────────
# Substrings that, when present in an exception message, indicate a
# quota / rate-limit / server-capacity error from the HuggingFace API.
_QUOTA_INDICATORS: tuple[str, ...] = (
    # HTTP status codes
    "429",
    "503",
    "504",
    # Rate-limit wording
    "rate limit",
    "rate_limit",
    "ratelimit",
    "too many requests",
    "quota",
    "capacity",
    "overloaded",
    # Server-error wording
    "service unavailable",
    "gateway time-out",
    "gateway timeout",
    "server error",
)


def _is_quota_error(error: Exception) -> bool:
    """Return ``True`` if *error* looks like a quota / rate-limit failure."""
    error_str = str(error).lower()
    return any(indicator in error_str for indicator in _QUOTA_INDICATORS)


# ═══════════════════════════════════════════════════════════════════════════════
# EmbeddingQuotaMonitor
# ═══════════════════════════════════════════════════════════════════════════════


class EmbeddingQuotaMonitor:
    """
    Monitors embedding API errors and manages a configurable cooldown.

    Thread-safe for single-process use (the default FastAPI / Uvicorn model).
    For multi-worker deployments, the JSON state file acts as a simple
    cross-process lock — each worker reads it on init and writes on update.

    Parameters
    ----------
    state_dir:
        Directory used for persisting the cooldown state file.
        Defaults to ``"../storage/vectordb"``.
    cooldown_seconds:
        Duration of the cooldown period in seconds.  Default is 7200 (2 h).
    """

    def __init__(
        self,
        state_dir: str = "../storage/vectordb",
        cooldown_seconds: int = 7200,
    ) -> None:
        self._state_path = Path(state_dir) / ".embedding_cooldown.json"
        self._cooldown_seconds = cooldown_seconds
        self._cooldown_until: Optional[datetime] = None
        self._load_state()

    # ── Public API ────────────────────────────────────────────────────────────

    def is_in_cooldown(self) -> bool:
        """
        Return ``True`` if a cooldown is currently active.

        Automatically clears the cooldown if the deadline has passed.
        """
        if self._cooldown_until is None:
            return False
        if datetime.now(timezone.utc) >= self._cooldown_until:
            logger.info("Embedding API cooldown has expired.")
            self._cooldown_until = None
            self._save_state()
            return False
        return True

    def get_cooldown_remaining(self) -> float:
        """Return the number of seconds remaining in the cooldown (0 if none)."""
        if self._cooldown_until is None:
            return 0.0
        remaining = (self._cooldown_until - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, remaining)

    def record_error(self, error: Exception) -> bool:
        """
        Inspect *error* and trigger a cooldown if it's a quota-related failure.

        Returns ``True`` if a cooldown was newly triggered, ``False`` if
        the error was not quota-related or a cooldown was already active.
        """
        if not _is_quota_error(error):
            return False

        if self.is_in_cooldown():
            # Already in cooldown — just log and return
            logger.debug(
                "Embedding API error repeated during cooldown: %s",
                _truncate(str(error), 200),
            )
            return False

        self._trigger_cooldown(error)
        return True

    def check_or_raise(self) -> None:
        """
        Raise :class:`EmbeddingCooldownError` if cooldown is active.

        Call this at the top of any endpoint that depends on embeddings
        to produce a graceful 503 response.
        """
        if self.is_in_cooldown():
            remaining = self.get_cooldown_remaining()
            raise EmbeddingCooldownError(
                f"Embedding API is in cooldown for another {remaining:.0f} seconds "
                f"(~{remaining // 60:.0f} minutes).  Semantic chunking and embedding "
                f"operations are temporarily disabled."
            )

    def remaining_minutes(self) -> int:
        """Convenience: return remaining cooldown as whole minutes."""
        return int(self.get_cooldown_remaining() // 60)

    # ── Cooldown lifecycle ────────────────────────────────────────────────────

    def _trigger_cooldown(self, error: Exception) -> None:
        """Start the cooldown period and alert the admin."""
        self._cooldown_until = datetime.now(timezone.utc) + timedelta(
            seconds=self._cooldown_seconds,
        )
        self._save_state()
        logger.warning(
            "EMBEDDING QUOTA ERROR — entering cooldown until %s UTC "
            "(%d minutes).  Error: %s",
            self._cooldown_until.isoformat(),
            self._cooldown_seconds // 60,
            _truncate(str(error), 300),
        )
        self._alert_admin(error)

    def _alert_admin(self, error: Exception) -> None:
        """Log the alert and persist it to MongoDB if available."""
        alert: dict[str, str] = {
            "type": "embedding_quota",
            "severity": "critical",
            "title": "Embedding API quota exhausted — cooldown activated",
            "message": (
                f"The HuggingFace Inference API returned a quota/rate-limit "
                f"error.  Embedding operations are paused for "
                f"{self._cooldown_seconds // 60} minutes.\n\n"
                f"Error details: {error}"
            ),
            "cooldown_until": self._cooldown_until.isoformat()
            if self._cooldown_until
            else "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resolved": "false",
        }
        # Always log at ERROR level so it appears in container logs
        logger.error("ADMIN ALERT [embedding_quota]: %s", json.dumps(alert))

        # Try to persist in MongoDB for the admin dashboard
        self._persist_alert(alert)

    def _persist_alert(self, alert: dict) -> None:
        """Store the alert document in MongoDB's ``admin_alerts`` collection."""
        try:
            from src.api.db.database import get_database

            db = get_database()
            if db is not None:
                db["admin_alerts"].insert_one(alert)
                logger.debug("Admin alert persisted to MongoDB.")
        except Exception as exc:
            logger.debug("Could not persist admin alert to MongoDB: %s", exc)

    # ── State persistence ─────────────────────────────────────────────────────

    def _load_state(self) -> None:
        """Restore cooldown state from the JSON file on disk."""
        try:
            if not self._state_path.exists():
                return
            data = json.loads(self._state_path.read_text())
            until_str = data.get("cooldown_until")
            if until_str:
                self._cooldown_until = datetime.fromisoformat(until_str)
                # If the stored deadline is already past, clear it immediately
                if datetime.now(timezone.utc) >= self._cooldown_until:
                    logger.info("Loaded stale cooldown — clearing (deadline passed).")
                    self._cooldown_until = None
                    self._save_state()
                else:
                    remaining = self.get_cooldown_remaining()
                    logger.info(
                        "Restored embedding cooldown — %d seconds remaining.",
                        int(remaining),
                    )
        except Exception as exc:
            logger.warning("Failed to load embedding cooldown state: %s", exc)
            self._cooldown_until = None

    def _save_state(self) -> None:
        """Persist the current cooldown state to the JSON file."""
        try:
            data: dict[str, object] = {
                "cooldown_until": self._cooldown_until.isoformat()
                if self._cooldown_until
                else None,
            }
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            self._state_path.write_text(json.dumps(data, indent=2))
        except Exception as exc:
            logger.warning("Failed to save embedding cooldown state: %s", exc)


# ── Module-level singleton helpers ────────────────────────────────────────────

_MONITOR: Optional[EmbeddingQuotaMonitor] = None


def get_quota_monitor() -> EmbeddingQuotaMonitor:
    """
    Return the application-wide :class:`EmbeddingQuotaMonitor` singleton.

    The monitor is lazily created on first call, using the vector-store
    directory from settings for state persistence.
    """
    global _MONITOR
    if _MONITOR is None:
        from src.core.config import get_settings

        settings = get_settings()
        _MONITOR = EmbeddingQuotaMonitor(
            state_dir=settings.vectordb_dir,
            cooldown_seconds=settings.embedding_cooldown_seconds,
        )
    return _MONITOR


def _truncate(text: str, max_len: int) -> str:
    """Truncate *text* to *max_len* characters, appending ``…`` if needed."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"
