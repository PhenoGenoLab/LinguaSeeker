"""Prompt builders for evidence extraction stages.

Re-exports all prompt builder functions for backward compatibility.
Import directly from specific sub-modules for better dependency tracking.
"""

from src.pipeline.skills.extraction.prompts.blocks import block_context_ref, block_readable_text, build_block_prompt_text, format_block_prompt_entry, map_block_type
from src.pipeline.skills.extraction.prompts.catalog import get_catalog_extraction_prompt
from src.pipeline.skills.extraction.prompts.context import get_clinical_context_prompt, get_core_identity_retry_prompt
from src.pipeline.skills.extraction.prompts.evidence_map import disease_boundary_guidance, expanded_field_coverage_guidance, get_channel_strategy_guidance, get_evidence_map_prompt, relationship_decision_guidance
from src.pipeline.skills.extraction.prompts.special import get_source_ambiguity_review_prompt, get_special_evidence_prompt

__all__ = [
    "block_context_ref",
    "block_readable_text",
    "build_block_prompt_text",
    "disease_boundary_guidance",
    "expanded_field_coverage_guidance",
    "format_block_prompt_entry",
    "get_catalog_extraction_prompt",
    "get_channel_strategy_guidance",
    "get_clinical_context_prompt",
    "get_core_identity_retry_prompt",
    "get_evidence_map_prompt",
    "get_source_ambiguity_review_prompt",
    "get_special_evidence_prompt",
    "map_block_type",
    "relationship_decision_guidance",
]

# Legacy single-file prompt versions, merged into this package.

from src.core.shared.tools.fact_chain.contracts import (
    ALLOWED_FIELD_IDS,
    FIELD_MODES,
    PromptVersions,
    sha256_text,
)
from src.pipeline.skills.translation.prompts import TRANSLATE_PROMPT_VERSION


EXTRACT_PROMPT = (
    "Extract clinical genetics facts from the source-language text window. Return JSON "
    '{"facts": [...]}; each fact has field_id (one of: '
    + ", ".join(ALLOWED_FIELD_IDS)
    + "), raw_value (verbatim substring of quote), polarity (positive, negative or uncertain), "
    "subject_status (known or unknown), subject_id (string when known, null when unknown) and "
    "quote (verbatim source sentence). Never translate. Never guess an unknown subject. "
    "Emit one fact per atomic value; never join several variants or phenotypes with a semicolon."
)
VERIFY_PROMPT = (
    "Check each candidate fact against the source window only. Return JSON "
    '{"verdicts": [{"fact_id", "label" (supported, unsupported or uncertain), "reason"}]}. '
    "Do not rewrite, correct or translate a candidate."
)
EXTRACT_PROMPT_VERSION = "extract:" + sha256_text(EXTRACT_PROMPT)[:12]
VERIFY_PROMPT_VERSION = "verify:" + sha256_text(VERIFY_PROMPT)[:12]
PRESENTATION_VERSION = "en-presentation-v1:" + TRANSLATE_PROMPT_VERSION


def current_prompt_versions(presentation_version: str = PRESENTATION_VERSION) -> PromptVersions:
    """Return the prompt identities a run must match to be reusable."""
    return PromptVersions(
        extract=EXTRACT_PROMPT_VERSION,
        verify=VERIFY_PROMPT_VERSION,
        translate=TRANSLATE_PROMPT_VERSION,
        presentation=presentation_version,
    )


PRESENTED_FIELD_IDS: tuple[str, ...] = tuple(field_id for field_id, mode in FIELD_MODES.items() if mode == "presented")
