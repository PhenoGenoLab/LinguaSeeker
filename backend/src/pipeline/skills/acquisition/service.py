"""Phase 1 skill: document acquisition.

The skill owns *how* the phase asks for a document; ``core.agents.acquisition``
owns the deterministic work. In ``legacy`` mode (the default) the skill simply
delegates, so behaviour is byte-identical to the pre-skill path. The agent path
is only reached when ``pipeline.agent_runtime`` is ``shadow`` or ``agentscope``.
"""

from __future__ import annotations

import json
from typing import Any

from src.pipeline.skills.runtime.modes import run_phase_async


class AcquisitionSkill:
    """Bounded agent for Phase 1: one tool, one request, one result."""

    name = "phase_1_acquisition"
    system_prompt = (
        "You acquire one document for a clinical-genetics pipeline.\n"
        "Call the `acquire_document` tool exactly once with the JSON payload you were given,\n"
        "then reply with that tool's JSON output verbatim. Do not invent fields."
    )

    def __init__(self, cfg: Any = None, service: Any = None) -> None:
        self._cfg = cfg
        self._service = service
        self._agent = None

    # -- deterministic path -------------------------------------------------

    @property
    def service(self) -> Any:
        if self._service is None:
            from src.core.agents.acquisition.service import DocumentAcquisitionService

            self._service = DocumentAcquisitionService()
        return self._service

    async def acquire(self, request: Any) -> Any:
        """Acquire one document, honouring ``pipeline.agent_runtime``."""
        return await run_phase_async(
            self.name,
            legacy=lambda: self.service.acquire(request),
            agent=lambda: self._agent_acquire(request),
        )

    # -- agent path ---------------------------------------------------------

    def _request_model(self) -> type:
        from src.core.agents.acquisition.contracts import DocumentAcquisitionRequest

        return DocumentAcquisitionRequest

    def _result_model(self) -> type:
        from src.core.agents.acquisition.contracts import DocumentAcquisitionResult

        return DocumentAcquisitionResult

    def _build_agent(self) -> Any:
        if self._agent is not None:
            return self._agent
        from src.pipeline.skills.runtime.agent import build_agent
        from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

        request_model = self._request_model()

        async def acquire_document(payload: str) -> str:
            """Acquire a document from the given JSON request and return JSON."""
            request = request_model.model_validate_json(payload)
            result = await self.service.acquire(request)
            return self._result_model().model_validate(result).model_dump_json()

        self._agent = build_agent(
            name=self.name,
            system_prompt=self.system_prompt,
            model=build_chat_model(self._cfg, tier="fast"),
            tools=[acquire_document],
        )
        return self._agent

    async def _agent_acquire(self, request: Any) -> Any:
        from agentscope.message import Msg, TextBlock

        payload = request.model_dump_json() if hasattr(request, "model_dump_json") else json.dumps(request, default=str)
        reply = await self._build_agent().reply(
            Msg(name="user", role="user", content=[TextBlock(text=payload)]),
        )
        text = reply.get_text_content() if hasattr(reply, "get_text_content") else str(reply.content)
        return self._result_model().model_validate_json(text)


__all__ = ["AcquisitionSkill"]
