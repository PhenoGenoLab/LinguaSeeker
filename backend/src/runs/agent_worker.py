"""Worker for the standalone agent job queue (API v2).

Mirrors the pipeline dispatcher: claim one queued job, execute it through an
injected executor, and record success or failure. One job at a time per worker
process; the DB claim keeps multiple workers safe.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Protocol

from loguru import logger

from src.dao.postgresql.agent_jobs import AgentJobRepository, AgentJobRow


class AgentJobFailure(Exception):
    """A terminal agent failure with a stable classification."""

    def __init__(self, message: str, *, kind: str = "permanent"):
        super().__init__(message)
        self.kind = kind


class AgentExecutor(Protocol):
    """Executes one claimed agent job and returns its result payload."""

    async def execute(self, job: AgentJobRow) -> dict[str, object]: ...


class AgentJobWorker:
    """Background polling loop for ``agent_jobs``."""

    def __init__(
        self,
        repository: AgentJobRepository,
        executor: AgentExecutor,
        *,
        poll_interval: float = 2.0,
        idle_max_interval: float = 30.0,
        worker_id: str | None = None,
    ):
        self._repository = repository
        self._executor = executor
        self._poll_interval = poll_interval
        self._idle_max_interval = idle_max_interval
        self._worker_id = worker_id or f"agent-worker:{uuid.uuid4().hex[:8]}"
        self._task: asyncio.Task | None = None
        self._stopping = False

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stopping = False
        self._task = asyncio.create_task(self._loop())
        logger.info("Agent job worker started (worker_id={})", self._worker_id)

    async def stop(self, timeout: float = 30.0) -> None:
        self._stopping = True
        if self._task is None or self._task.done():
            return
        self._task.cancel()
        try:
            await asyncio.wait_for(self._task, timeout=timeout)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        self._task = None
        logger.info("Agent job worker stopped")

    async def _loop(self) -> None:
        idle_delay = self._poll_interval
        while not self._stopping:
            try:
                job = await self._repository.claim_next(self._worker_id)
                if job is None:
                    await asyncio.sleep(idle_delay)
                    idle_delay = min(idle_delay * 2, self._idle_max_interval)
                    continue
                idle_delay = self._poll_interval
                await self._execute(job)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Agent worker loop error")
                await asyncio.sleep(self._poll_interval)

    async def _execute(self, job: AgentJobRow) -> None:
        logger.info("Executing agent job: job_id={}, agent={}, action={}", job.job_id, job.agent, job.action)
        try:
            result = await self._executor.execute(job)
        except AgentJobFailure as exc:
            await self._repository.fail(job.job_id, str(exc), kind=exc.kind)
            return
        except Exception as exc:  # noqa: BLE001 - record and keep the worker alive
            logger.exception("Agent job failed: job_id={}", job.job_id)
            await self._repository.fail(job.job_id, str(exc), kind="permanent")
            return
        await self._repository.complete(job.job_id, result)
