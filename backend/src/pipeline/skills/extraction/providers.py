"""Structured evidence extraction over AgentScope chat models.

The provider only knows two tiers (fast/standard/strong), asks for JSON that
matches the requested schema, and validates it locally. Retries cover transient
transport errors; strict-schema modes are not used, so there is no
provider-specific ``response_format`` fallback tree to maintain.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from enum import Enum
from typing import Any, TypeVar

import httpx
import openai
from loguru import logger
from pydantic import TypeAdapter, ValidationError

from agentscope.model import ChatModelBase

from src.pipeline.skills.extraction.config_context import EvidenceExtractionConfigContext
from src.pipeline.skills.runtime.agentscope_llm import create_chat_model
from src.pipeline.skills.runtime.llm import ainvoke_model_text, invoke_model_text
from src.utils.text import strip_json_fences

SchemaT = TypeVar("SchemaT")


class EvidenceModelTier(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    STRONG = "strong"


class AgentScopeEvidenceProvider:
    """JSON-schema extraction provider backed by AgentScope chat models."""

    _TRANSIENT_EXCEPTIONS = (
        openai.APITimeoutError,
        openai.APIConnectionError,
        openai.RateLimitError,
        openai.InternalServerError,
        httpx.TimeoutException,
        httpx.ConnectError,
    )

    def __init__(self, ctx: EvidenceExtractionConfigContext):
        self._ctx = ctx
        self._models: dict[EvidenceModelTier, ChatModelBase] = {}

    def _model_for_tier(self, tier: EvidenceModelTier) -> str:
        if tier == EvidenceModelTier.FAST:
            return self._ctx.fast_model
        if tier == EvidenceModelTier.STANDARD:
            return self._ctx.standard_model
        return self._ctx.strong_model

    def _effort_for_tier(self, tier: EvidenceModelTier) -> str:
        if tier == EvidenceModelTier.FAST:
            return self._ctx.fast_effort
        if tier == EvidenceModelTier.STANDARD:
            return self._ctx.standard_effort
        return self._ctx.strong_effort

    def _api_keys_for_tier(self, tier: EvidenceModelTier) -> list[str]:
        if tier == EvidenceModelTier.FAST:
            keys = [*self._ctx.api_keys, self._ctx.api_key]
        else:
            keys = [*self._ctx.reasoning_api_keys, self._ctx.reasoning_api_key]
        return [key.strip() for key in keys if key and key.strip()]

    def _client_for_tier(self, tier: EvidenceModelTier) -> ChatModelBase:
        if tier not in self._models:
            base_url = self._ctx.base_url if tier == EvidenceModelTier.FAST else self._ctx.reasoning_base_url
            api_keys = self._api_keys_for_tier(tier)
            if not api_keys:
                raise RuntimeError(f"missing LLM API key for evidence extraction tier {tier.value}")
            self._models[tier] = create_chat_model(
                model=self._model_for_tier(tier),
                base_url=base_url,
                api_keys=api_keys,
                max_tokens=self._ctx.max_tokens,
                temperature=self._ctx.temperature,
                timeout=self._ctx.timeout,
                reasoning_effort=self._effort_for_tier(tier) or None,
            )
        return self._models[tier]

    # ── structured invocation ────────────────────────────────────────────

    def invoke_structured(
        self,
        prompt: str,
        output_schema: type[SchemaT],
        tier: EvidenceModelTier,
        stage: str,
    ) -> SchemaT:
        model = self._client_for_tier(tier)
        adapter = TypeAdapter(output_schema)
        schema = adapter.json_schema()
        json_prompt = _json_prompt(prompt, schema)
        last_exc: Exception | None = None
        for attempt in range(1, self._ctx.max_retries + 1):
            try:
                text = invoke_model_text(model, json_prompt)
                return self._parse(adapter, text, model, schema, stage)
            except self._TRANSIENT_EXCEPTIONS as exc:
                last_exc = exc
                logger.warning("Stage {} transient failure {}/{}: {}", stage, attempt, self._ctx.max_retries, exc)
                if attempt < self._ctx.max_retries:
                    time.sleep(2**attempt)
        raise RuntimeError(f"Stage {stage} failed structured output") from last_exc

    async def ainvoke_structured(
        self,
        prompt: str,
        output_schema: type[SchemaT],
        tier: EvidenceModelTier,
        stage: str,
    ) -> SchemaT:
        model = self._client_for_tier(tier)
        adapter = TypeAdapter(output_schema)
        schema = adapter.json_schema()
        json_prompt = _json_prompt(prompt, schema)
        last_exc: Exception | None = None
        for attempt in range(1, self._ctx.max_retries + 1):
            try:
                text = await ainvoke_model_text(model, json_prompt)
                return await self._aparse(adapter, text, model, schema, stage)
            except self._TRANSIENT_EXCEPTIONS as exc:
                last_exc = exc
                logger.warning("Stage {} transient failure {}/{}: {}", stage, attempt, self._ctx.max_retries, exc)
                if attempt < self._ctx.max_retries:
                    await asyncio.sleep(2**attempt)
        raise RuntimeError(f"Stage {stage} failed structured output") from last_exc

    # ── parsing and repair ───────────────────────────────────────────────

    def _parse(
        self,
        adapter: TypeAdapter,
        text: str,
        model: ChatModelBase,
        schema: dict[str, Any],
        stage: str,
    ) -> Any:
        json_text = strip_json_fences(text)
        try:
            return adapter.validate_python(json.loads(json_text))
        except (ValidationError, ValueError, json.JSONDecodeError):
            try:
                repaired_candidate = re.sub(r"\\(?![\"\\/bfnrtu])", r"\\\\", json_text)
                return adapter.validate_python(json.loads(repaired_candidate))
            except Exception:
                logger.warning("Stage {} JSON invalid, asking the model to repair it", stage)
                repaired = strip_json_fences(invoke_model_text(model, _repair_prompt(json_text, schema)))
                return adapter.validate_python(json.loads(repaired))

    async def _aparse(
        self,
        adapter: TypeAdapter,
        text: str,
        model: ChatModelBase,
        schema: dict[str, Any],
        stage: str,
    ) -> Any:
        json_text = strip_json_fences(text)
        try:
            return adapter.validate_python(json.loads(json_text))
        except (ValidationError, ValueError, json.JSONDecodeError):
            try:
                repaired_candidate = re.sub(r"\\(?![\"\\/bfnrtu])", r"\\\\", json_text)
                return adapter.validate_python(json.loads(repaired_candidate))
            except Exception:
                logger.warning("Stage {} JSON invalid, asking the model to repair it", stage)
                repaired = strip_json_fences(await ainvoke_model_text(model, _repair_prompt(json_text, schema)))
                return adapter.validate_python(json.loads(repaired))


def _json_prompt(prompt: str, schema: dict[str, Any]) -> str:
    return (
        f"{prompt}\n\n"
        "Return only valid JSON matching this JSON Schema. Do not wrap it in Markdown code fences.\n"
        f"{json.dumps(schema, ensure_ascii=False)}"
    )


def _repair_prompt(invalid_json: str, schema: dict[str, Any]) -> str:
    return (
        "Repair the following invalid JSON so it exactly matches the JSON Schema. "
        "Return only valid JSON. Do not add Markdown fences or explanation.\n\n"
        f"JSON Schema:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
        f"Invalid JSON:\n{invalid_json}"
    )


__all__ = ["AgentScopeEvidenceProvider", "EvidenceModelTier"]
