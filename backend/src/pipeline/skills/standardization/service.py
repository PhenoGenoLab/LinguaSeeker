"""Phase 4 skill: entity standardization and knowledge alignment.

Same contract as acquisition/parsing: the agent must call the
`standardize_entities` tool, whose real ``StandardizationResult`` is returned
unchanged. The DB session is bound at call time because it is not serializable;
there is no fallback path.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from src.pipeline.skills.runtime import messages


class StandardizationSkill:
    """Bounded agent for Phase 4: one tool that standardizes a dual result."""

    name = "phase_4_standardization"
    system_prompt = (
        "You standardize extracted clinical entities against terminology databases.\n"
        "Call the `standardize_entities` tool exactly once, then reply with a one-line summary."
    )

    def __init__(self, cfg: Any = None, service: Any = None, agent: Any = None) -> None:
        self._cfg = cfg
        self._service = service
        self._agent = agent
        self._tool: Callable[[str], Awaitable[str]] | None = None

    @property
    def service(self) -> Any:
        if self._service is None:
            from src.pipeline.skills.standardization.api import EntityStandardizationService
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
        """Standardize one dual-extraction result through the agent's tool."""
        holder: dict[str, Any] = {}

        async def standardize_entities(_payload: str) -> str:
            """Run standardization for the bound session and return a status string."""
            holder["result"] = await self.service.run_dual_result(
                session,
                dual_result,
                source_document_id=source_document_id,
                processing_run_id=processing_run_id,
                owner_user_id=owner_user_id,
            )
            return "standardized"

        self._tool = standardize_entities
        agent = self._build_agent(standardize_entities)
        await agent.reply(messages.user_message("standardize the entities"))
        if "result" not in holder:
            raise RuntimeError(f"{self.name}: agent did not call standardize_entities")
        return holder["result"]

    def _build_agent(self, tool: Callable[[str], Awaitable[str]]) -> Any:
        if self._agent is not None:
            return self._agent
        from src.pipeline.skills.runtime.agent import build_agent
        from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

        return build_agent(
            name=self.name,
            system_prompt=self.system_prompt,
            model=build_chat_model(self._cfg, tier="reasoning"),
            tools=[tool],
        )


__all__ = ["StandardizationSkill"]
