"""Presentation helpers for evidence search and group detail responses."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from loguru import logger

from src.core.tools.review.contracts import (
    EvidenceChainHighlight,
    EvidenceFieldDistribution,
    EvidenceGroupItem,
    EvidenceSearchResult,
    EvidenceTrackTrace,
)
from src.utils.text.content import parse_gene_from_group_id, parse_variant_from_group_id

from src.core.tools.review.evidence_search_repository import (
    CLASSIFICATION_FIELDS as _CLASSIFICATION_FIELDS,
    DISEASE_FIELDS as _DISEASE_FIELDS,
    GENE_FIELDS as _GENE_FIELDS,
    VARIANT_FIELDS as _VARIANT_FIELDS,
)
from src.core.tools.review.search_blocks import coerce_str, row_fact_key

_TOKEN_BOUNDARY_CHARS = r"A-Za-z0-9_"


def category_from_field_id(field_id: str) -> str | None:
    """Infer the evidence category prefix from a field id."""
    if not field_id:
        return None
    if "." not in field_id:
        return field_id
    return field_id.split(".", 1)[0]


def extract_summary_field(
    field_id: str,
    value: str | None,
    target: dict[str, str | None],
) -> None:
    """Extract gene/variant/disease/classification into target dict if not already set."""
    if field_id in _GENE_FIELDS and not target.get("gene"):
        target["gene"] = coerce_str(value)
    elif field_id in _VARIANT_FIELDS and not target.get("variant"):
        target["variant"] = coerce_str(value)
    elif field_id in _DISEASE_FIELDS and not target.get("disease"):
        target["disease"] = coerce_str(value)
    elif field_id in _CLASSIFICATION_FIELDS and not target.get("classification"):
        target["classification"] = coerce_str(value)


def _parse_source_offset(raw: Any, *, default: int, name: str) -> tuple[int, bool]:
    """Parse a stored source offset, with default + validity flag for fallback.

    Returns (offset, valid). ``valid`` is False when the stored value was
    missing or malformed; callers use that to decide between clamping and
    value-anchor fallback.
    """
    if raw is None:
        return default, False
    try:
        return int(raw), True
    except (TypeError, ValueError):
        logger.warning(
            "Invalid source_span {}_offset={!r}; using value fallback",
            name,
            raw,
        )
        return default, False


def _find_value_anchor(text: str, value: str | None) -> tuple[int, int] | None:
    """Find a safe case-insensitive value anchor in snippet text.

    Single-letter values are too ambiguous in prose. Two-letter values are
    only matched when uppercase (typical for gene symbols like ``BR``).
    Three-or-more-letter values use a token-boundary regex with
    case-insensitive matching to avoid matching inside longer words.
    """
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if len(candidate) == 1:
        return None
    if len(candidate) == 2:
        if not candidate.isupper():
            return None
        match = re.search(
            rf"(?<![{_TOKEN_BOUNDARY_CHARS}]){re.escape(candidate)}(?![{_TOKEN_BOUNDARY_CHARS}])",
            text,
        )
        if not match:
            return None
        return match.start(), match.end()
    pattern = re.compile(
        rf"(?<![{_TOKEN_BOUNDARY_CHARS}]){re.escape(candidate)}(?![{_TOKEN_BOUNDARY_CHARS}])",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match is None:
        return None
    return match.start(), match.end()


def build_highlight(
    source_span: dict[str, object],
    value: str | None = None,
) -> EvidenceChainHighlight | None:
    """Build a clamped highlight payload from a stored source span.

    Source spans store document-global offsets while text_snippet is a short
    excerpt. When offsets are malformed or start beyond the snippet, locate
    value inside the snippet using a safe token-boundary search. When the value
    cannot be located, start and end collapse to 0 (no visible highlight).
    """
    if not source_span or not isinstance(source_span, dict):
        return None

    text = str(source_span.get("text_snippet") or "")
    if not text:
        return None

    text_len = len(text)
    start, start_valid = _parse_source_offset(
        source_span.get("start_offset"),
        default=0,
        name="start",
    )
    end, end_valid = _parse_source_offset(
        source_span.get("end_offset"),
        default=text_len,
        name="end",
    )
    if end < start:
        end = text_len

    # Valid starts inside the snippet should keep current behavior: clamp the
    # end to snippet bounds instead of falling through to value search.
    if start_valid and end_valid and start < text_len:
        start = max(start, 0)
        end = min(max(end, start), text_len)
    else:
        anchor = _find_value_anchor(text, value)
        if anchor is None:
            start = end = 0
        else:
            start, end = anchor

    page = source_span.get("page")
    clean_source_span = {k: v for k, v in source_span.items() if v is not None}
    return EvidenceChainHighlight(
        text=text,
        highlight_start=max(start, 0),
        highlight_end=min(max(end, 0), text_len),
        page=page if isinstance(page, int) else None,
        source_span=clean_source_span,
    )


def evidence_search_result_from_dict(row: dict[str, Any]) -> EvidenceSearchResult:
    """Rebuild an ``EvidenceSearchResult`` from the dict shape produced by
    ``variant_aggregation``. UUIDs and datetimes were serialized to strings
    during aggregation (so lexicographic sort matches the TypeScript port); we
    parse them back here for the typed API response."""
    source_document_id = row.get("source_document_id")
    canonical_evidence_id = row.get("canonical_evidence_id")
    created_at_raw = row.get("created_at")
    created_at: datetime | None = None
    if created_at_raw:
        try:
            created_at = datetime.fromisoformat(str(created_at_raw))
        except ValueError:
            created_at = None
    return EvidenceSearchResult(
        group_id=row.get("group_id") or "",
        source_document_id=UUID(str(source_document_id)) if source_document_id else UUID(int=0),
        title=row.get("title"),
        pmid=row.get("pmid"),
        doi=row.get("doi"),
        source_language=row.get("source_language"),
        gene=row.get("gene"),
        variant=row.get("variant"),
        disease=row.get("disease"),
        classification=row.get("classification"),
        field_count=row.get("field_count") or 0,
        avg_confidence=row.get("avg_confidence"),
        review_status=row.get("review_status") or "provisional",
        canonical_evidence_id=UUID(str(canonical_evidence_id)) if canonical_evidence_id else None,
        created_at=created_at,
        has_full_text=bool(row.get("has_full_text")),
        has_translation=bool(row.get("has_translation")),
    )


def pivot_group_summaries(
    detail_rows: list[Any],
    page_summary: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Pivot field-level rows into per-group summary rows for the current page."""
    groups: dict[str, dict[str, Any]] = {}
    for row in detail_rows:
        payload = row.active_payload or {}
        gid = payload.get("group_id", "")
        if not gid:
            continue

        if gid not in groups:
            summary = page_summary.get(gid, {})
            groups[gid] = {
                "group_id": gid,
                "source_document_id": summary.get("source_document_id", row.source_document_id),
                "canonical_evidence_id": summary.get("canonical_evidence_id", row.canonical_evidence_id),
                "created_at": summary.get("created_at", row.created_at),
                "review_status": summary.get("review_status", row.review_status),
                "field_count": summary.get("field_count", 0),
                "avg_confidence": summary.get("avg_confidence"),
                "gene": None,
                "variant": None,
                "disease": None,
                "classification": None,
            }

        extract_summary_field(row.field_id, payload.get("value"), groups[gid])

    # Fallback: parse gene/variant from group_id
    for group in groups.values():
        if not group["gene"]:
            group["gene"] = parse_gene_from_group_id(group["group_id"])
        if not group["variant"]:
            group["variant"] = parse_variant_from_group_id(group["group_id"])
    return groups


