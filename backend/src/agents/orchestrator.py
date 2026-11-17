"""Transitional re-export shim for :mod:`src.pipeline.graph.topology`.

Kept for one release cycle so existing callers (``src/api/wiring.py``) keep
importing the old path without changing behaviour.  New code should import
``src.pipeline.graph.topology``.
"""

from src.pipeline.graph.topology import REQUIRED_UPSTREAM, PipelineOrchestrator

__all__ = ["PipelineOrchestrator", "REQUIRED_UPSTREAM"]
