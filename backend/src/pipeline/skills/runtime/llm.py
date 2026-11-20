"""Provider boundary for the source fact chain.

The chain only sees a ``Provider`` protocol, so tests inject local stubs and no
model name or network endpoint is hard-coded in the orchestration. The default
provider reuses the platform LLM pool: extract/translate use the fast tier and
verification uses the reasoning tier (AGENTS.md §23).
"""

from __future__ import annotations

from typing import Any, Protocol

from langchain_core.messages import HumanMessage
from loguru import logger

from src.utils.llm_adapter import LLMPoolAdapter, create_llm_client


class ProviderError(Exception):
    """A provider call failed (transport, refusal, empty content or quota)."""


class Provider(Protocol):
    """Minimal synchronous text-in/text-out model interface."""

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str: ...


class ChatModelProvider:
    """Chat-model provider used by stages that are not yet agent-backed."""

    def __init__(self, cfg: Any):
        self._cfg = cfg
        self._clients: dict[str, LLMPoolAdapter] = {}

    def _client(self, tier: str) -> LLMPoolAdapter:
        if tier in self._clients:
            return self._clients[tier]
        provider = self._cfg.llm if tier == "fast" else self._cfg.reasoning
        model = provider.model or self._cfg.llm.model
        keys = getattr(provider, "all_api_keys", [])
        model_kwargs: dict[str, Any] | None = None
        effort = getattr(provider, "reasoning_effort", "") if tier == "reasoning" else ""
        if effort:
            model_kwargs = {"reasoning_effort": effort}
        self._clients[tier] = create_llm_client(
            model=model,
            base_url=provider.base_url,
            api_keys=keys,
            temperature=0.0,
            max_tokens=getattr(provider, "max_tokens", 8192),
            timeout=getattr(provider, "timeout", 180),
            model_kwargs=model_kwargs,
        )
        return self._clients[tier]

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        tier = "reasoning" if stage == "verify" else "fast"
        messages = [HumanMessage(content=f"{prompt}\n\nINPUT:\n{payload}")]
        try:
            result = self._client(tier).invoke(messages)
        except Exception as exc:  # noqa: BLE001 - provider transport errors are retried upstream
            raise ProviderError(f"{stage}: {exc}") from exc

        content = getattr(result, "content", result)
        if isinstance(content, list):
            content = "".join(str(part.get("text", part)) if isinstance(part, dict) else str(part) for part in content)
        text = str(content or "").strip()
        if not text:
            raise ProviderError(f"{stage}: empty provider reply (model={model_id})")
        logger.debug("source fact chain call ok: stage={}, model={}", stage, model_id)
        return text


__all__ = ["ChatModelProvider", "Provider", "ProviderError"]
