"""Sync bridge for AgentScope's asynchronous ``Agent.reply``.

AgentScope is async-only; the fact-chain runner is synchronous and already runs
in a worker thread (``asyncio.to_thread``). This module keeps that single bridge
in one place. Agent construction, toolkits and message objects come straight
from AgentScope - nothing is re-implemented here.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from collections.abc import Callable, Coroutine
from typing import TypeVar

from agentscope.agent import Agent
from agentscope.message import Msg, UserMsg
from pydantic import BaseModel

T = TypeVar("T")


def run_coroutine_sync(factory: Callable[[], Coroutine[object, object, T]]) -> T:
    """Run an AgentScope coroutine from synchronous code."""

    def _run() -> T:
        return asyncio.run(factory())

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _run()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_run).result()


def run_reply_sync(agent: Agent, content: str, schema: type[BaseModel]) -> Msg:
    """Return ``agent.reply(..., structured_schema=schema)`` from sync code.

    The runner normally has no running loop, so ``asyncio.run`` is enough.
    When a loop is already active (direct reuse from async callers), the call
    runs in a dedicated thread instead of failing on a nested loop.
    """

    return run_coroutine_sync(
        lambda: agent.reply(
            UserMsg(name="user", content=content),
            structured_schema=schema,
        )
    )


__all__ = ["run_coroutine_sync", "run_reply_sync"]
