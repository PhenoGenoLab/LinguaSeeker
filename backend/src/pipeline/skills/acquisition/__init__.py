"""Phase 1 skill: document acquisition.

``AcquisitionSkill`` owns the phase's agent and delegates the deterministic work
to ``src.pipeline.graph.agents.acquisition``.
"""

from src.pipeline.skills.acquisition.service import AcquisitionSkill

__all__ = ["AcquisitionSkill"]
