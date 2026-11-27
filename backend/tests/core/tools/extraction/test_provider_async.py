"""Async tests for the AgentScope-backed structured evidence provider."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import BaseModel

from src.pipeline.skills.extraction.config_context import EvidenceExtractionConfigContext
from src.pipeline.skills.extraction.providers import (
    AgentScopeEvidenceProvider,
    EvidenceModelTier,
)


class _SampleOutput(BaseModel):
    value: str


@pytest.fixture
def provider() -> AgentScopeEvidenceProvider:
    ctx = EvidenceExtractionConfigContext(
        api_key="test-key",
        base_url="http://test",
        reasoning_api_key="test-reasoning-key",
        reasoning_base_url="http://test-reasoning",
        fast_model="fast-model",
        standard_model="std-model",
        strong_model="strong-model",
    )
    return AgentScopeEvidenceProvider(ctx)


@pytest.mark.asyncio
async def test_ainvoke_structured_returns_parsed_model(provider: AgentScopeEvidenceProvider) -> None:
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.ainvoke_model_text",
            new_callable=AsyncMock,
            return_value='{"value": "hello"}',
        ),
    ):
        result = await provider.ainvoke_structured("prompt", _SampleOutput, EvidenceModelTier.FAST, "test")

    assert result == _SampleOutput(value="hello")


@pytest.mark.asyncio
async def test_concurrent_ainvoke_structured_calls(provider: AgentScopeEvidenceProvider) -> None:
    call_log: list[float] = []

    async def _fake(model, content, **kwargs):  # noqa: ANN001
        import time

        call_log.append(time.monotonic())
        await asyncio.sleep(0.05)
        return '{"value": "ok"}'

    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch("src.pipeline.skills.extraction.providers.ainvoke_model_text", side_effect=_fake),
    ):
        results = await asyncio.gather(
            provider.ainvoke_structured("p1", _SampleOutput, EvidenceModelTier.FAST, "s1"),
            provider.ainvoke_structured("p2", _SampleOutput, EvidenceModelTier.FAST, "s2"),
            provider.ainvoke_structured("p3", _SampleOutput, EvidenceModelTier.FAST, "s3"),
        )

    assert [r.value for r in results] == ["ok", "ok", "ok"]
    assert len(call_log) == 3
    assert call_log[2] - call_log[0] < 0.03


@pytest.mark.asyncio
async def test_ainvoke_structured_retries_transient_failures(provider: AgentScopeEvidenceProvider) -> None:
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.ainvoke_model_text",
            new_callable=AsyncMock,
            side_effect=[httpx.ConnectError("down"), '{"value": "ok"}'],
        ) as invoke,
        patch("src.pipeline.skills.extraction.providers.asyncio.sleep", new_callable=AsyncMock),
    ):
        result = await provider.ainvoke_structured("prompt", _SampleOutput, EvidenceModelTier.STRONG, "test")

    assert result == _SampleOutput(value="ok")
    assert invoke.await_count == 2


@pytest.mark.asyncio
async def test_ainvoke_structured_repairs_invalid_json(provider: AgentScopeEvidenceProvider) -> None:
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.ainvoke_model_text",
            new_callable=AsyncMock,
            side_effect=["{not json", '{"value": "repaired"}'],
        ) as invoke,
    ):
        result = await provider.ainvoke_structured("prompt", _SampleOutput, EvidenceModelTier.STANDARD, "test")

    assert result == _SampleOutput(value="repaired")
    assert invoke.await_count == 2


@pytest.mark.asyncio
async def test_ainvoke_structured_propagates_non_transient_errors(provider: AgentScopeEvidenceProvider) -> None:
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.ainvoke_model_text",
            new_callable=AsyncMock,
            side_effect=ValueError("bad input"),
        ),
    ):
        with pytest.raises(ValueError, match="bad input"):
            await provider.ainvoke_structured("prompt", _SampleOutput, EvidenceModelTier.FAST, "test")
