"""Phase 3 verify skill: reasoning-tier verdicts that never rewrite facts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.pipeline.skills.fact_chain.agent_skill import StageAgentSkill
from src.pipeline.skills.fact_chain.prompts import VERIFY_PROMPT


class Verdict(BaseModel):
    """One verification verdict; labels are frozen by the stage contract."""

    model_config = ConfigDict(extra="forbid")

    fact_id: str
    label: Literal["supported", "unsupported", "uncertain"]
    reason: str


class VerifyReply(BaseModel):
    """Structured reply the verify agent must produce."""

    model_config = ConfigDict(extra="forbid")

    verdicts: list[Verdict]


class VerifySkill(StageAgentSkill):
    """Verify stage: source window plus candidate facts in, verdicts out."""

    stage = "verify"
    prompt = VERIFY_PROMPT
    schema = VerifyReply
    name = "fact_chain_verify"
    tier = "reasoning"


__all__ = ["Verdict", "VerifyReply", "VerifySkill"]
