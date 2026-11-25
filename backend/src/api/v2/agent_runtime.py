"""Runtime wiring for the standalone agent job worker (API v2)."""

from __future__ import annotations

from src.api.deps import get_review_factory
from src.api.v2.executors import AgentExecutor
from src.api.wiring import get_agent_job_store, get_neo4j_repository, get_session_factory
from src.core.config import get_config
from src.runs import AgentJobWorker

_worker: AgentJobWorker | None = None


def get_agent_worker() -> AgentJobWorker:
    """Return the process-wide agent job worker (lazily constructed)."""
    global _worker
    if _worker is None:
        executor = AgentExecutor(
            get_config(),
            session_factory=get_session_factory(),
            neo4j_repository=get_neo4j_repository(),
            review_factory=get_review_factory(),
        )
        _worker = AgentJobWorker(get_agent_job_store(), executor)
    return _worker


def reset_agent_worker() -> None:
    """Drop the cached worker (tests and shutdown)."""
    global _worker
    _worker = None
