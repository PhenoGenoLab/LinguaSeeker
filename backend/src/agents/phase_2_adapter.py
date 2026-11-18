"""Transitional re-export shim for :mod:`src.pipeline.graph.phases.phase_2`.

Kept for one release cycle; new code should import the new path.
"""

from src.pipeline.graph.phases.phase_2 import Phase2Adapter

__all__ = ["Phase2Adapter"]
