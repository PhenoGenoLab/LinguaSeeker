"""Runtime mode routing for pipeline skills.

These tests pin the three ``pipeline.agent_runtime`` modes: ``legacy`` must not
touch the agent at all, ``shadow`` must return the legacy result and record a
diff row, and ``agentscope`` must return the agent result. The shadow row is the
gate for ever flipping a phase, so its "not equal" branch is tested too.
"""

from __future__ import annotations

import json

import pytest

from src.pipeline.skills.runtime import modes


@pytest.fixture()
def report(tmp_path, monkeypatch):
    path = tmp_path / "shadow_report.json"
    monkeypatch.setenv("PIPELINE_SHADOW_REPORT", str(path))
    return path


def _force_mode(monkeypatch, mode: str) -> None:
    monkeypatch.setattr(modes, "agent_mode", lambda: mode)


def test_legacy_never_calls_the_agent(monkeypatch, report):
    _force_mode(monkeypatch, "legacy")
    called = {"agent": False}

    def agent():
        called["agent"] = True
        return {"value": 2}

    result = modes.run_phase_sync("phase_x", legacy=lambda: {"value": 1}, agent=agent)

    assert result == {"value": 1}
    assert called["agent"] is False
    assert not report.exists()


def test_shadow_returns_legacy_and_records_equal_row(monkeypatch, report):
    _force_mode(monkeypatch, "shadow")

    result = modes.run_phase_sync("phase_x", legacy=lambda: {"value": 1}, agent=lambda: {"value": 1})

    assert result == {"value": 1}
    rows = json.loads(report.read_text(encoding="utf-8"))["rows"]
    assert len(rows) == 1
    assert rows[0]["phase"] == "phase_x"
    assert rows[0]["equal"] is True
    assert rows[0]["legacy_hash"] == rows[0]["agent_hash"]


def test_shadow_records_inequality_when_agent_drifts(monkeypatch, report):
    _force_mode(monkeypatch, "shadow")

    result = modes.run_phase_sync("phase_x", legacy=lambda: {"value": 1}, agent=lambda: {"value": 2})

    assert result == {"value": 1}
    row = json.loads(report.read_text(encoding="utf-8"))["rows"][0]
    assert row["equal"] is False
    assert row["legacy_hash"] != row["agent_hash"]


def test_shadow_swallows_agent_failure_but_records_it(monkeypatch, report):
    _force_mode(monkeypatch, "shadow")

    def boom():
        raise ValueError("agent exploded")

    result = modes.run_phase_sync("phase_x", legacy=lambda: 7, agent=boom)

    assert result == 7
    row = json.loads(report.read_text(encoding="utf-8"))["rows"][0]
    assert row["equal"] is False
    assert row["agent_hash"] is None
    assert "agent exploded" in row["agent_error"]


def test_agentscope_returns_agent_result(monkeypatch, report):
    _force_mode(monkeypatch, "agentscope")

    assert modes.run_phase_sync("phase_x", legacy=lambda: 1, agent=lambda: 2) == 2


def test_agentscope_surfaces_agent_failure(monkeypatch, report):
    _force_mode(monkeypatch, "agentscope")

    def boom():
        raise ValueError("agent exploded")

    with pytest.raises(RuntimeError, match="phase_x"):
        modes.run_phase_sync("phase_x", legacy=lambda: 1, agent=boom)


@pytest.mark.asyncio
async def test_async_shadow_returns_legacy_and_records(monkeypatch, report):
    _force_mode(monkeypatch, "shadow")

    async def legacy():
        return {"value": 1}

    async def agent():
        return {"value": 2}

    assert await modes.run_phase_async("phase_x", legacy=legacy, agent=agent) == {"value": 1}
    assert json.loads(report.read_text(encoding="utf-8"))["rows"][0]["equal"] is False


def test_skill_facade_uses_legacy_mode_by_default(monkeypatch, report):
    """The shipped default must be ``legacy`` so the skill is a no-op wrapper."""
    from src.pipeline.skills.acquisition.service import AcquisitionSkill

    seen = {}

    class StubService:
        async def acquire(self, request):
            seen["request"] = request
            return {"ok": True}

    skill = AcquisitionSkill(cfg=None, service=StubService())

    class StubRequest:
        def model_dump_json(self):
            return "{}"

    import asyncio

    assert asyncio.run(skill.acquire(StubRequest())) == {"ok": True}
    assert seen["request"] is not None
