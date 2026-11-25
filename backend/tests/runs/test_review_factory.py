"""Tests for ReviewServiceFactory."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.pipeline.skills.review.factory import ReviewServiceFactory
from src.pipeline.skills.review.chat_service import ChatService
from src.core.tools.review.delta_audit_service import (
    DeltaAuditService,
)
from src.dao.postgresql.review.feedback_store import (
    FeedbackService,
)
from src.dao.postgresql.review.source_link_store import PostgresSourceLinkStore


@pytest.fixture
def factory() -> ReviewServiceFactory:
    return ReviewServiceFactory(cfg=MagicMock(), session_factory=MagicMock())


def test_create_feedback_service(factory: ReviewServiceFactory):
    """create_feedback_service returns a FeedbackService instance."""
    session = MagicMock()
    service = factory.create_feedback_service(session)
    assert isinstance(service, FeedbackService)


def test_create_chat_service(factory: ReviewServiceFactory):
    """create_chat_service returns a ChatService instance."""
    service = factory.create_chat_service()
    assert isinstance(service, ChatService)


def test_create_source_linker(factory: ReviewServiceFactory):
    """create_source_linker returns a session-per-call store."""
    linker = factory.create_source_linker()
    assert isinstance(linker, PostgresSourceLinkStore)


def test_delta_audit_returns_singleton(factory: ReviewServiceFactory):
    """delta_audit property returns the same DeltaAuditService instance."""
    audit1 = factory.delta_audit
    audit2 = factory.delta_audit
    assert isinstance(audit1, DeltaAuditService)
    assert audit1 is audit2
