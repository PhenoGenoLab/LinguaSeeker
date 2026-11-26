"""Phase 2 skill: document parsing (MinerU remote → local fallback).

Same contract as acquisition: the agent must call the `parse_document` tool and
the tool's real ``ParseResult`` is returned unchanged.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any



class ParsingSkill:
    """Bounded agent for Phase 2: one tool that parses and saves artifacts."""

    name = "parsing"
    system_prompt = (
        "You parse one document for a clinical-genetics pipeline.\n"
        "Call the `parse_document` tool exactly once, then reply with a one-line summary."
    )

    def __init__(self, cfg: Any = None, service: Any = None, agent: Any = None) -> None:
        self._cfg = cfg
        self._service = service
        self._agent = agent
        self._tool: Callable[[str], Awaitable[str]] | None = None

    @property
    def service(self) -> Any:
        if self._service is None:
            from src.core.tools.parsing import create_parse_service

            self._service = create_parse_service()
        return self._service

    async def parse_local_files_and_save(self, *, file_paths: list[str], output_dir: str) -> Any:
        """Parse the given files through the agent's single tool."""
        holder: dict[str, Any] = {}

        async def parse_document(payload: str) -> str:
            """Parse the bound files and return a short status string."""
            holder["result"] = await self.service.parse_local_files_and_save(
                file_paths=file_paths, output_dir=output_dir
            )
            return "parsed"

        self._tool = parse_document
        agent = self._build_agent(parse_document)
        from agentscope.message import UserMsg

        for _ in range(2):
            await agent.reply(UserMsg(name="user", content="parse the document"))
            if "result" in holder:
                return holder["result"]
            await agent.reply(
                UserMsg(
                    name="user",
                    content="You must call the `parse_document` tool now; do not answer in text.",
                )
            )
        raise RuntimeError(f"{self.name}: agent did not call parse_document")

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
                            message="parsing tool is always allowed in this pipeline",
                        ),
                    )
                ]
            ),
        )


__all__ = ["ParsingSkill"]
