"""AgentScope runtime helpers shared by pipeline skills.

AgentScope's agent API is asynchronous; the fact chain runner is synchronous
and already executes in a worker thread (``asyncio.to_thread``).  This module
keeps the single event-loop bridge in one place and builds agents from the
configured model tiers.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from agentscope.agent import Agent
from agentscope.message import Msg, TextBlock
from pydantic import BaseModel


def run_reply_sync(agent: Agent, content: str, schema: type[BaseModel]) -> Msg:
    """Return ``agent.reply(..., structured_schema=schema)`` from sync code.

    The runner normally has no running loop, so ``asyncio.run`` is enough.
    When a loop is already active (direct reuse from async callers), the call
    runs in a dedicated thread instead of failing on a nested loop.
    """

    def _reply() -> Msg:
        return asyncio.run(
            agent.reply(
                Msg(name="user", role="user", content=[TextBlock(text=content)]),
                structured_schema=schema,
            )
        )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _reply()
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_reply).result()


def build_agent(
    *,
    name: str,
    system_prompt: str,
    model: Any,
    tools: list[Any] | None = None,
) -> Agent:
    """Build a bounded AgentScope agent: model, prompt and an explicit toolkit.

    Plain callables are wrapped in ``FunctionTool``: AgentScope's toolkit later
    calls ``tool.name``, which a bare function does not expose.
    """
    from agentscope.tool import FunctionTool, Toolkit

    registered = [tool if hasattr(tool, "name") else FunctionTool(tool) for tool in tools or []]
    return Agent(
        name=name,
        system_prompt=system_prompt,
        model=model,
        toolkit=Toolkit(tools=registered),
    )


__all__ = ["build_agent", "run_reply_sync"]
