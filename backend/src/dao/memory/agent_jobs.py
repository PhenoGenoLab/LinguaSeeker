"""In-memory agent job queue (process lifetime only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class _AgentJob:
    job_id: UUID
    agent: str
    action: str | None
    request_data: dict[str, object] = field(default_factory=dict)
    status: str = "queued"
    result: dict[str, object] | None = None
    error_message: str | None = None
    error_kind: str | None = None
    owner_user_id: UUID | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class InMemoryAgentJobStore:
    """Queue v2 agent jobs in insertion order; no cross-worker claiming."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, _AgentJob] = {}

    async def enqueue(
        self,
        *,
        job_id: UUID,
        agent: str,
        action: str | None,
        request_data: dict[str, object],
        owner_user_id: UUID | None = None,
    ) -> None:
        self._jobs[job_id] = _AgentJob(
            job_id=job_id,
            agent=agent,
            action=action,
            request_data=dict(request_data),
            owner_user_id=owner_user_id,
            created_at=datetime.now(),
        )

    async def claim_next(self, worker_id: str) -> _AgentJob | None:
        del worker_id
        for job in self._jobs.values():
            if job.status == "queued":
                job.status = "running"
                job.started_at = datetime.now()
                return job
        return None

    async def complete(self, job_id: UUID, result: dict[str, object]) -> None:
        if job := self._jobs.get(job_id):
            job.status = "succeeded"
            job.result = result
            job.finished_at = datetime.now()

    async def fail(self, job_id: UUID, error_message: str, *, kind: str = "permanent") -> None:
        if job := self._jobs.get(job_id):
            job.status = "failed"
            job.error_message = error_message
            job.error_kind = kind
            job.finished_at = datetime.now()

    async def get(self, job_id: UUID, *, owner_user_id: UUID | None = None) -> _AgentJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if owner_user_id is not None and job.owner_user_id not in (None, owner_user_id):
            return None
        return job
