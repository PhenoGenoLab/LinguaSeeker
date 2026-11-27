"""Phase 2 skill: document parsing through the remote MinerU API.

``ParsingSkill`` owns the phase's agent and delegates the deterministic work to
``src.core.tools.parsing``.
"""

from src.pipeline.skills.parsing.service import ParsingSkill

__all__ = ["ParsingSkill"]
