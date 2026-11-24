"""Persistence for the standalone agent job queue (API v2)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.dao.postgresql.models import AgentJob


@dataclass(frozen=True)
class AgentJobRow:
    """Detached snapshot of one agent job."""

    job_id: uuid.UUID
    agent: str
    action: str | None
    status: str
    request_data: dict[str, object]
    result: dict[str, object] | None
    error_message: str | None
    error_kind: str | None
    owner_user_id: uuid.UUID | None
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None


def _row(job: AgentJob) -> AgentJobRow:
    return AgentJobRow(
        job_id=job.job_id,
        agent=job.agent,
        action=job.action,
        status=job.status,
        request_data=dict(job.request_data or {}),
        result=dict(job.result) if job.result is not None else None,
        error_message=job.error_message,
        error_kind=job.error_kind,
        owner_user_id=job.owner_user_id,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


class AgentJobRepository:
    """Queue operations for agent jobs (claim is atomic across workers)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def enqueue(
        self,
        *,
        job_id: uuid.UUID,
        agent: str,
        action: str | None,
        request_data: dict[str, object],
        owner_user_id: uuid.UUID | None,
    ) -> None:
        async with self._session_factory() as session:
            session.add(
                AgentJob(
                    job_id=job_id,
                    agent=agent,
                    action=action,
                    status="queued",
                    request_data=request_data,
                    owner_user_id=owner_user_id,
                )
            )
            await session.commit()

    async def claim_next(self, worker_id: str) -> AgentJobRow | None:
        """Claim the oldest queued job, or return None."""
        async with self._session_factory() as session:
            stmt = (
                select(AgentJob)
                .where(AgentJob.status == "queued")
                .order_by(AgentJob.created_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            job = (await session.execute(stmt)).scalar_one_or_none()
            if job is None:
                return None
            job.status = "running"
            job.started_at = datetime.now().astimezone()
            job.worker_id = worker_id
            await session.commit()
            return _row(job)

    async def complete(self, job_id: uuid.UUID, result: dict[str, object]) -> None:
        async with self._session_factory() as session:
            job = await session.get(AgentJob, job_id)
            if job is None:
                return
            job.status = "succeeded"
            job.result = result
            job.finished_at = datetime.now().astimezone()
            await session.commit()

    async def fail(self, job_id: uuid.UUID, message: str, *, kind: str = "permanent") -> None:
        async with self._session_factory() as session:
            job = await session.get(AgentJob, job_id)
            if job is None:
                return
            job.status = "failed"
            job.error_message = message
            job.error_kind = kind
            job.finished_at = datetime.now().astimezone()
            await session.commit()

    async def get(self, job_id: uuid.UUID, *, owner_user_id: uuid.UUID | None = None) -> AgentJobRow | None:
        async with self._session_factory() as session:
            job = await session.get(AgentJob, job_id)
            if job is None:
                return None
            if owner_user_id is not None and job.owner_user_id not in (None, owner_user_id):
                return None
            return _row(job)