@dataclass
class DetailBuild:
    """Presentation outputs derived from one group's deduplicated rows."""

    items: list[EvidenceGroupItem] = field(default_factory=list)
    distribution: EvidenceFieldDistribution = field(default_factory=EvidenceFieldDistribution)
    confidences: list[float] = field(default_factory=list)
    gene: str | None = None
    variant: str | None = None
    disease: str | None = None
    classification: str | None = None


def build_group_items(rows: list[Any]) -> DetailBuild:
    """Build item rows, distribution counts, and summary fields for one group."""
    build = DetailBuild()
    for row in rows:
        payload = row.active_payload or {}
        value = coerce_str(payload.get("value"))
        field_id = row.field_id
        field_name = payload.get("field_name")
        category = payload.get("category") or category_from_field_id(field_id)
        track = payload.get("track")
        confidence = float(row.current_best_confidence) if row.current_best_confidence is not None else None
        if confidence is not None:
            build.confidences.append(confidence)

        if category:
            category_key = str(category)
            build.distribution.by_category[category_key] = build.distribution.by_category.get(category_key, 0) + 1
        build.distribution.by_field[field_id] = build.distribution.by_field.get(field_id, 0) + 1
        build.distribution.by_status[row.review_status] = build.distribution.by_status.get(row.review_status, 0) + 1
        if track:
            track_key = str(track)
            build.distribution.by_track[track_key] = build.distribution.by_track.get(track_key, 0) + 1

        if field_id in _GENE_FIELDS and not build.gene:
            build.gene = value
        elif field_id in _VARIANT_FIELDS and not build.variant:
            build.variant = value
        elif field_id in _DISEASE_FIELDS and not build.disease:
            build.disease = value
        elif field_id in _CLASSIFICATION_FIELDS and not build.classification:
            build.classification = value

        source_payload = payload.get("source")
        page = source_payload.get("page") if isinstance(source_payload, dict) else None
        build.items.append(
            EvidenceGroupItem(
                canonical_evidence_id=row.canonical_evidence_id,
                field_id=field_id,
                field_name=str(field_name) if field_name else None,
                category=str(category) if category else None,
                value=value,
                review_status=row.review_status,
                confidence=confidence,
                track=str(track) if track else None,
                page=page if isinstance(page, int) else None,
            )
        )
    return build


