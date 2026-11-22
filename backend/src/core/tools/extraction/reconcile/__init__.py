"""Source-grounded cross-track reconcile: contracts and pure logic.

The service facade lives in :mod:`src.pipeline.skills.extraction.reconcile.api`.
"""

from src.core.tools.extraction.reconcile.contracts import CandidateScore, FieldDecision, ReconcileOutput, ReconcileParams
from src.core.tools.extraction.reconcile.core import reconcile_results

__all__ = ["CandidateScore", "FieldDecision", "ReconcileOutput", "ReconcileParams", "reconcile_results"]
