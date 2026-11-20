"""Translate-stage prompt: presentation fields only, never new facts.

The stage translates the *presentation* fields of already-verified facts; it may
not introduce facts, alter polarity or touch preserved fields.
"""

from __future__ import annotations

from src.core.shared.tools.fact_chain.contracts import sha256_text


TRANSLATE_PROMPT = (
    "Translate each raw_value into English. Keep numbers, units, gene and variant strings, "
    "negation and uncertainty. Do not add facts. Return JSON "
    '{"translations": [{"fact_id", "english_text"}]}.'
)
TRANSLATE_PROMPT_VERSION = "translate:" + sha256_text(TRANSLATE_PROMPT)[:12]


__all__ = ["TRANSLATE_PROMPT", "TRANSLATE_PROMPT_VERSION"]
