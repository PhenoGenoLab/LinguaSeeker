"""In-memory pipeline job queue (process lifetime only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class _QueuedRunJob:
    job_id: UUID
    processing_run_id: UUID
    source_document_id: UUID
    owner_user_id: UUID | None
    request_data: dict[str, object] = field(default_factory=dict)
    status: str = "queued"
    error_message: str | None = None


class InMemoryRunJobQueue:
    """Queue pipeline jobs in insertion order; no cross-worker claiming."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, _QueuedRunJob] = {}

    async def enqueue(
        self,
        *,
        job_id: UUID,
        processing_run_id: UUID,
        source_document_id: UUID,
        request_data: dict[str, object],
        owner_user_id: UUID | None = None,
        priority: int = 0,
    ) -> None:
        del priority
        self._jobs[job_id] = _QueuedRunJob(
            job_id=job_id,
            processing_run_id=processing_run_id,
            source_document_id=source_document_id,
            owner_user_id=owner_user_id,
            request_data=dict(request_data),
        )

    async def claim_next(self, worker_id: str) -> _QueuedRunJob | None:
        del worker_id
        for job in self._jobs.values():
            if job.status == "queued":
                job.status = "running"
                return job
        return None

    async def complete(self, job_id: UUID) -> None:
        if job := self._jobs.get(job_id):
            job.status = "completed"

    async def fail(self, job_id: UUID, error_message: str) -> None:
        if job := self._jobs.get(job_id):
            job.status = "failed"
            job.error_message = error_message

    async def get_status(self, processing_run_id: str, owner_user_id: UUID | None = None) -> str | None:
        for job in self._jobs.values():
            if str(job.processing_run_id) != processing_run_id:
                continue
            if owner_user_id is not None and job.owner_user_id != owner_user_id:
                continue
            return job.status
        return None

    async def get_running_count(self) -> int:
        return sum(1 for job in self._jobs.values() if job.status == "running")

    async def recover_stale_jobs(self) -> int:
        return 0
