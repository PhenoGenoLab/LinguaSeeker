"""API dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.pipeline.skills.review.factory import ReviewServiceFactory
from src.api.wiring import get_session_factory
from src.dao.neo4j.repository import Neo4jRepository
from src.dao.postgresql.users import PostgresUserStore
from src.dao.postgresql.review.annotation_store import PostgresAnnotationStore
from src.dao.postgresql.review.evidence_store import PostgresEvidenceStore
from src.dao.postgresql.review.audit_store import PostgresAuditStore
from src.dao.postgresql.review.feedback_store import PostgresFeedbackStore
from src.dao.postgresql.review.literature_store import PostgresLiteratureStore
from src.dao.postgresql.run_state_store import PostgresRunStateStore
from src.runs import RunStateStore
from src.ports.review import (
    AnnotationStore,
    AuditStore,
    EvidenceQueryStore,
    FeedbackStore,
    LiteratureStore,
)
from src.ports.users import UserStore

_review_factory: ReviewServiceFactory | None = None
_neo4j_repository: Neo4jRepository | None = None


def set_neo4j_repository(repository: Neo4jRepository) -> None:
    """Set the global Neo4j repository (called from lifespan startup)."""
    global _neo4j_repository
    _neo4j_repository = repository


def get_neo4j_repository() -> Neo4jRepository:
    """Return the global Neo4j repository (raises if not initialized)."""
    if _neo4j_repository is None:
        raise RuntimeError("Neo4j repository not initialized")
    return _neo4j_repository


def set_review_factory(factory: ReviewServiceFactory) -> None:
    """Set the global ReviewServiceFactory (called from lifespan startup)."""
    global _review_factory
    _review_factory = factory


def get_review_factory() -> ReviewServiceFactory:
    """Return the global ReviewServiceFactory (raises if not initialized)."""
    if _review_factory is None:
        raise RuntimeError("ReviewServiceFactory not initialized")
    return _review_factory


def get_user_store() -> UserStore:
    """Return a user store bound to the configured session factory.

    Built per request so tests can patch ``get_session_factory``; without a
    database the factory raises a 503-mapped ``PersistenceUnavailableError``.
    """
    return PostgresUserStore(get_session_factory())


def get_evidence_store() -> EvidenceQueryStore:
    """Return a read-only evidence query store for the current session factory."""
    return PostgresEvidenceStore(get_session_factory())


def get_feedback_store() -> FeedbackStore:
    """Return a feedback store that owns the patch transaction."""
    return PostgresFeedbackStore(get_session_factory())


def get_audit_store() -> AuditStore:
    """Return a read-only audit store for the current session factory."""
    return PostgresAuditStore(get_session_factory())


def get_literature_store() -> LiteratureStore:
    """Return a literature profile store for the current session factory."""
    return PostgresLiteratureStore(get_session_factory())


def get_annotation_store() -> AnnotationStore:
    """Return an annotation store for the current session factory."""
    return PostgresAnnotationStore(get_session_factory())


def get_run_state_store() -> RunStateStore:
    """Return a run state store for the current session factory."""
    return PostgresRunStateStore(get_session_factory())


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield an async database session.

    Commits on successful handler exit; rolls back on exception.

    Tradeoff: commit runs after the response is sent (FastAPI dependency
    cleanup). If commit fails (e.g. deferred constraint violation), the
    client already received 200 OK but data was rolled back. This is a
    known FastAPI limitation — the alternative (commit inside the handler)
    forces every route to manage transactions explicitly.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
