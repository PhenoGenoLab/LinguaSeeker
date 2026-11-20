"""Phase 4 skill: entity standardization and knowledge alignment.

Deterministic delegation in ``legacy`` mode; agent path only under
``shadow``/``agentscope``. The DB session is bound at call time — it is not
serializable, so the agent's single tool closes over it and performs the real
standardization, returning its JSON for the agent to echo back.
"""

from __future__ import annotations

import json
from typing import Any

from src.pipeline.skills.runtime.modes import run_phase_async


class StandardizationSkill:
    """Bounded agent for Phase 4: one tool that standardizes a dual result."""

    name = "phase_4_standardization"
    system_prompt = (
        "You standardize extracted clinical entities against terminology databases.\n"
        "Call the `standardize_entities` tool exactly once, then reply with that tool's JSON\n"
        "output verbatim. Never invent matches."
    )

    def __init__(self, cfg: Any = None, service: Any = None) -> None:
        self._cfg = cfg
        self._service = service

    @property
    def service(self) -> Any:
        if self._service is None:
            from src.core.agents.standardization.api import EntityStandardizationService
            from src.core.config import get_config

            self._service = EntityStandardizationService(cfg=self._cfg or get_config(), graph_rag_service=None)
        return self._service

    async def run_dual_result(
        self,
        session: Any,
        dual_result: Any,
        *,
        source_document_id: str | None = None,
        processing_run_id: str | None = None,
        owner_user_id: str | None = None,
    ) -> Any:
        """Standardize one dual-extraction result, honouring the runtime mode."""
        return await run_phase_async(
            self.name,
            legacy=lambda: self.service.run_dual_result(
                session,
                dual_result,
                source_document_id=source_document_id,
                processing_run_id=processing_run_id,
                owner_user_id=owner_user_id,
            ),
            agent=lambda: self._agent_standardize(
                session=session,
                dual_result=dual_result,
                source_document_id=source_document_id,
                processing_run_id=processing_run_id,
                owner_user_id=owner_user_id,
            ),
        )

    def _result_model(self) -> type:
        from src.core.agents.standardization.contracts import StandardizationResult

        return StandardizationResult

    async def _agent_standardize(
        self,
        *,
        session: Any,
        dual_result: Any,
        source_document_id: str | None,
        processing_run_id: str | None,
        owner_user_id: str | None,
    ) -> Any:
        from agentscope.message import Msg, TextBlock

        from src.pipeline.skills.runtime.agent import build_agent
        from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

        result_model = self._result_model()

        async def standardize_entities(_payload: str) -> str:
            """Run the real standardization for the bound session and return JSON."""
            result = await self.service.run_dual_result(
                session,
                dual_result,
                source_document_id=source_document_id,
                processing_run_id=processing_run_id,
                owner_user_id=owner_user_id,
            )
            return result_model.model_validate(result).model_dump_json()

        agent = build_agent(
            name=self.name,
            system_prompt=self.system_prompt,
            model=build_chat_model(self._cfg, tier="reasoning"),
            tools=[standardize_entities],
        )
        payload = json.dumps(
            {
                "source_document_id": source_document_id,
                "processing_run_id": processing_run_id,
            }
        )
        reply = await agent.reply(Msg(name="user", role="user", content=[TextBlock(text=payload)]))
        text = reply.get_text_content() if hasattr(reply, "get_text_content") else str(reply.content)
        return result_model.model_validate_json(text)


__all__ = ["StandardizationSkill"]
