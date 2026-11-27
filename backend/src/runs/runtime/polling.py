"""Shared claim-and-execute polling loop for background workers."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from loguru import logger

JobT = TypeVar("JobT")


async def run_polling_loop(
    *,
    claim: Callable[[], Awaitable[JobT | None]],
    handle: Callable[[JobT], Awaitable[None]],
    poll_interval: float,
    idle_max_interval: float,
    loop_name: str,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    """Claim jobs until stopped, backing off exponentially while idle.

    A single job error is logged and does not stop the loop. The loop ends when
    ``should_stop`` reports true or the task is cancelled; callers normally
    stop it by cancelling its task.
    """
    idle_delay = poll_interval
    while should_stop is None or not should_stop():
        try:
            job = await claim()
            if job is None:
                await asyncio.sleep(idle_delay)
                idle_delay = min(idle_delay * 2, idle_max_interval)
                continue
            idle_delay = poll_interval
            await handle(job)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("{} loop error", loop_name)
            await asyncio.sleep(poll_interval)


async def stop_polling_task(task: asyncio.Task[None] | None, *, timeout: float) -> None:
    """Cancel a polling task and wait for it to finish, bounded by *timeout*."""
    if task is None or task.done():
        return
    task.cancel()
    try:
        await asyncio.wait_for(task, timeout=timeout)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
