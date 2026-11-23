"""Single-path skills: the agent is the only path, failures propagate.

There is no legacy fallback any more. The agent must call the skill's tool; the
tool's real result object is what the skill returns (no JSON round-trip, so
dataclass fields and enums survive). An agent that raises, or one that never
calls the tool, fails the phase.
"""

from __future__ import annotations

import asyncio

import pytest

from src.pipeline.skills.acquisition.service import AcquisitionSkill


class _Agent:
    """Test double: optionally invokes the skill's tool, like the real agent would."""

    def __init__(self, *, skill: AcquisitionSkill | None = None, call_tool: bool = True, error: Exception | None = None):
        self._skill = skill
        self._call_tool = call_tool
        self._error = error
        self.calls = 0

    async def reply(self, _message: object) -> None:
        self.calls += 1
        if self._error is not None:
            raise self._error
        if self._call_tool:
            assert self._skill is not None and self._skill._tool is not None
            await self._skill._tool("")


class _Service:
    def __init__(self) -> None:
        self.requests: list[object] = []

    async def acquire(self, request: object) -> object:
        self.requests.append(request)
        return {"acquired": True}


def test_tool_result_is_returned_and_agent_runs_once() -> None:
    service = _Service()
    skill = AcquisitionSkill(cfg=None, service=service)
    agent = _Agent(skill=skill)
    skill._agent = agent

    result = asyncio.run(skill.acquire(object()))

    assert result == {"acquired": True}
    assert agent.calls == 1
    assert len(service.requests) == 1


def test_agent_failure_propagates() -> None:
    skill = AcquisitionSkill(cfg=None, service=_Service())
    skill._agent = _Agent(skill=skill, error=RuntimeError("provider down"))

    with pytest.raises(RuntimeError, match="provider down"):
        asyncio.run(skill.acquire(object()))


def test_agent_that_never_calls_the_tool_fails_the_phase() -> None:
    skill = AcquisitionSkill(cfg=None, service=_Service())
    skill._agent = _Agent(skill=skill, call_tool=False)

    with pytest.raises(RuntimeError, match="did not call acquire_document"):
        asyncio.run(skill.acquire(object()))
