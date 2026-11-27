"""Translation pipeline: language detection, multi-stage LLM translation, validation."""

from src.core.tools.translation.translate.blocks import _BLOCK_SEP, is_short_keyword, merge_short_keywords, split_merged_keywords
from src.core.tools.translation.translate.exceptions import TranslationError
from src.core.tools.translation.translate.language_detector import detect_language
from src.core.tools.translation.translate.postprocess import build_translated_blocks, compute_translation_drift, deduplicate_bilingual_blocks
from src.pipeline.skills.translation.translate.providers import create_llm, create_json_llm, invoke_with_retry
from src.pipeline.skills.translation.translate.translator import MultiStageTranslator
from src.core.tools.translation.translate.validator import mark_redacted_values, normalize_cjk_punctuation, normalize_placeholders, strip_prompt_artifacts, validate_segment, validate_translation_output

__all__ = [
    "MultiStageTranslator",
    "TranslationError",
    "_BLOCK_SEP",
    "build_translated_blocks",
    "compute_translation_drift",
    "create_json_llm",
    "create_llm",
    "deduplicate_bilingual_blocks",
    "detect_language",
    "invoke_with_retry",
    "is_short_keyword",
    "mark_redacted_values",
    "merge_short_keywords",
    "normalize_cjk_punctuation",
    "normalize_placeholders",
    "split_merged_keywords",
    "strip_prompt_artifacts",
    "validate_segment",
    "validate_translation_output",
]
