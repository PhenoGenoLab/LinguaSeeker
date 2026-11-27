"""AgentScope model construction for pipeline skills.

Imported only when a skill builds its agent, so importing a skill module in a
test that injects a fake agent never loads AgentScope.
"""

from __future__ import annotations

from typing import Any

import openai
from loguru import logger
from agentscope.credential import OpenAICredential
from agentscope.model import ChatModelBase, OpenAIChatModel


class RotatingOpenAIChatModel(OpenAIChatModel):
    """OpenAI chat model that rotates API keys after an auth failure.

    ``OpenAIChatModel`` caches its client from the credential passed at
    construction, so rotation rebuilds the client.  Only authentication and
    permission errors trigger a rotation; transport and rate-limit failures
    keep the current key and are retried by the stage runner, exactly like the
    legacy provider.
    """

    def __init__(self, *, credentials: list[OpenAICredential], model: str, **kwargs: Any) -> None:
        if not credentials:
            raise ValueError("RotatingOpenAIChatModel needs at least one credential")
        super().__init__(credential=credentials[0], model=model, **kwargs)
        self._credentials = tuple(credentials)
        self._credential_index = 0

    def _use_credential(self, index: int) -> None:
        self._credential_index = index % len(self._credentials)
        credential = self._credentials[self._credential_index]
        self.credential = credential
        self.client = openai.AsyncClient(
            api_key=credential.api_key.get_secret_value(),
            organization=credential.organization,
            base_url=credential.base_url,
            **self.client_kwargs,
        )

    async def _call_api(
        self,
        model_name: str,
        messages: list[Any],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: Any = None,
        **generate_kwargs: Any,
    ) -> Any:
        last_error: Exception | None = None
        for _ in range(len(self._credentials)):
            try:
                return await super()._call_api(
                    model_name=model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice=tool_choice,
                    **generate_kwargs,
                )
            except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
                last_error = exc
                logger.warning("agent runtime: rotating API key after {}", type(exc).__name__)
                self._use_credential(self._credential_index + 1)
        assert last_error is not None  # noqa: S101 - the loop always runs at least once
        raise last_error


def create_chat_model(
    *,
    model: str,
    base_url: str,
    api_keys: list[str],
    temperature: float = 0.0,
    max_tokens: int = 8192,
    timeout: float = 180,
    reasoning_effort: str | None = None,
    max_retries: int = 0,
) -> ChatModelBase:
    """Build an AgentScope chat model from explicit connection settings."""
    keys = [key.strip() for key in api_keys if key and key.strip()]
    if not keys:
        raise ValueError("agent runtime: no API key configured")
    parameters = OpenAIChatModel.Parameters(
        max_tokens=max_tokens,
        temperature=temperature,
        reasoning_effort=reasoning_effort or None,
    )
    credentials = [OpenAICredential(api_key=key, base_url=base_url) for key in keys]
    return RotatingOpenAIChatModel(
        credentials=credentials,
        model=model,
        parameters=parameters,
        stream=False,
        max_retries=max_retries,
        client_kwargs={"timeout": timeout},
    )


def build_chat_model(cfg: Any, *, tier: str = "fast") -> ChatModelBase:
    """Build an AgentScope chat model for one tier (fast or reasoning)."""
    provider = cfg.llm if tier == "fast" else cfg.reasoning
    return create_chat_model(
        model=provider.model or cfg.llm.model,
        base_url=provider.base_url,
        api_keys=list(getattr(provider, "all_api_keys", [])),
        temperature=0.0,
        max_tokens=getattr(provider, "max_tokens", 8192),
        timeout=getattr(provider, "timeout", 180),
        reasoning_effort=getattr(provider, "reasoning_effort", None) or None,
        max_retries=getattr(provider, "max_retries", 0),
    )


__all__ = ["RotatingOpenAIChatModel", "build_chat_model", "create_chat_model"]
