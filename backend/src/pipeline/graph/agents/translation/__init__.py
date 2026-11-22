"""Portal — translation agent.

Deterministic text work lives in :mod:`src.core.tools.translation`, the agent in
:mod:`src.pipeline.skills.translation`. The graph imports this portal only.
"""

from src.core.tools.translation.translate.language_detector import detect_language
from src.pipeline.skills.translation import TranslationService

__all__ = ["TranslationService", "detect_language"]
