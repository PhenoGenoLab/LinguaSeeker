"""Phase 3 extract skill: bounded AgentScope agent behind the provider protocol.

The runner still owns retries, budget accounting and stage events.  This module
only declares the extract prompt/schema and the window-bound helper tools.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict

from src.pipeline.contracts.skill_io import SkillError, SkillFailureKind
from src.pipeline.skills.fact_chain.agent_skill import StageAgentSkill
from src.pipeline.skills.fact_chain.prompts import EXTRACT_PROMPT
from src.pipeline.tools.fact_chain.contracts import ChainContractError
from src.pipeline.tools.fact_chain.core import is_atomic, locate_quote


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


class ExtractSkill(StageAgentSkill):
    """Extract stage: window text in, candidate facts out."""

    stage = "extract"
    prompt = EXTRACT_PROMPT
    schema = ExtractReply
    name = "fact_chain_extract"

    def _tools(self, payload: dict[str, Any]) -> list[Callable[..., str]]:
        window_text = str(payload.get("window_text") or "")
        if not window_text:
            raise SkillError("extract: payload has no window_text", kind=SkillFailureKind.PERMANENT)
        return window_tools(window_text)

    def _system_prompt(self, payload: dict[str, Any]) -> str:
        """Append reference-only ReMe recall; failures already degrade to empty."""
        if self._memory is None:
            return self.prompt
        query = str(payload.get("window_text") or "")[:400]
        block = self._memory.search(query, top_k=self._top_k).as_prompt_block()
        return f"{self.prompt}\n\n{block}" if block else self.prompt


__all__ = ["ExtractReply", "ExtractSkill", "ExtractedFact", "window_tools"]
