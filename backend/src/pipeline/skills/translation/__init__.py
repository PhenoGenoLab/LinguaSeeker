"""Phase 3 translation skill: presentation-field English views.

Split out of the former ``fact_chain`` package: extraction owns candidate facts
and their verification, translation owns turning verified facts into English
presentation fields without creating new facts.
"""

from src.pipeline.skills.translation.prompts import TRANSLATE_PROMPT, TRANSLATE_PROMPT_VERSION
from src.pipeline.skills.translation.api import TranslationService
from src.pipeline.skills.translation.stage import TranslationStage

__all__ = ["TRANSLATE_PROMPT", "TRANSLATE_PROMPT_VERSION", "TranslationService", "TranslationStage"]
