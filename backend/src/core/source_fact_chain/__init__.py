"""Transitional re-export shim package for :mod:`src.pipeline.{tools,skills}.fact_chain`.

The implementation moved in stage 2. Importers should use
``src.pipeline.tools.fact_chain`` (deterministic helpers) and
``src.pipeline.skills.fact_chain`` (prompts, stage runner, service facade).
This package only re-exports for one release cycle.
"""

from src.pipeline.tools.fact_chain.contracts import (
    ChainConfig,
    ChainRun,
    EnglishView,
    SourceDocument,
    SourceFact,
    Verification,
)
from src.pipeline.tools.fact_chain.projection import project_dual_result, supported_facts
from src.pipeline.skills.fact_chain.runner import ChainRunner
from src.pipeline.skills.fact_chain.service import ChainArtifacts, SourceFactChainService

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
