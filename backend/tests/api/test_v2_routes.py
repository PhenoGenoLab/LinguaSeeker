"""The v2 router is mounted and exposes directory runs plus agent jobs."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_v2_routes_registered(async_client):
    response = await async_client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in (
        "/api/v2/runs",
        "/api/v2/runs/{processing_run_id}/status",
        "/api/v2/runs/batches/{batch_id}",
        "/api/v2/agents/acquisition",
        "/api/v2/agents/parsing",
        "/api/v2/agents/fact-chain",
        "/api/v2/agents/standardization",
        "/api/v2/agents/graph-retrieval",
        "/api/v2/agents/review/search",
        "/api/v2/agents/review/feedback",
        "/api/v2/agents/review/chat",
        "/api/v2/agents/jobs/{job_id}",
        "/api/v2/agents/jobs/{job_id}/result",
    ):
        assert path in paths, path
