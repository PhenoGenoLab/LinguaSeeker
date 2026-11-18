"""Phase 3 translate skill: English presentation for PRESENTED fields only."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.pipeline.skills.fact_chain.agent_skill import StageAgentSkill
from src.pipeline.skills.fact_chain.prompts import TRANSLATE_PROMPT


class Translation(BaseModel):
    """One fact-level English presentation; never a new fact."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str
    english_text: str


class TranslateReply(BaseModel):
    """Structured reply the translate agent must produce."""

    model_config = ConfigDict(extra="forbid")

    translations: list[Translation]


class TranslateSkill(StageAgentSkill):
    """Translate stage: presented values in, fact English out.

    English-source documents never reach this skill: the runner takes the
    passthrough path before any provider call.
    """

    stage = "translate"
    prompt = TRANSLATE_PROMPT
    schema = TranslateReply
    name = "fact_chain_translate"


__all__ = ["Translation", "TranslateReply", "TranslateSkill"]
