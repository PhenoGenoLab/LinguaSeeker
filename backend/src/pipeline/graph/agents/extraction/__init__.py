"""Portal — evidence extraction agent.

Deterministic rules live in :mod:`src.core.tools.extraction`, the agent itself
in :mod:`src.pipeline.skills.extraction`. The graph imports this portal only.
"""

from src.core.tools.extraction.contracts import DualEvidenceExtractionResult
from src.core.tools.extraction.projection import project_dual_result
from src.pipeline.skills.extraction.service import SourceFactChainService

__all__ = ["DualEvidenceExtractionResult", "SourceFactChainService", "project_dual_result"]
