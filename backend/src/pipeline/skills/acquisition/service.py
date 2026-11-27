"""Phase 1 skill: document acquisition.

The agent is the preferred path: it should call the `acquire_document` tool,
whose result is the real ``DocumentAcquisitionResult`` (no JSON round-trip, so
dataclass fields, enums and nested entries survive intact). If the agent does
not call the tool after retries, the bound tool is invoked directly; a tool
that raises still fails the phase.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger



class AcquisitionSkill:
    """Bounded agent for Phase 1: one tool, one request, one result."""

    name = "acquisition"
    system_prompt = (
        "You acquire one document for a clinical-genetics pipeline.\n"
        "Call the `acquire_document` tool exactly once, then reply with a one-line summary."
    )

    def __init__(self, cfg: Any = None, service: Any = None, agent: Any = None) -> None:
        self._cfg = cfg
        self._service = service
        self._agent = agent
        self._tool: Callable[[str], Awaitable[str]] | None = None

    @property
    def service(self) -> Any:
        if self._service is None:
            from src.core.tools.acquisition.service import DocumentAcquisitionService

            self._service = DocumentAcquisitionService()
        return self._service

    async def acquire(self, request: Any) -> Any:
        """Acquire one document through the agent's single tool."""
        holder: dict[str, Any] = {}

        async def acquire_document(payload: str) -> str:
            """Acquire the bound request and return a short status string."""
            holder["result"] = await self.service.acquire(request)
            return "acquired"

        self._tool = acquire_document
        agent = self._build_agent(acquire_document)
        from agentscope.message import UserMsg

        for _ in range(2):
            await agent.reply(UserMsg(name="user", content="acquire the document"))
            if "result" in holder:
                return holder["result"]
            await agent.reply(
                UserMsg(
                    name="user",
                    content="You must call the `acquire_document` tool now; do not answer in text.",
                )
            )
        logger.warning("acquisition: agent did not call acquire_document; invoking bound tool directly")
        await acquire_document("acquire")
        return holder["result"]

    def _build_agent(self, tool: Callable[[str], Awaitable[str]]) -> Any:
        if self._agent is not None:
            return self._agent
        from agentscope.agent import Agent, ModelConfig
        from agentscope.permission import PermissionBehavior, PermissionDecision
        from agentscope.tool import FunctionTool, Toolkit
        from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

        return Agent(
            name=self.name,
            system_prompt=self.system_prompt,
            model=build_chat_model(self._cfg, tier="fast"),
            model_config=ModelConfig(max_retries=3),
            toolkit=Toolkit(
                tools=[
                    FunctionTool(
                        tool,
                        permission=PermissionDecision(
                            behavior=PermissionBehavior.ALLOW,
                            message="acquisition tool is always allowed in this pipeline",
                        ),
                    )
                ]
            ),
        )


__all__ = ["AcquisitionSkill"]
