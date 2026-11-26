"""Phase 4 skill: entity standardization and knowledge alignment.

Same contract as acquisition/parsing: the agent must call the
`standardize_entities` tool, whose real ``StandardizationResult`` is returned
unchanged. Persistence and transaction scope belong to the injected runner.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


class StandardizationSkill:
    """Bounded agent for Phase 4: one tool that standardizes a dual result."""

    name = "standardization"
    system_prompt = (
        "You standardize extracted clinical entities against terminology databases.\n"
        "Call the `standardize_entities` tool exactly once, then reply with a one-line summary."
    )

    def __init__(self, cfg: Any = None, runner: Any = None, agent: Any = None) -> None:
        self._cfg = cfg
        self._runner = runner
        self._agent = agent
        self._tool: Callable[[str], Awaitable[str]] | None = None

    async def run_dual_result(
        self,
        dual_result: Any,
        *,
        source_document_id: str | None = None,
        processing_run_id: str | None = None,
        owner_user_id: str | None = None,
    ) -> Any:
        """Standardize one dual-extraction result through the agent's tool."""
        if self._runner is None:
            raise RuntimeError(f"{self.name}: standardization runner is not configured")
        holder: dict[str, Any] = {}

        async def standardize_entities(payload: str) -> str:
            """Run standardization and return a status string."""
            holder["result"] = await self._runner.run_dual_result(
                dual_result,
                source_document_id=source_document_id,
                processing_run_id=processing_run_id,
                owner_user_id=owner_user_id,
            )
            return "standardized"

        self._tool = standardize_entities
        agent = self._build_agent(standardize_entities)
        from agentscope.message import UserMsg

        for _ in range(2):
            await agent.reply(UserMsg(name="user", content="standardize the entities"))
            if "result" in holder:
                return holder["result"]
            await agent.reply(
                UserMsg(
                    name="user",
                    content="You must call the `standardize_entities` tool now; do not answer in text.",
                )
            )
        raise RuntimeError(f"{self.name}: agent did not call standardize_entities")

    def _build_agent(self, tool: Callable[[str], Awaitable[str]]) -> Any:
        if self._agent is not None:
            return self._agent
        from agentscope.agent import Agent
        from agentscope.permission import PermissionBehavior, PermissionDecision
        from agentscope.tool import FunctionTool, Toolkit
        from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

        return Agent(
            name=self.name,
            system_prompt=self.system_prompt,
            model=build_chat_model(self._cfg, tier="fast"),
            toolkit=Toolkit(
                tools=[
                    FunctionTool(
                        tool,
                        permission=PermissionDecision(
                            behavior=PermissionBehavior.ALLOW,
                            message="standardization tool is always allowed in this pipeline",
                        ),
                    )
                ]
            ),
        )


__all__ = ["StandardizationSkill"]
