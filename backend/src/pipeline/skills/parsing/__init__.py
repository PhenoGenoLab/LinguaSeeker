"""Phase 2 skill: document parsing (MinerU remote -> local fallback).

``ParsingSkill`` owns the phase's agent and delegates the deterministic work to
``src.pipeline.graph.agents.parsing``.
"""

from src.pipeline.skills.parsing.service import ParsingSkill

__all__ = ["ParsingSkill"]
