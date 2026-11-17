"""Source-grounded fact chain: windows -> extract -> verify -> fact English -> bilingual rows."""

from .api import ChainArtifacts, SourceFactChainService
from .contracts import (
    ChainConfig,
    ChainRun,
    EnglishView,
    SourceDocument,
    SourceFact,
    Verification,
)
from .projection import project_dual_result, supported_facts
from .runner import ChainRunner

__all__ = [
    "ChainArtifacts",
    "ChainConfig",
    "ChainRun",
    "ChainRunner",
    "EnglishView",
    "SourceDocument",
    "SourceFact",
    "SourceFactChainService",
    "Verification",
    "project_dual_result",
    "supported_facts",
]
