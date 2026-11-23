"""Phase 3 extract skill: bounded AgentScope agent behind the provider protocol.

The runner still owns retries, budget accounting and stage events.  This module
only turns one extract call into a structured AgentScope reply and, in shadow
mode, compares it with the legacy provider without changing the output.
"""

from __future__ import annotations

from collections.abc import Callable
import json
import time
from typing import Any, Protocol

from loguru import logger
from pydantic import BaseModel, ConfigDict, ValidationError

from src.core.shared.contracts.skill_io import SkillError, SkillFailureKind, SkillRequest, SkillResult
from src.pipeline.skills.extraction.prompts import EXTRACT_PROMPT, EXTRACT_PROMPT_VERSION
from src.pipeline.skills.runtime.llm import Provider
from src.core.shared.tools.fact_chain.contracts import ChainContractError, canonical_json
from src.core.shared.tools.fact_chain.core import is_atomic, locate_quote, validate_reply_schema


class ExtractedFact(BaseModel):
    """One extraction candidate; the schema is the agent's structured output."""

    model_config = ConfigDict(extra="forbid")

    field_id: str
    raw_value: str
    polarity: str
    subject_status: str
    subject_id: str | None
    quote: str


class ExtractReply(BaseModel):
    """Structured reply the extract agent must produce."""

    model_config = ConfigDict(extra="forbid")

    facts: list[ExtractedFact]


def window_tools(window_text: str) -> list[Callable[..., str]]:
    """Deterministic helpers exposed to the extract agent.

    Both functions are plain Python: they are registered as AgentScope tools
    and remain directly callable from tests.
    """

    def quote_in_window(quote: str) -> str:
        """Locate a verbatim quote in the source window."""
        try:
            start, end = locate_quote(window_text, quote)
        except ChainContractError as exc:
            return f"not_found: {exc}"
        return f"found: {start}-{end}"

    def atomic_value(raw_value: str) -> str:
        """Report whether a value is a single atomic value (no semicolon list)."""
        return "atomic" if is_atomic(raw_value) else "contains_semicolon"

    return [quote_in_window, atomic_value]


class ExtractSkill:
    """Bounded extract skill: fixed prompt, fixed tools, structured output."""

    name = "fact_chain_extract"

    def __init__(
        self,
        cfg: Any,
        *,
        tier: str = "fast",
        model: Any | None = None,
        agent_factory: Callable[[str], Any] | None = None,
        memory: Any | None = None,
        top_k: int | None = None,
    ) -> None:
        self._cfg = cfg
        self._tier = tier
        self._model = model
        self._agent_factory = agent_factory
        self._memory = memory
        if top_k is None:
            memory_cfg = getattr(getattr(cfg, "pipeline", None), "memory", None)
            top_k = int(getattr(memory_cfg, "top_k", 5))
        self._top_k = top_k

    def _system_prompt(self, payload: dict[str, Any]) -> str:
        """Append reference-only ReMe recall; failures already degrade to empty."""
        if self._memory is None:
            return EXTRACT_PROMPT
        query = str(payload.get("window_text") or "")[:400]
        block = self._memory.search(query, top_k=self._top_k).as_prompt_block()
        return f"{EXTRACT_PROMPT}\n\n{block}" if block else EXTRACT_PROMPT

    def _build_agent(self, window_text: str) -> Any:
        if self._agent_factory is not None:
            return self._agent_factory(window_text)
        from agentscope.agent import Agent
        from agentscope.tool import FunctionTool, Toolkit

        if self._model is None:
            from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

            self._model = build_chat_model(self._cfg, tier=self._tier)
        tools = [FunctionTool(fn) for fn in window_tools(window_text)]
        return Agent(
            name=self.name,
            system_prompt=self._system_prompt({"window_text": window_text}),
            model=self._model,
            toolkit=Toolkit(tools=tools),
        )

    def call(self, request: SkillRequest) -> SkillResult:
        """Run one extract request and return its validated structured reply."""
        if request.stage != "extract":
            raise SkillError(f"extract skill received stage={request.stage}", kind=SkillFailureKind.PERMANENT)
        try:
            payload = json.loads(request.payload)
        except json.JSONDecodeError as exc:
            raise SkillError(f"extract: payload is not JSON: {exc}", kind=SkillFailureKind.PERMANENT) from exc
        window_text = str(payload.get("window_text") or "")
        if not window_text:
            raise SkillError("extract: payload has no window_text", kind=SkillFailureKind.PERMANENT)

        started = time.perf_counter()
        try:
            from src.pipeline.skills.runtime.agent import run_reply_sync

            agent = self._build_agent(window_text)
            message = run_reply_sync(agent, request.payload, ExtractReply)
            structured = getattr(message, "structured_output", None)
            if not isinstance(structured, dict):
                raise SkillError("extract: agent returned no structured output")
            reply = ExtractReply.model_validate(structured)
            data = reply.model_dump()
            validate_reply_schema(data, "extract")
        except SkillError:
            raise
        except (ValidationError, ValueError, ChainContractError) as exc:
            raise SkillError(f"extract: schema failure: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - the runner classifies and retries
            raise SkillError(f"extract: agent failure: {exc}") from exc
        return SkillResult(
            stage=request.stage,
            data=data,
            latency_ms=round((time.perf_counter() - started) * 1000, 1),
        )

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        """Provider-protocol adapter so the runner needs no agent-specific code."""
        request = SkillRequest(
            stage=stage,
            model_id=model_id,
            window_id=str(_payload_window(payload)),
            prompt=prompt,
            payload=payload,
        )
        result = self.call(request)
        logger.debug(
            "fact chain extract agent ok: model={}, prompt_version={}, latency_ms={}",
            model_id,
            EXTRACT_PROMPT_VERSION,
            result.latency_ms,
        )
        return canonical_json(result.data)


def _payload_window(payload: str) -> str:
    try:
        return str(json.loads(payload).get("window_id", ""))
    except (json.JSONDecodeError, AttributeError):
        return ""








class ExtractInvoker(Protocol):
    """The one method the router needs from an extract skill."""

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str: ...





class ExtractAgentProvider:
    """Route the extract stage to the AgentScope skill; other stages use chat models."""

    def __init__(self, *, chat: Provider, extract: ExtractInvoker) -> None:
        self._chat = chat
        self._extract = extract

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        if stage == "extract":
            return self._extract.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        return self._chat.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)


__all__ = [
    "ExtractAgentProvider",
    "ExtractInvoker",
    "ExtractReply",
    "ExtractSkill",
    "ExtractedFact",
    "window_tools",
]
