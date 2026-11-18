"""Orchestration of the source fact chain.

Stages, in order and over the full document: extract (per source window) ->
verify (per window, against the same window) -> translate (presentation fields
only; English-source documents take the passthrough path). The runner only
connects stages and passes typed state; business rules live in ``core`` and
model access goes through the ``Provider`` protocol.
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from src.pipeline.tools.fact_chain.contracts import (
    FIELD_MODES,
    STAGE_NAMES,
    ChainConfig,
    ChainRun,
    DocumentWindow,
    EnglishStatus,
    EnglishView,
    PresentationMode,
    Rejection,
    SourceDocument,
    SourceHashMismatch,
    SourceFact,
    StageName,
    StageOutcome,
    StageProgress,
    VERIFY_LABELS,
    Verification,
    VerificationLabel,
    WindowPlanEntry,
    canonical_json,
    sha256_text,
)
from src.pipeline.tools.fact_chain.core import (
    candidate_to_fact,
    reconcile,
    validate_reply_schema,
)
from src.pipeline.tools.fact_chain.windowing import chunk_document
from src.pipeline.skills.fact_chain.prompts import (
    EXTRACT_PROMPT,
    EXTRACT_PROMPT_VERSION,
    PRESENTATION_VERSION,
    TRANSLATE_PROMPT,
    TRANSLATE_PROMPT_VERSION,
    VERIFY_PROMPT,
    VERIFY_PROMPT_VERSION,
    current_prompt_versions,
)
from src.pipeline.skills.runtime.llm import Provider, ProviderError


class BudgetExhausted(Exception):
    """``max_provider_calls`` reached; the run stops with an explicit event."""

    def __init__(self, message: str, run: ChainRun) -> None:
        super().__init__(message)
        self.run = run


class ChainRunner:
    """Runs extract -> verify -> translate for one document with an injected provider."""

    def __init__(
        self,
        provider: Provider,
        config: ChainConfig,
        *,
        presentation_version: str = PRESENTATION_VERSION,
    ) -> None:
        self.provider = provider
        self.config = config
        self.presentation_version = presentation_version

    def run(self, document: SourceDocument, *, manifest_hash: str | None = None) -> ChainRun:
        run = ChainRun(
            document_id=document.document_id,
            source_hash=document.source_hash,
            language=document.language,
            config=self.config,
            prompt_versions=current_prompt_versions(self.presentation_version),
        )
        expected = manifest_hash or document.source_hash
        if document.source_hash != expected or sha256_text(document.text) != document.source_hash:
            run.event(StageName.EXTRACT, "source_hash_mismatch", detail="rejected before any provider call")
            raise SourceHashMismatch(f"{document.document_id}: manifest hash differs; no call made")
        run.event(StageName.EXTRACT, "preflight_ok", detail="source hash matches")

        windows = list(chunk_document(document.text, self.config.window_chars, self.config.window_overlap))
        self._plan_windows(run, windows)
        for stage, action in (
            (StageName.EXTRACT, self._extract),
            (StageName.VERIFY, self._verify),
            (StageName.TRANSLATE, self._translate),
        ):
            for window in windows:
                record = self._stage_record(run, window, stage)
                try:
                    outcome, detail = action(document, window, run)
                except BudgetExhausted:
                    record.outcome = StageOutcome.FAILURE
                    record.detail = f"budget exhausted during {stage.value}"
                    raise
                record.outcome = outcome
                record.detail = detail
        return run

    # -- planning -----------------------------------------------------------

    def _plan_windows(self, run: ChainRun, windows: list[DocumentWindow]) -> None:
        for window in windows:
            run.windows.append(
                WindowPlanEntry(
                    document_id=run.document_id,
                    window_id=window.label,
                    start=window.start_offset,
                    end=window.end_offset,
                )
            )
            for stage in STAGE_NAMES:
                run.stage_progress.append(
                    StageProgress(
                        document_id=run.document_id,
                        window_id=window.label,
                        start=window.start_offset,
                        end=window.end_offset,
                        stage=stage,
                    )
                )

    def _stage_record(self, run: ChainRun, window: DocumentWindow, stage: StageName) -> StageProgress:
        for record in run.stage_progress:
            if record.window_id == window.label and record.stage == stage:
                return record
        raise RuntimeError(f"stage plan missing for {window.label}/{stage.value}")

    # -- stages -------------------------------------------------------------

    def _extract(self, document: SourceDocument, window: DocumentWindow, run: ChainRun) -> tuple[StageOutcome, str]:
        parsed, error = self._call_json(
            run,
            stage=StageName.EXTRACT,
            model_id=self.config.extract_model,
            prompt=EXTRACT_PROMPT,
            prompt_version=EXTRACT_PROMPT_VERSION,
            payload={
                "document_id": document.document_id,
                "language": document.language,
                "window_id": window.label,
                "window_text": window.text,
            },
            window_id=window.label,
        )
        if parsed is None:
            return StageOutcome.FAILURE, f"provider or schema failure after retries: {error}"

        candidates = parsed.get("facts") or []
        seen = {fact.fact_id for fact in run.facts}
        for candidate in candidates:
            try:
                fact = candidate_to_fact(
                    candidate,
                    document=document,
                    window=window,
                    allowed_field_ids=self.config.allowed_field_ids,
                )
            except Exception as exc:  # noqa: BLE001 - every candidate rejection is recorded by reason
                run.rejections.append(
                    Rejection(
                        stage=StageName.EXTRACT,
                        window_id=window.label,
                        reason=getattr(exc, "reason", "candidate_invalid"),
                        detail=str(exc),
                    )
                )
                run.event(StageName.EXTRACT, "rejected", window_id=window.label, detail=str(exc))
                continue
            if fact.fact_id in seen:
                run.event(
                    StageName.EXTRACT,
                    "merged_duplicate",
                    window_id=window.label,
                    fact_id=fact.fact_id,
                    detail="same source fact found in overlap",
                )
                continue
            seen.add(fact.fact_id)
            run.facts.append(fact)
            run.event(StageName.EXTRACT, "fact_added", window_id=window.label, fact_id=fact.fact_id)
        return StageOutcome.SUCCESS, f"{len(candidates)} candidates"

    def _verify(self, document: SourceDocument, window: DocumentWindow, run: ChainRun) -> tuple[StageOutcome, str]:
        items = [fact for fact in run.facts if fact.window_id == window.label]
        if not items:
            return StageOutcome.EMPTY, "no facts to verify in this window"
        ids = [fact.fact_id for fact in items]
        parsed, error = self._call_json(
            run,
            stage=StageName.VERIFY,
            model_id=self.config.verify_model,
            prompt=VERIFY_PROMPT,
            prompt_version=VERIFY_PROMPT_VERSION,
            payload={
                "document_id": document.document_id,
                "window_id": window.label,
                "source_window_text": window.text,
                "items": [
                    {
                        "fact_id": fact.fact_id,
                        "field_id": fact.field_id,
                        "raw_value": fact.raw_value,
                        "polarity": fact.polarity.value,
                        "subject_status": fact.subject.status.value,
                        "subject_id": fact.subject.subject_id,
                        "quote": fact.quote,
                    }
                    for fact in items
                ],
            },
            window_id=window.label,
        )
        if parsed is None:
            for fact_id in ids:
                self._label(run, fact_id, VerificationLabel.UNVERIFIED, f"verify_call_failed: {error}")
            return StageOutcome.FAILURE, f"provider or schema failure after retries: {error}"

        result = reconcile(ids, parsed.get("verdicts", []), "fact_id")
        for fact_id in result.duplicates:
            run.event(StageName.VERIFY, "duplicate_ignored", window_id=window.label, fact_id=fact_id)
        for fact_id in result.unexpected:
            run.event(StageName.VERIFY, "unexpected_ignored", window_id=window.label, fact_id=fact_id)
        for fact_id in result.missing:
            run.event(StageName.VERIFY, "missing", window_id=window.label, fact_id=fact_id)
            self._label(run, fact_id, VerificationLabel.UNVERIFIED, "missing_verdict")
        for fact_id, item in result.matched.items():
            label = item.get("label")
            reason = str(item.get("reason", ""))
            if isinstance(label, str) and label in VERIFY_LABELS:
                self._label(run, fact_id, VerificationLabel(label), reason)
            else:
                self._label(run, fact_id, VerificationLabel.UNVERIFIED, "invalid_label")
        return StageOutcome.SUCCESS, f"{len(result.matched)} labelled, {len(result.missing)} missing"

    def _label(self, run: ChainRun, fact_id: str, label: VerificationLabel, reason: str) -> None:
        run.verifications.append(
            Verification(
                fact_id=fact_id,
                label=label,
                reason=reason,
                model_id=self.config.verify_model,
                prompt_version=VERIFY_PROMPT_VERSION,
            )
        )

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

    # -- provider boundary --------------------------------------------------

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
        payload_text = canonical_json(payload)
        last_error = "no attempt made"
        for attempt in range(1, self.config.max_attempts + 1):
            if self.config.max_provider_calls > 0 and run.provider_calls >= self.config.max_provider_calls:
                run.event(stage, "budget_exhausted", window_id=window_id)
                raise BudgetExhausted(
                    f"max_provider_calls={self.config.max_provider_calls} reached at {stage.value}",
                    run,
                )
            run.provider_calls += 1
            try:
                text = self.provider.invoke(stage=stage.value, model_id=model_id, prompt=prompt, payload=payload_text)
            except ProviderError as exc:
                last_error = f"provider: {exc}"
                run.event(stage, "attempt_failed", window_id=window_id, detail=last_error)
                continue
            try:
                parsed = json.loads(text)
                validate_reply_schema(parsed, stage.value)
            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                last_error = f"parse: {exc}"
                run.event(stage, "attempt_failed", window_id=window_id, detail=last_error)
                continue
            logger.debug(
                "source fact chain stage ok: stage={}, window={}, attempt={}, presentation={}",
                stage.value,
                window_id,
                attempt,
                presentation_version,
            )
            return parsed, None
        run.event(stage, "failed", window_id=window_id, detail=last_error)
        return None, last_error


__all__ = ["BudgetExhausted", "ChainRunner"]
