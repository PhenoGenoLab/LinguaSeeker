"""Generic AgentScope stage skill for the Phase 3 chain.

One class owns the boilerplate shared by extract/verify/translate: payload
decoding, bounded agent construction, structured reply validation and the
provider-protocol adapter.  Subclasses declare their stage, prompt and reply
schema; only genuinely stage-specific behavior is overridden.
"""

from __future__ import annotations

from collections.abc import Callable
import json
import time
from typing import Any, ClassVar, Protocol

from loguru import logger
from pydantic import BaseModel, ValidationError

from src.pipeline.contracts.skill_io import SkillError, SkillFailureKind, SkillRequest, SkillResult
from src.pipeline.mcp.reme.client import MemoryClient
from src.pipeline.skills.runtime.agent import build_agent, run_reply_sync
from src.pipeline.tools.fact_chain.contracts import ChainContractError, canonical_json
from src.pipeline.tools.fact_chain.core import validate_reply_schema


class StageInvoker(Protocol):
    """The one method the router needs from a stage skill."""

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str: ...


class StageAgentSkill:
    """Bounded stage skill: fixed prompt, optional fixed tools, structured output."""

    stage: ClassVar[str]
    prompt: ClassVar[str]
    schema: ClassVar[type[BaseModel]]
    name: ClassVar[str]
    tier: ClassVar[str] = "fast"

    def __init__(
        self,
        cfg: Any,
        *,
        model: Any | None = None,
        agent_factory: Callable[[dict[str, Any]], Any] | None = None,
        memory: MemoryClient | None = None,
    ) -> None:
        self._cfg = cfg
        self._model = model
        self._agent_factory = agent_factory
        self._memory = memory
        memory_cfg = getattr(getattr(cfg, "pipeline", None), "memory", None)
        self._top_k = max(1, int(getattr(memory_cfg, "top_k", 5) or 5))

    def _tools(self, payload: dict[str, Any]) -> list[Callable[..., str]]:
        return []

    def _system_prompt(self, payload: dict[str, Any]) -> str:
        """Stage prompt; subclasses may append reference-only context."""
        return self.prompt

    def _build_agent(self, payload: dict[str, Any]) -> Any:
        if self._agent_factory is not None:
            return self._agent_factory(payload)
        if self._model is None:
            from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

            self._model = build_chat_model(self._cfg, tier=self.tier)
        return build_agent(
            name=self.name,
            system_prompt=self._system_prompt(payload),
            model=self._model,
            tools=self._tools(payload),
        )

    def call(self, request: SkillRequest) -> SkillResult:
        """Run one stage request and return its validated structured reply."""
        if request.stage != self.stage:
            raise SkillError(f"{self.stage} skill received stage={request.stage}", kind=SkillFailureKind.PERMANENT)
        try:
            payload = json.loads(request.payload)
        except json.JSONDecodeError as exc:
            raise SkillError(f"{self.stage}: payload is not JSON: {exc}", kind=SkillFailureKind.PERMANENT) from exc
        if not isinstance(payload, dict):
            raise SkillError(f"{self.stage}: payload must be an object", kind=SkillFailureKind.PERMANENT)

        started = time.perf_counter()
        try:
            agent = self._build_agent(payload)
            message = run_reply_sync(agent, request.payload, self.schema)
            structured = getattr(message, "structured_output", None)
            if not isinstance(structured, dict):
                raise SkillError(f"{self.stage}: agent returned no structured output")
            reply = self.schema.model_validate(structured)
            data = reply.model_dump()
            validate_reply_schema(data, self.stage)
        except SkillError:
            raise
        except (ValidationError, ValueError, ChainContractError) as exc:
            raise SkillError(f"{self.stage}: schema failure: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - the runner classifies and retries
            raise SkillError(f"{self.stage}: agent failure: {exc}") from exc
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
            window_id=_payload_window(payload),
            prompt=prompt,
            payload=payload,
        )
        result = self.call(request)
        logger.debug(
            "fact chain {} agent ok: model={}, latency_ms={}",
            self.stage,
            model_id,
            result.latency_ms,
        )
        return canonical_json(result.data)


def _payload_window(payload: str) -> str:
    try:
        return str(json.loads(payload).get("window_id", ""))
    except (json.JSONDecodeError, AttributeError):
        return ""


__all__ = ["StageAgentSkill", "StageInvoker"]
