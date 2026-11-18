"""Versioned prompts for extract -> verify -> translate.

Prompt identity is part of the audit record: changing the text changes the
version suffix carried by every verification and English view.
"""

from __future__ import annotations

from src.core.tools.fact_chain.contracts import (
    ALLOWED_FIELD_IDS,
    FIELD_MODES,
    PromptVersions,
    sha256_text,
)


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
TRANSLATE_PROMPT = (
    "Translate each raw_value into English. Keep numbers, units, gene and variant strings, "
    "negation and uncertainty. Do not add facts. Return JSON "
    '{"translations": [{"fact_id", "english_text"}]}.'
)

EXTRACT_PROMPT_VERSION = "extract:" + sha256_text(EXTRACT_PROMPT)[:12]
VERIFY_PROMPT_VERSION = "verify:" + sha256_text(VERIFY_PROMPT)[:12]
TRANSLATE_PROMPT_VERSION = "translate:" + sha256_text(TRANSLATE_PROMPT)[:12]
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
