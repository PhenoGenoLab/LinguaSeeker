"""Transitional re-export shim for :mod:`src.pipeline.graph.phases.phase_3`.

Kept for one release cycle; new code should import the new path.
"""

from src.pipeline.graph.phases.phase_3 import Phase3Adapter

__all__ = ["Phase3Adapter"]
