"""Provider boundary for the source fact chain.

The chain only sees a ``Provider`` protocol, so tests inject local stubs and no
model name or network endpoint is hard-coded in the orchestration. The default
provider reuses the platform LLM pool: extract/translate use the fast tier and
verification uses the reasoning tier (AGENTS.md §23).
"""

from __future__ import annotations

from typing import Any, Protocol

from loguru import logger

from src.pipeline.skills.runtime.agent import run_coroutine_sync


class ProviderError(Exception):
    """A provider call failed (transport, refusal, empty content or quota)."""


class Provider(Protocol):
    """Minimal synchronous text-in/text-out model interface."""

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str: ...


async def ainvoke_model_text(model: Any, content: str, **kwargs: Any) -> str:
    """Call an AgentScope chat model and return its text blocks joined."""
    from agentscope.message import TextBlock, UserMsg

    response = await model([UserMsg(name="user", content=content)], **kwargs)
    blocks = getattr(response, "content", None) or []
    text = "".join(block.text for block in blocks if isinstance(block, TextBlock)).strip()
    if not text:
        raise ProviderError("empty model reply")
    return text


def invoke_model_text(model: Any, content: str, **kwargs: Any) -> str:
    """Synchronous wrapper around :func:`ainvoke_model_text`."""
    return run_coroutine_sync(lambda: ainvoke_model_text(model, content, **kwargs))


class ChatModelProvider:
    """AgentScope chat model used by stages that are not agent-backed."""

    def __init__(self, cfg: Any):
        self._cfg = cfg
        self._models: dict[str, Any] = {}

    def _model(self, tier: str) -> Any:
        if tier not in self._models:
            from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

            self._models[tier] = build_chat_model(self._cfg, tier=tier)
        return self._models[tier]

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        from agentscope.message import TextBlock, UserMsg

        tier = "reasoning" if stage == "verify" else "fast"
        message = UserMsg(name="user", content=f"{prompt}\n\nINPUT:\n{payload}")
        try:
            response = run_coroutine_sync(lambda: self._model(tier)([message]))
        except Exception as exc:  # noqa: BLE001 - provider transport errors are retried upstream
            raise ProviderError(f"{stage}: {exc}") from exc

        blocks = getattr(response, "content", None) or []
        text = "".join(block.text for block in blocks if isinstance(block, TextBlock)).strip()
        if not text:
            raise ProviderError(f"{stage}: empty provider reply (model={model_id})")
        logger.debug("source fact chain call ok: stage={}, model={}", stage, model_id)
        return text


__all__ = ["ChatModelProvider", "Provider", "ProviderError", "ainvoke_model_text", "invoke_model_text"]
