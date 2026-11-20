"""Phase 4 skill: entity standardization and knowledge alignment.

``StandardizationSkill`` owns the phase's agent and delegates the deterministic
work to ``src.pipeline.graph.agents.standardization``.
"""

from src.pipeline.skills.standardization.service import StandardizationSkill

__all__ = ["StandardizationSkill"]
