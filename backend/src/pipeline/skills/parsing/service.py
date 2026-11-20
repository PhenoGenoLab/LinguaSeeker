"""Phase 2 skill: document parsing (MinerU remote → local fallback).

Same contract as the acquisition skill: deterministic delegation in ``legacy``
mode, agent path only under ``shadow``/``agentscope``.
"""

from __future__ import annotations

import json
from typing import Any

from src.pipeline.skills.runtime.modes import run_phase_async


class ParsingSkill:
    """Bounded agent for Phase 2: one tool that parses and saves artifacts."""

    name = "phase_2_parsing"
    system_prompt = (
        "You parse one document for a clinical-genetics pipeline.\n"
        "Call the `parse_document` tool exactly once with the JSON payload you were given,\n"
        "then reply with that tool's JSON output verbatim. Do not invent fields."
    )

    def __init__(self, cfg: Any = None, service: Any = None) -> None:
        self._cfg = cfg
        self._service = service
        self._agent = None

    @property
    def service(self) -> Any:
        if self._service is None:
            from src.core.agents.parsing import create_parse_service

            self._service = create_parse_service()
        return self._service

    async def parse_local_files_and_save(self, *, file_paths: list[str], output_dir: str) -> Any:
        """Parse the given files, honouring ``pipeline.agent_runtime``."""
        return await run_phase_async(
            self.name,
            legacy=lambda: self.service.parse_local_files_and_save(file_paths=file_paths, output_dir=output_dir),
            agent=lambda: self._agent_parse(file_paths=file_paths, output_dir=output_dir),
        )

    def _result_model(self) -> type:
        from src.core.agents.parsing.contracts import ParseResult

        return ParseResult

    def _build_agent(self) -> Any:
        if self._agent is not None:
            return self._agent
        from src.pipeline.skills.runtime.agent import build_agent
        from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

        result_model = self._result_model()

        async def parse_document(payload: str) -> str:
            """Parse the given files and return the saved-artifact JSON."""
            data = json.loads(payload)
            result = await self.service.parse_local_files_and_save(
                file_paths=list(data["file_paths"]),
                output_dir=str(data["output_dir"]),
            )
            return result_model.model_validate(result).model_dump_json()

        self._agent = build_agent(
            name=self.name,
            system_prompt=self.system_prompt,
            model=build_chat_model(self._cfg, tier="fast"),
            tools=[parse_document],
        )
        return self._agent

    async def _agent_parse(self, *, file_paths: list[str], output_dir: str) -> Any:
        from agentscope.message import Msg, TextBlock

        payload = json.dumps({"file_paths": file_paths, "output_dir": output_dir})
        reply = await self._build_agent().reply(Msg(name="user", role="user", content=[TextBlock(text=payload)]))
        text = reply.get_text_content() if hasattr(reply, "get_text_content") else str(reply.content)
        return self._result_model().model_validate_json(text)


__all__ = ["ParsingSkill"]
