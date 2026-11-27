"""Tests for the AgentScope-backed structured evidence provider."""

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


class DemoSchema(BaseModel):
    answer: str


def _ctx(**overrides: object) -> EvidenceExtractionConfigContext:
    values: dict[str, object] = {
        "api_key": "key",
        "api_keys": [],
        "base_url": "http://localhost:8001/v1",
        "reasoning_api_key": "reasoning-key",
        "reasoning_api_keys": [],
        "reasoning_base_url": "http://localhost:8001/v1",
        "fast_model": "fast",
        "standard_model": "standard",
        "strong_model": "strong",
        "max_tokens": 8192,
    }
    values.update(overrides)
    return EvidenceExtractionConfigContext(**values)  # type: ignore[arg-type]


def test_strong_tier_routes_to_reasoning_model_and_keys():
    provider = AgentScopeEvidenceProvider(_ctx())
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model") as factory,
        patch("src.pipeline.skills.extraction.providers.invoke_model_text", return_value='{"answer": "ok"}'),
    ):
        result = provider.invoke_structured(
            prompt="Return JSON.",
            output_schema=DemoSchema,
            tier=EvidenceModelTier.STRONG,
            stage="demo",
        )

    assert result.answer == "ok"
    factory.assert_called_once_with(
        model="strong",
        base_url="http://localhost:8001/v1",
        api_keys=["reasoning-key"],
        max_tokens=8192,
        temperature=0.0,
        timeout=180,
        reasoning_effort="high",
    )


def test_fast_tier_routes_to_fast_model_and_keys():
    provider = AgentScopeEvidenceProvider(_ctx())
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model") as factory,
        patch("src.pipeline.skills.extraction.providers.invoke_model_text", return_value='{"answer": "ok"}'),
    ):
        provider.invoke_structured(
            prompt="Return JSON.",
            output_schema=DemoSchema,
            tier=EvidenceModelTier.FAST,
            stage="demo",
        )

    kwargs = factory.call_args.kwargs
    assert kwargs["model"] == "fast"
    assert kwargs["api_keys"] == ["key"]
    assert kwargs["reasoning_effort"] is None


def test_missing_api_keys_fails_fast():
    provider = AgentScopeEvidenceProvider(_ctx(api_keys=[], api_key="", reasoning_api_keys=[], reasoning_api_key=""))
    with pytest.raises(RuntimeError, match="missing LLM API key"):
        provider.invoke_structured(
            prompt="x",
            output_schema=DemoSchema,
            tier=EvidenceModelTier.FAST,
            stage="demo",
        )


def test_structured_output_accepts_fenced_json():
    provider = AgentScopeEvidenceProvider(_ctx())
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch("src.pipeline.skills.extraction.providers.invoke_model_text", return_value='```json\n{"answer": "ok"}\n```'),
    ):
        result = provider.invoke_structured("x", DemoSchema, EvidenceModelTier.FAST, "demo")
    assert result.answer == "ok"


def test_list_schema_is_supported():
    provider = AgentScopeEvidenceProvider(_ctx())
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch("src.pipeline.skills.extraction.providers.invoke_model_text", return_value='[{"answer": "a"}]'),
    ):
        result = provider.invoke_structured("x", list[DemoSchema], EvidenceModelTier.FAST, "demo")  # type: ignore[arg-type]
    assert [item.answer for item in result] == ["a"]


def test_invalid_json_asks_the_model_to_repair_it():
    provider = AgentScopeEvidenceProvider(_ctx())
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.invoke_model_text",
            side_effect=["{not json", '{"answer": "repaired"}'],
        ) as invoke,
    ):
        result = provider.invoke_structured("x", DemoSchema, EvidenceModelTier.FAST, "demo")

    assert result.answer == "repaired"
    assert invoke.call_count == 2


def test_backslash_escapes_are_repaired_without_second_call():
    provider = AgentScopeEvidenceProvider(_ctx())
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.invoke_model_text",
            return_value='{"answer": "C:\\\\Users"}',
        ) as invoke,
    ):
        result = provider.invoke_structured("x", DemoSchema, EvidenceModelTier.FAST, "demo")

    assert result.answer
    assert invoke.call_count == 1


def test_transient_failure_retries_then_succeeds():
    provider = AgentScopeEvidenceProvider(_ctx(max_retries=2))
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.invoke_model_text",
            side_effect=[httpx.ConnectError("down"), '{"answer": "ok"}'],
        ) as invoke,
        patch("src.pipeline.skills.extraction.providers.time.sleep"),
    ):
        result = provider.invoke_structured("x", DemoSchema, EvidenceModelTier.FAST, "demo")

    assert result.answer == "ok"
    assert invoke.call_count == 2


def test_async_structured_output_parses_json():
    provider = AgentScopeEvidenceProvider(_ctx())
    with (
        patch("src.pipeline.skills.extraction.providers.create_chat_model", return_value="model"),
        patch(
            "src.pipeline.skills.extraction.providers.ainvoke_model_text",
            new_callable=AsyncMock,
            return_value='{"answer": "async"}',
        ),
    ):
        result = asyncio.run(provider.ainvoke_structured("x", DemoSchema, EvidenceModelTier.STANDARD, "demo"))

    assert result.answer == "async"