def build_traces(rows: list[Any]) -> list[EvidenceTrackTrace]:
    """Pair original/translated rows by fact identity into alignment traces."""
    # Build traces by matching original/translated pairs per fact identity.
    # Fact-chain rows share one fact_id across tracks via source.span_id
    # ("original-F-..." / "translated-F-..."); legacy rows without a fact
    # id keep the historical one-trace-per-field behavior.
    items_by_field: dict[tuple[str, str], list[Any]] = {}
    for row in rows:
        items_by_field.setdefault((row.field_id, row_fact_key(row)), []).append(row)

    traces: list[EvidenceTrackTrace] = []
    for (field_id, _), field_rows in items_by_field.items():
        original_row = None
        translated_row = None
        reconciled_row = None
        for row in field_rows:
            payload = row.active_payload or {}
            track = payload.get("track")
            if track == "original":
                if original_row is not None:
                    logger.debug(
                        "Duplicate original track for field_id={}: overwriting with canonical_evidence_id={}",
                        field_id,
                        row.canonical_evidence_id,
                    )
                original_row = row
            elif track == "translated":
                if translated_row is not None:
                    logger.debug(
                        "Duplicate translated track for field_id={}: overwriting with canonical_evidence_id={}",
                        field_id,
                        row.canonical_evidence_id,
                    )
                translated_row = row
            elif track == "reconciled":
                if reconciled_row is None:
                    reconciled_row = row
            else:
                logger.debug(
                    "Non-standard track value {!r} for field_id={}, "
                    "canonical_evidence_id={} — skipping in trace pairing",
                    track,
                    field_id,
                    row.canonical_evidence_id,
                )

        # Fall back to reconciled row when no original/translated exist
        if original_row is None and translated_row is None and reconciled_row is not None:
            original_row = reconciled_row

        ref_row = original_row or translated_row or reconciled_row
        if ref_row is None:
            logger.debug(
                "No usable track found for field_id={} — skipping trace",
                field_id,
            )
            continue

        original_source = (
            original_row.active_payload.get("source") if original_row and original_row.active_payload else {}
        ) or {}
        translated_source = (
            translated_row.active_payload.get("source") if translated_row and translated_row.active_payload else {}
        ) or {}
        original_value = (
            coerce_str(original_row.active_payload.get("value")) if original_row and original_row.active_payload else None
        )
        translated_value = (
            coerce_str(translated_row.active_payload.get("value"))
            if translated_row and translated_row.active_payload
            else None
        )

        original = build_highlight(original_source, original_value) if original_source is not None else None
        translated = (
            build_highlight(translated_source, translated_value) if translated_source is not None else None
        )

        # Fall back to reconciled row's highlight when original/translated
        # sources are non-dict (e.g. "benchmark_ground_truth" strings)
        # and produce no usable highlight.
        if original is None and translated is None and reconciled_row is not None:
            rec_payload = reconciled_row.active_payload or {}
            rec_source = rec_payload.get("source")
            if isinstance(rec_source, dict):
                rec_value = coerce_str(rec_payload.get("value"))
                original = build_highlight(rec_source, rec_value)
                original_value = original_value or rec_value

        canonical_id = ref_row.canonical_evidence_id
        field_name = ref_row.active_payload.get("field_name") if ref_row.active_payload else None

        traces.append(
            EvidenceTrackTrace(
                canonical_evidence_id=canonical_id,
                field_id=field_id,
                field_name=str(field_name) if field_name else None,
                original_value=original_value,
                translated_value=translated_value,
                original=original,
                translated=translated,
                alignment_confidence=1.0 if original and translated else None,
            )
        )
    return traces
