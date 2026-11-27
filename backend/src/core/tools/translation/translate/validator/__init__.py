"""Translation quality validation and post-processing.

Re-exports all validation functions.
"""

from src.core.tools.translation.translate.validator.artifacts import _is_terminology_echo, strip_inline_artifacts, strip_prompt_artifacts, strip_prompt_echo, strip_source_contamination
from src.core.tools.translation.translate.validator.core import _IMAGE_REF_RE, summarize_validation_error, validate_image_references_preserved, validate_segment, validate_translation_output
from src.core.tools.translation.translate.validator.normalize import fix_email_placeholder, fix_ocr_truncations, fix_word_boundary_redacted, normalize_cjk_punctuation, normalize_keywords_capitalization, normalize_placeholders
from src.core.tools.translation.translate.validator.redacted import mark_redacted_values

__all__ = [
    "_IMAGE_REF_RE",
    "_is_terminology_echo",
    "fix_email_placeholder",
    "fix_ocr_truncations",
    "fix_word_boundary_redacted",
    "mark_redacted_values",
    "normalize_cjk_punctuation",
    "normalize_keywords_capitalization",
    "normalize_placeholders",
    "strip_inline_artifacts",
    "strip_prompt_artifacts",
    "strip_prompt_echo",
    "strip_source_contamination",
    "summarize_validation_error",
    "validate_image_references_preserved",
    "validate_segment",
    "validate_translation_output",
]
