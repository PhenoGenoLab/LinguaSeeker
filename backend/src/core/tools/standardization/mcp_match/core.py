"""Phenotype matching through the FastHPOCR MCP service."""

from __future__ import annotations

from typing import Protocol

from loguru import logger

from src.core.adapters.mcp.hpocr import HpoAnnotation
from src.core.tools.standardization.contracts import (
    EntityMatch,
    EntityType,
    MatchMethod,
    MatchStatus,
    StandardizationCandidate,
    TerminologyCandidate,
)


class HpoAnnotationClient(Protocol):
    """Protocol implemented by the FastHPOCR MCP adapter."""

    async def annotate(self, text: str, *, longest_match: bool = True) -> tuple[HpoAnnotation, ...]: ...


class HpoMcpTerminologyMatcher:
    """Map phenotype mentions through FastHPOCR, delegating other entity types.

    A phenotype maps only when the service returns one HPO identity for the
    mention. Several distinct identities are reported as ambiguous rather than
    silently picking one; service failures degrade to unmapped.
    """

    def __init__(self, client: HpoAnnotationClient, fallback) -> None:
        self._client = client
        self._fallback = fallback
        self._cache: dict[str, tuple[HpoAnnotation, ...]] = {}

    async def match(self, candidate: StandardizationCandidate) -> EntityMatch:
        """Return a FastHPOCR-derived match for phenotypes, else use fallback."""
        if candidate.entity_type != EntityType.PHENOTYPE:
            return await self._fallback.match(candidate)
        annotations = await self._annotate(candidate.raw_text)
        if annotations is None:
            return self._unmapped(candidate, "hpocr MCP service unavailable")
        if not annotations:
            return self._unmapped(candidate, "no HPO annotation")
        return self._choose(candidate, annotations)

    async def _annotate(self, text: str) -> tuple[HpoAnnotation, ...] | None:
        cached = self._cache.get(text)
        if cached is not None:
            return cached
        try:
            annotations = await self._client.annotate(text, longest_match=True)
        except Exception as exc:  # noqa: BLE001 - external service failure degrades to unmapped
            logger.warning("hpocr MCP annotation failed for {!r}: {}", text[:120], exc)
            return None
        self._cache[text] = annotations
        return annotations

    def _choose(
        self,
        candidate: StandardizationCandidate,
        annotations: tuple[HpoAnnotation, ...],
    ) -> EntityMatch:
        unique = _unique_by_uri(annotations)
        if len(unique) == 1:
            annotation = unique[0]
            return EntityMatch(
                candidate=candidate,
                status=MatchStatus.STANDARDIZED,
                external_id=annotation.hpo_uri,
                display_name=annotation.hpo_label,
                terminology_candidates=(_terminology_candidate(annotation),),
                rationale="FastHPOCR MCP annotation",
                match_method=MatchMethod.MCP,
            )

        exact = tuple(
            annotation
            for annotation in annotations
            if _normalize_span(annotation.text_span) == _normalize_span(candidate.raw_text)
        )
        if len(exact) == 1:
            annotation = exact[0]
            return EntityMatch(
                candidate=candidate,
                status=MatchStatus.STANDARDIZED,
                external_id=annotation.hpo_uri,
                display_name=annotation.hpo_label,
                terminology_candidates=(_terminology_candidate(annotation),),
                rationale="FastHPOCR MCP exact-span annotation",
                match_method=MatchMethod.MCP,
            )
        return EntityMatch(
            candidate=candidate,
            status=MatchStatus.AMBIGUOUS,
            external_id=None,
            display_name=candidate.raw_text,
            terminology_candidates=tuple(_terminology_candidate(item) for item in unique),
            rationale="multiple distinct FastHPOCR HPO annotations",
            match_method=MatchMethod.MCP,
        )

    def _unmapped(self, candidate: StandardizationCandidate, rationale: str) -> EntityMatch:
        return EntityMatch(
            candidate=candidate,
            status=MatchStatus.UNMAPPED,
            external_id=None,
            display_name=candidate.raw_text,
            rationale=rationale,
            match_method=MatchMethod.MCP,
        )


def _unique_by_uri(annotations: tuple[HpoAnnotation, ...]) -> list[HpoAnnotation]:
    seen: set[str] = set()
    unique: list[HpoAnnotation] = []
    for annotation in annotations:
        if annotation.hpo_uri in seen:
            continue
        seen.add(annotation.hpo_uri)
        unique.append(annotation)
    return unique


def _terminology_candidate(annotation: HpoAnnotation) -> TerminologyCandidate:
    return TerminologyCandidate(
        entry_id=annotation.hpo_uri,
        entity_type=EntityType.PHENOTYPE,
        source_db="HPO",
        external_id=annotation.hpo_uri,
        display_name=annotation.hpo_label,
        normalized_alias=_normalize_span(annotation.text_span),
        alias_type="mcp",
        raw_payload={
            "start": annotation.start,
            "end": annotation.end,
            "text_span": annotation.text_span,
        },
    )


def _normalize_span(value: str) -> str:
    return " ".join(value.casefold().split())
