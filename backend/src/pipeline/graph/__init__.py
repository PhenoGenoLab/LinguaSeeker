"""LangGraph topology and phase adapters.

Import boundary: this package must not import ``agentscope``.  Graph code owns
topology, conditional edges and node adapters only; prompts and model calls
belong to ``src.pipeline.skills``.
"""
