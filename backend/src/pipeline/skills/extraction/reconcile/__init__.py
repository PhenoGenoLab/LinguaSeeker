"""Source-grounded cross-track reconcile for dual evidence extraction."""

from src.pipeline.skills.extraction.reconcile.api import CrossTrackReconcileService
from src.core.tools.extraction.reconcile.contracts import CandidateScore, FieldDecision, ReconcileOutput, ReconcileParams
from src.core.tools.extraction.reconcile.core import reconcile_results

__all__ = [
    "CandidateScore",
    "CrossTrackReconcileService",
    "FieldDecision",
    "ReconcileOutput",
    "ReconcileParams",
    "reconcile_results",
]
