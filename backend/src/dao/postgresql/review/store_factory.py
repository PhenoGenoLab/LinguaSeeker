"""Construct Phase 5 persistence stores from one session factory."""

from __future__ import annotations

from typing import Any

from src.dao.postgresql.review.chat_store import PostgresChatStore
from src.dao.postgresql.review.feedback_store import PostgresFeedbackStore
from src.dao.postgresql.review.source_link_store import PostgresSourceLinkStore


class PostgresReviewStoreFactory:
    """Create review stores that share a session factory."""

    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    def chat_store(self) -> PostgresChatStore:
        return PostgresChatStore(self._session_factory)

    def feedback_store(self) -> PostgresFeedbackStore:
        return PostgresFeedbackStore(self._session_factory)

    def source_link_store(self) -> PostgresSourceLinkStore:
        return PostgresSourceLinkStore(self._session_factory)
