"""Portal — entity standardization agent.

Matching, importers and persistence live in :mod:`src.core.tools.standardization`,
the agent in :mod:`src.pipeline.skills.standardization`.
"""

from src.pipeline.skills.standardization import StandardizationSkill

__all__ = ["StandardizationSkill"]
