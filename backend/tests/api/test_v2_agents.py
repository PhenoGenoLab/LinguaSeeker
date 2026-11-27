"""Tests for v2 agent job routes."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_get_job_returns_literal_agent_name(monkeypatch) -> None:
    """Polling a job must serialize free-form DB agent values as AgentName."""
    from src.api.v2 import agents
    from src.core.foundation.auth.contracts import AuthContext

    class FakeRepository:
        async def get(self, job_id, owner_user_id=None):
            assert owner_user_id is None
            return SimpleNamespace(
                job_id=job_id,
                agent="review",
                status="succeeded",
                created_at=None,
                started_at=None,
                finished_at=None,
                error_message=None,
                error_kind=None,
            )

    monkeypatch.setattr(agents, "_repository", lambda: FakeRepository())
    job_id = uuid4()
    status = await agents.get_job(
        str(job_id),
        account=AuthContext(
            authenticated=True,
            account_type="public",
            user_id=None,
            username=None,
            display_name=None,
            method="api_key",
        ),
    )

    assert status.job_id == str(job_id)
    assert status.agent == "review"
    assert status.status == "succeeded"
