"""Portal — Phase 1 acquisition agent.

The implementation lives in :mod:`src.core.tools.acquisition` (deterministic
tooling) and :mod:`src.pipeline.skills.acquisition` (the bounded agent). The
graph imports only this portal; every other caller imports the implementation
directly so there is exactly one definition per name.
"""

from src.core.tools.acquisition import AcquisitionSource, DocumentAcquisitionRequest

__all__ = ["AcquisitionSource", "DocumentAcquisitionRequest"]
