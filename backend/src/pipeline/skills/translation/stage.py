"""Translate stage of the source fact chain.

Owns the presentation-field translation: which facts get an English view, how a
provider reply is reconciled against the presented facts, and what an English
view looks like when the call fails. The stage executes inside ``ChainRunner``
via mixin composition, so it uses the runner's provider boundary
(``_call_json``), config and presentation version.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.shared.tools.fact_chain.contracts import (
    FIELD_MODES,
    ChainRun,
    DocumentWindow,
    EnglishStatus,
    EnglishView,
    PresentationMode,
    SourceDocument,
    SourceFact,
    StageName,
    StageOutcome,
)
from src.core.shared.tools.fact_chain.core import reconcile
from src.pipeline.skills.translation.prompts import TRANSLATE_PROMPT, TRANSLATE_PROMPT_VERSION

if TYPE_CHECKING:
    from src.core.shared.tools.fact_chain.contracts import ChainConfig


class TranslationStage:
    """Presentation-field translation for one window (mixin for ``ChainRunner``)."""

    # Provided by the composing runner; declared here so type checkers see them.
    config: "ChainConfig"
    presentation_version: str

    def _call_json(
        self,
        run: ChainRun,
        *,
        stage: StageName,
        model_id: str,
        prompt: str,
        prompt_version: str,
        payload: dict[str, Any],
        window_id: str,
        presentation_version: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        raise NotImplementedError("provided by the composing ChainRunner")


    def _translate(self, document: SourceDocument, window: DocumentWindow, run: ChainRun) -> tuple[StageOutcome, str]:
        items = [fact for fact in run.facts if fact.window_id == window.label]
        presented: list[SourceFact] = []
        for fact in items:
            if FIELD_MODES[fact.field_id] == PresentationMode.PRESERVED:
                run.english.append(
                    self._view(
                        fact, mode=PresentationMode.PRESERVED, status=EnglishStatus.PRESERVED, text=fact.raw_value
                    )
                )
            else:
                presented.append(fact)
        if not presented:
            return StageOutcome.EMPTY, "no presented fields in this window"
        if document.language == "en":
            for fact in presented:
                run.english.append(
                    self._view(
                        fact, mode=PresentationMode.PRESENTED, status=EnglishStatus.PASSTHROUGH, text=fact.raw_value
                    )
                )
            run.event(
                StageName.TRANSLATE, "passthrough", window_id=window.label, detail="English source; no translation call"
            )
            return StageOutcome.SUCCESS, "English passthrough views created"

        ids = [fact.fact_id for fact in presented]
        parsed, error = self._call_json(
            run,
            stage=StageName.TRANSLATE,
            model_id=self.config.translate_model,
            prompt=TRANSLATE_PROMPT,
            prompt_version=TRANSLATE_PROMPT_VERSION,
            payload={
                "document_id": document.document_id,
                "source_language": document.language,
                "window_id": window.label,
                "items": [
                    {"fact_id": fact.fact_id, "field_id": fact.field_id, "raw_value": fact.raw_value}
                    for fact in presented
                ],
            },
            window_id=window.label,
            presentation_version=self.presentation_version,
        )
        if parsed is None:
            for fact in presented:
                run.english.append(self._failed_view(fact, f"translate_call_failed: {error}"))
            return StageOutcome.FAILURE, f"provider or schema failure after retries: {error}"

        result = reconcile(ids, parsed.get("translations", []), "fact_id")
        for fact_id in result.duplicates:
            run.event(StageName.TRANSLATE, "duplicate_ignored", window_id=window.label, fact_id=fact_id)
        for fact_id in result.unexpected:
            run.event(
                StageName.TRANSLATE,
                "unexpected_ignored",
                window_id=window.label,
                fact_id=fact_id,
                detail="translation may not introduce facts",
            )
        for fact in presented:
            item = result.matched.get(fact.fact_id)
            if item is None:
                run.event(StageName.TRANSLATE, "missing", window_id=window.label, fact_id=fact.fact_id)
                run.english.append(
                    self._view(
                        fact,
                        mode=PresentationMode.PRESENTED,
                        status=EnglishStatus.MISSING,
                        text=None,
                        error="missing_translation",
                    )
                )
                continue
            text = item.get("english_text")
            if isinstance(text, str) and text.strip():
                run.english.append(
                    self._view(
                        fact,
                        mode=PresentationMode.PRESENTED,
                        status=EnglishStatus.TRANSLATED,
                        text=text,
                    )
                )
            else:
                run.english.append(self._failed_view(fact, "invalid_english_text"))
        return StageOutcome.SUCCESS, f"{len(result.matched)} translated, {len(result.missing)} missing"

    def _view(
        self,
        fact: SourceFact,
        *,
        mode: PresentationMode,
        status: EnglishStatus,
        text: str | None,
        error: str | None = None,
    ) -> EnglishView:
        translated = status is EnglishStatus.TRANSLATED
        return EnglishView(
            fact_id=fact.fact_id,
            field_id=fact.field_id,
            mode=mode,
            status=status,
            english_text=text,
            polarity=fact.polarity,
            subject=fact.subject,
            presentation_version=self.presentation_version if translated else None,
            model_id=self.config.translate_model if translated else None,
            error=error,
        )

    def _failed_view(self, fact: SourceFact, error: str) -> EnglishView:
        return self._view(
            fact,
            mode=PresentationMode.PRESENTED,
            status=EnglishStatus.FAILED,
            text=None,
            error=error,
        )


__all__ = ["TranslationStage"]
