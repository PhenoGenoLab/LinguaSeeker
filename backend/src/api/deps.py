"""API dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.runs.review_factory import ReviewServiceFactory
from src.api.wiring import get_session_factory
from src.dao.neo4j.repository import Neo4jRepository

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
