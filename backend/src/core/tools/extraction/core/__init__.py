"""Core business logic for evidence extraction.

Re-exports public types from focused sub-modules for convenience.
New code should prefer importing directly from the specific sub-module.
"""

from src.core.tools.extraction.core.evidence_chain import EvidenceChainBuilder
from src.core.tools.extraction.core.grouping import GroupAssigner, make_group_id, normalize_group_token
from src.core.tools.extraction.core.normalization import EvidenceItemNormalizer, FieldValueNormalizer, RawSourceNormalizer
from src.core.tools.extraction.core.quality import IntraTrackConflictChecker, QualityValidator, TargetEntityGuard
from src.core.tools.extraction.core.source_grounding import SourceGrounder, _fuzzy_ellipsis_match
from src.core.tools.extraction.core.special_evidence import SpecialEvidenceValidator

__all__ = [
    "EvidenceChainBuilder",
    "GroupAssigner",
    "IntraTrackConflictChecker",
    "QualityValidator",
    "RawSourceNormalizer",
    "SourceGrounder",
    "SpecialEvidenceValidator",
    "TargetEntityGuard",
    "EvidenceItemNormalizer",
    "FieldValueNormalizer",
    "make_group_id",
    "normalize_group_token",
    "_fuzzy_ellipsis_match",
]
