"""Portal — Phase 2 parsing agent.

The implementation lives in :mod:`src.core.tools.parsing` (parser strategies,
orchestration, contracts) and :mod:`src.pipeline.skills.parsing` (the bounded
agent). The graph imports only this portal; every other caller imports the
implementation directly so there is exactly one definition per name.
"""

from src.pipeline.skills.parsing import ParsingSkill

__all__ = ["ParsingSkill"]
