"""Phase 4 skill: entity standardization and knowledge alignment.

``StandardizationSkill`` owns the phase's agent and delegates the deterministic
work to ``src.core.agents.standardization``.
"""

from src.pipeline.skills.standardization.service import StandardizationSkill

__all__ = ["StandardizationSkill"]
