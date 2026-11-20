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
from src.pipeline.skills.runtime.agent import build_agent, run_reply_sync
from src.pipeline.skills.runtime.llm import Provider, ProviderError
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
    ) -> None:
        self._cfg = cfg
        self._tier = tier
        self._model = model
        self._agent_factory = agent_factory

    def _build_agent(self, window_text: str) -> Any:
        if self._agent_factory is not None:
            return self._agent_factory(window_text)
        if self._model is None:
            from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

            self._model = build_chat_model(self._cfg, tier=self._tier)
        return build_agent(
            name=self.name,
            system_prompt=EXTRACT_PROMPT,
            model=self._model,
            tools=window_tools(window_text),
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


class ShadowStats(BaseModel):
    """Counters for one shadow-mode router."""

    calls: int = 0
    mismatches: int = 0
    agent_failures: int = 0


def compare_extract_replies(legacy_text: str, agent_text: str) -> list[str]:
    """Return human-readable differences between two extract replies."""
    try:
        legacy = json.loads(legacy_text).get("facts")
        agent = json.loads(agent_text).get("facts")
    except (json.JSONDecodeError, AttributeError) as exc:
        return [f"unparsable reply: {exc}"]
    if not isinstance(legacy, list) or not isinstance(agent, list):
        return ["facts must be a list"]
    left = sorted(canonical_json(item) for item in legacy)
    right = sorted(canonical_json(item) for item in agent)
    if left == right:
        return []
    differences = [f"fact count legacy={len(left)} agent={len(right)}"]
    only_legacy = [item for item in left if item not in right]
    only_agent = [item for item in right if item not in left]
    differences.extend(f"legacy_only: {item}" for item in only_legacy)
    differences.extend(f"agent_only: {item}" for item in only_agent)
    return differences


class ExtractInvoker(Protocol):
    """The one method the router needs from an extract skill."""

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str: ...


class StageRouterProvider:
    """Route extract to AgentScope; keep verify/translate on the legacy provider.

    ``shadow`` calls both paths and returns the legacy reply, so production
    output stays byte-identical while differences are logged.  ``agentscope``
    returns the agent reply for extract only.
    """

    def __init__(self, *, legacy: Provider, extract: ExtractInvoker, mode: str) -> None:
        if mode not in {"shadow", "agentscope"}:
            raise ValueError(f"unsupported agent runtime mode: {mode}")
        self._legacy = legacy
        self._extract = extract
        self._mode = mode
        self._stats = ShadowStats()

    @property
    def stats(self) -> ShadowStats:
        return self._stats

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        if stage != "extract":
            return self._legacy.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        if self._mode == "agentscope":
            return self._extract.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        legacy_text = self._legacy.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        self._stats.calls += 1
        try:
            agent_text = self._extract.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        except (ProviderError, SkillError) as exc:
            self._stats.agent_failures += 1
            logger.warning("extract shadow agent failed, legacy reply kept: {}", exc)
            return legacy_text
        differences = compare_extract_replies(legacy_text, agent_text)
        if differences:
            self._stats.mismatches += 1
            logger.warning("extract shadow diff ({}): {}", model_id, "; ".join(differences))
        else:
            logger.info("extract shadow match: model={}, window={}", model_id, _payload_window(payload))
        return legacy_text


__all__ = [
    "ExtractInvoker",
    "ExtractReply",
    "ExtractSkill",
    "ExtractedFact",
    "ShadowStats",
    "StageRouterProvider",
    "compare_extract_replies",
    "window_tools",
]
