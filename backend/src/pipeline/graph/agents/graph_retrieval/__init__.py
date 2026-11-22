"""Portal — literature graph retrieval agent.

Graph building and retrieval live in :mod:`src.core.tools.graph_retrieval`, the
Q&A agent in :mod:`src.pipeline.skills.graph_retrieval`.
"""

from src.pipeline.skills.graph_retrieval.api import GraphRagService

__all__ = ["GraphRagService"]
