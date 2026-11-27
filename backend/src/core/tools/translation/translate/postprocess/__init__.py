"""Post-processing: dedup, quality flagging, language check, block building.

Re-exports all post-processing functions for backward compatibility.
Import directly from specific sub-modules for better dependency tracking.
"""

from src.core.tools.translation.translate.postprocess.blocks import _DOI_RE, build_translated_blocks, fallback_block_text
from src.core.tools.translation.translate.postprocess.drift import compute_translation_drift
from src.core.tools.translation.translate.postprocess.quality import check_block_coverage, check_block_language, deduplicate_bilingual_blocks, flag_quality_issues, trim_repetitive_content

__all__ = [
    "_DOI_RE",
    "build_translated_blocks",
    "check_block_coverage",
    "check_block_language",
    "compute_translation_drift",
    "deduplicate_bilingual_blocks",
    "fallback_block_text",
    "flag_quality_issues",
    "trim_repetitive_content",
]
