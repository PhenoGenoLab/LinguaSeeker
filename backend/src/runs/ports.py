"""Ports for the run lifecycle.

These protocols are owned by the code that consumes them. Persistence
adapters implement them, so nothing in ``src.runs`` (or any API route)
needs to know whether a database exists, which driver is used, or how a
transaction is scoped.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.runs.contracts import PipelineGraphState, RunSummary


class RunJob(Protocol):
    """One queued pipeline job as seen by the dispatcher."""

    job_id: UUID | str
    processing_run_id: UUID | str
    source_document_id: UUID | str
    owner_user_id: UUID | str | None
    request_data: dict[str, object]


class AgentJob(Protocol):
    """One queued v2 agent job as seen by the worker and routes."""

    job_id: UUID
    agent: str
    action: str | None
    status: str
    request_data: dict[str, object]
    result: dict[str, object] | None
    error_message: str | None
    error_kind: str | None
    owner_user_id: UUID | None
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None


@dataclass(frozen=True)
class CachedRun:
    """A cached pipeline result and the tier it came from."""

    state: PipelineGraphState
    source: str


class RunStateStore(Protocol):
    """Persist and query pipeline run state."""

    async def save(
        self,
        state: PipelineGraphState,
        *,
        owner_worker_id: str | None = None,
        heartbeat_at: datetime | None = None,
    ) -> None: ...

    async def load(self, processing_run_id: str) -> PipelineGraphState | None: ...

    async def reset_phase_rerun_artifacts(
        self,
        *,
        processing_run_id: str,
        source_document_id: str,
        owner_user_id: str | None = None,
        target_phase: int,
    ) -> None: ...

    async def recover_orphaned_runs(self, *, heartbeat_timeout_seconds: int = 300) -> int: ...

    async def heartbeat(self, processing_run_id: str, owner_worker_id: str) -> bool: ...

    async def has_active_source_key(self, source_key: str, owner_user_id: str | None = None) -> bool: ...

    async def latest_state_for_document(self, source_document_id: str) -> PipelineGraphState | None:
        """Return the newest state for one source document, if any."""
        ...

    async def states_for_batch(self, batch_id: str) -> list[PipelineGraphState]:
        """Return every run state that belongs to one directory batch."""
        ...

    async def list_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
        owner_user_id: str | None = None,
    ) -> tuple[list[RunSummary], int]: ...


class RunJobQueue(Protocol):
    """Queue for pipeline jobs consumed by the dispatcher."""

    async def enqueue(
        self,
        *,
        job_id: UUID,
        processing_run_id: UUID,
        source_document_id: UUID,
        owner_user_id: UUID | None,
        request_data: dict[str, object],
    ) -> None: ...

    async def claim_next(self, worker_id: str) -> RunJob | None: ...

    async def complete(self, job_id: str) -> None: ...

    async def fail(self, job_id: str, error_message: str) -> None: ...

    async def get_status(self, processing_run_id: str, owner_user_id: UUID | None = None) -> str | None: ...

    async def get_running_count(self) -> int: ...

    async def recover_stale_jobs(self) -> int: ...


class AgentJobStore(Protocol):
    """Queue for standalone v2 agent jobs."""

    async def enqueue(
        self,
        *,
        job_id: UUID,
        agent: str,
        action: str | None,
        request_data: dict[str, object],
        owner_user_id: UUID | None = None,
    ) -> None: ...

    async def claim_next(self, worker_id: str) -> AgentJob | None: ...

    async def complete(self, job_id: UUID, result: dict[str, object]) -> None: ...

    async def fail(self, job_id: UUID, error_message: str, *, kind: str = "permanent") -> None: ...

    async def get(self, job_id: UUID, *, owner_user_id: UUID | None = None) -> AgentJob | None: ...


class ProcessingCache(Protocol):
    """Content-hash cache for completed pipeline results."""

    async def get_cached_result(self, content_hash: str) -> CachedRun | None: ...

    async def cache_result(self, content_hash: str, state: PipelineGraphState) -> None: ...
