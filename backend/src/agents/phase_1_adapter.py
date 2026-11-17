"""Transitional re-export shim for :mod:`src.pipeline.graph.phases.phase_1`.

Kept for one release cycle; new code should import the new path.
"""

from src.pipeline.graph.phases.phase_1 import Phase1Adapter

__all__ = ["Phase1Adapter"]
