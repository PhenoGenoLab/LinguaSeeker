"""SQL persistence for evidence search rows and document metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.tools.review.search_blocks import (
    coerce_str,
    extract_source_language,
    extract_source_language_from_state,
)
from src.dao.postgresql.models import (
    CanonicalEvidenceItem,
    PipelineRunState,
    SourceDocument,
    SourceDocumentIdentifier,
)

from src.core.tools.review.search_fields import (
    DISEASE_FIELDS,
    GENE_FIELDS,
    VARIANT_FIELDS,
)


@dataclass(frozen=True)
class PageGroupRow:
    """Aggregated row for one evidence group in the current page."""

    group_id: str
    field_count: int
    avg_confidence: float | None
    canonical_evidence_id: UUID | None
    source_document_id: UUID
    review_status: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class PageGroups:
    """One page of grouped evidence rows plus the unpaginated total."""

    total: int
    rows: tuple[PageGroupRow, ...]


@dataclass(frozen=True)
class DocumentMetadata:
    """Document identifiers, titles, languages, and availability flags."""

    identifiers: dict[str, dict[str, str]]
    titles: dict[str, str]
    languages: dict[str, str]
    availability: dict[str, dict[str, bool]]


@dataclass(frozen=True)
class DocumentSnapshot:
    """Full document payload used by the group-detail response."""

    identifiers: dict[str, str]
    raw_metadata: dict[str, Any]
    original_text: str | None
    translated_text: str | None
    original_blocks: list[dict] | None
    translated_blocks: list[dict] | None


class EvidenceSearchRepository:
    """Read queries behind evidence search and group detail."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def matching_group_ids(
        self,
        *,
        owner_id: UUID | None,
        gene: str | None,
        variant: str | None,
        disease: str | None,
    ) -> set[str] | None:
        """Return group ids matching every supplied summary filter, or None."""
        group_id_expr = CanonicalEvidenceItem.active_payload["group_id"].astext
        owner_filter = self._owner_filter(owner_id)

        # Build per-filter group_id sets, then intersect (AND across filters).
        # Each filter targets a disjoint field_id domain (gene vs variant vs disease),
        # so they must be queried independently — ANDing them in one WHERE clause
        # would require field_id to match multiple domains simultaneously.
        per_filter_clauses = []
        if gene:
            per_filter_clauses.append(
                and_(
                    CanonicalEvidenceItem.field_id.in_(GENE_FIELDS),
                    CanonicalEvidenceItem.active_payload["value"].astext.ilike(f"%{gene}%"),
                )
            )
        if variant:
            per_filter_clauses.append(
                and_(
                    CanonicalEvidenceItem.field_id.in_(VARIANT_FIELDS),
                    CanonicalEvidenceItem.active_payload["value"].astext.ilike(f"%{variant}%"),
                )
            )
        if disease:
            per_filter_clauses.append(
                and_(
                    CanonicalEvidenceItem.field_id.in_(DISEASE_FIELDS),
                    CanonicalEvidenceItem.active_payload["value"].astext.ilike(f"%{disease}%"),
                )
            )

        if not per_filter_clauses:
            return None

        matching: set[str] | None = None
        for clause in per_filter_clauses:
            filter_stmt = select(group_id_expr).where(owner_filter, clause).group_by(group_id_expr)
            result = await self._session.execute(filter_stmt)
            ids = {row[0] for row in result.all() if row[0]}
            matching = ids if matching is None else matching & ids
        return matching

    async def page_groups(
        self,
        *,
        owner_id: UUID | None,
        matching_group_ids: set[str] | None,
        page: int,
        page_size: int,
    ) -> PageGroups:
        """Return one page of aggregated groups and the total group count."""
        from sqlalchemy import func as sa_func
        from sqlalchemy.dialects.postgresql.ext import aggregate_order_by

        group_id_expr = CanonicalEvidenceItem.active_payload["group_id"].astext
        owner_filter = self._owner_filter(owner_id)

        # ── Pass 1: DB-level GROUP BY + pagination ────────────────
        #
        # The inner query aggregates per-group rows. UUID-typed columns
        # (canonical_evidence_id) and status strings (review_status) cannot
        # be reduced with `min()` / `max()` (no PG ordering for UUID), so
        # we capture them as `array_agg(x ORDER BY created_at)` arrays.
        # The outer SELECT indexes those arrays at [1] to pick the oldest
        # row's value as the representative — a form PostgreSQL actually
        # accepts (unlike `CAST(... AS UUID[])[1]`, which is a syntax
        # error because the cast needs parentheses before indexing).
        inner = (
            select(
                group_id_expr.label("group_id"),
                sa_func.count().label("field_count"),
                sa_func.avg(CanonicalEvidenceItem.current_best_confidence).label("avg_confidence"),
                sa_func.array_agg(
                    aggregate_order_by(
                        CanonicalEvidenceItem.canonical_evidence_id,
                        CanonicalEvidenceItem.created_at.asc(),
                    )
                ).label("canonical_ids"),
                CanonicalEvidenceItem.source_document_id.label("source_document_id"),
                sa_func.array_agg(
                    aggregate_order_by(
                        CanonicalEvidenceItem.review_status,
                        CanonicalEvidenceItem.created_at.asc(),
                    )
                ).label("review_statuses"),
                sa_func.max(CanonicalEvidenceItem.created_at).label("created_at"),
            )
            .where(owner_filter)
            .group_by(
                group_id_expr,
                CanonicalEvidenceItem.source_document_id,
            )
            .having(group_id_expr.isnot(None))
            .having(group_id_expr != "")
        )
        if matching_group_ids is not None:
            inner = inner.where(group_id_expr.in_(matching_group_ids))

        sub = inner.subquery()
        page_query = select(
            sub.c.group_id,
            sub.c.field_count,
            sub.c.avg_confidence,
            sub.c.canonical_ids[1].label("canonical_evidence_id"),
            sub.c.source_document_id,
            sub.c.review_statuses[1].label("review_status"),
            sub.c.created_at,
        )

        count_sub = page_query.subquery()
        count_stmt = select(sa_func.count()).select_from(count_sub)
        total = (await self._session.execute(count_stmt)).scalar_one()

        if total == 0:
            return PageGroups(total=0, rows=())

        offset = (page - 1) * page_size
        page_query = page_query.order_by(sub.c.group_id).offset(offset).limit(page_size)
        page_result = await self._session.execute(page_query)
        rows = tuple(
            PageGroupRow(
                group_id=row.group_id,
                field_count=row.field_count,
                avg_confidence=float(row.avg_confidence) if row.avg_confidence else None,
                canonical_evidence_id=row.canonical_evidence_id,
                source_document_id=row.source_document_id,
                review_status=row.review_status,
                created_at=row.created_at,
            )
            for row in page_result.all()
        )
        return PageGroups(total=total, rows=rows)

    async def detail_rows(self, *, owner_id: UUID | None, group_ids: list[str]) -> list[Any]:
        """Fetch field-level rows for the current page's groups."""
        group_id_expr = CanonicalEvidenceItem.active_payload["group_id"].astext
        detail_stmt = (
            select(
                CanonicalEvidenceItem.canonical_evidence_id,
                CanonicalEvidenceItem.source_document_id,
                CanonicalEvidenceItem.field_id,
                CanonicalEvidenceItem.review_status,
                CanonicalEvidenceItem.current_best_confidence,
                CanonicalEvidenceItem.active_payload,
                CanonicalEvidenceItem.created_at,
            )
            .where(self._owner_filter(owner_id), group_id_expr.in_(group_ids))
            .order_by(group_id_expr, CanonicalEvidenceItem.field_id)
        )
        result = await self._session.execute(detail_stmt)
        return list(result.all())

    async def document_metadata(
        self,
        *,
        doc_ids: set[UUID],
        owner_id: UUID | None,
    ) -> DocumentMetadata:
        """Batch-load identifiers, titles, languages, and availability flags.

        Only ``raw_metadata`` plus DB-side availability flags are fetched here -
        the large ``original_text`` / ``translated_text`` / ``original_blocks``
        / ``translated_blocks`` columns are deliberately excluded. Full-text
        language detection is deferred to the single-document detail endpoint;
        the list view resolves ``source_language`` from persisted metadata only.
        """
        identifiers: dict[str, dict[str, str]] = {}
        titles: dict[str, str] = {}
        languages: dict[str, str] = {}
        availability: dict[str, dict[str, bool]] = {}
        if not doc_ids:
            return DocumentMetadata(identifiers, titles, languages, availability)

        ident_stmt = select(SourceDocumentIdentifier).where(
            SourceDocumentIdentifier.source_document_id.in_(doc_ids)
        )
        ident_result = await self._session.execute(ident_stmt)
        for ident in ident_result.scalars():
            identifiers.setdefault(str(ident.source_document_id), {})
            identifiers[str(ident.source_document_id)][ident.identifier_type] = ident.identifier_value

        # DB-side availability flags avoid pulling the large text/blocks
        # columns into Python just to check for non-emptiness.
        has_full_text_expr = or_(
            SourceDocument.original_text.isnot(None),
            SourceDocument.original_blocks.isnot(None),
        )
        has_translation_expr = or_(
            SourceDocument.translated_text.isnot(None),
            SourceDocument.translated_blocks.isnot(None),
        )
        metadata_stmt = select(
            SourceDocument.source_document_id,
            SourceDocument.raw_metadata,
            SourceDocument.source_language,
            has_full_text_expr.label("has_full_text"),
            has_translation_expr.label("has_translation"),
        ).where(SourceDocument.source_document_id.in_(doc_ids))
        metadata_result = await self._session.execute(metadata_stmt)
        for row in metadata_result.all():
            raw_metadata = row.raw_metadata or {}
            doc_key = str(row.source_document_id)
            title = coerce_str(raw_metadata.get("title")) if isinstance(raw_metadata, dict) else None
            if title:
                titles[doc_key] = title
            # Prefer the materialized column; fall back to parsing
            # raw_metadata so documents not yet backfilled still resolve.
            source_language = row.source_language or extract_source_language(raw_metadata)
            if source_language:
                languages[doc_key] = source_language
            availability[doc_key] = {
                "has_full_text": bool(row.has_full_text),
                "has_translation": bool(row.has_translation),
            }

        missing_language_doc_ids = [doc_id for doc_id in doc_ids if str(doc_id) not in languages]
        if missing_language_doc_ids:
            run_state_stmt = (
                select(
                    PipelineRunState.source_document_id,
                    PipelineRunState.state_json,
                )
                .where(
                    PipelineRunState.source_document_id.in_(missing_language_doc_ids),
                    self._owner_filter(owner_id, model=PipelineRunState),
                )
                .order_by(PipelineRunState.created_at.desc())
            )
            run_state_result = await self._session.execute(run_state_stmt)
            for row in run_state_result.all():
                doc_key = str(row.source_document_id)
                if doc_key in languages:
                    continue
                source_language = extract_source_language_from_state(row.state_json)
                if source_language:
                    languages[doc_key] = source_language

        return DocumentMetadata(identifiers, titles, languages, availability)

    async def group_rows(
        self,
        *,
        group_id: str | None,
        source_document_id: str | None,
        owner_id: UUID | None,
    ) -> list[Any]:
        """Fetch canonical rows for one group/document detail request."""
        conditions: list[Any] = [self._owner_filter(owner_id)]
        if group_id:
            conditions.append(
                CanonicalEvidenceItem.active_payload["group_id"].astext == group_id,
            )
        if source_document_id:
            conditions.append(
                CanonicalEvidenceItem.source_document_id == source_document_id,
            )
        stmt = (
            select(
                CanonicalEvidenceItem.canonical_evidence_id,
                CanonicalEvidenceItem.source_document_id,
                CanonicalEvidenceItem.field_id,
                CanonicalEvidenceItem.review_status,
                CanonicalEvidenceItem.current_best_confidence,
                CanonicalEvidenceItem.active_payload,
                CanonicalEvidenceItem.updated_at,
            )
            .where(*conditions)
            .order_by(CanonicalEvidenceItem.field_id)
        )
        result = await self._session.execute(stmt)
        return list(result.all())

    async def document_snapshot(self, source_document_id: UUID) -> DocumentSnapshot:
        """Load identifiers and the full document payload for one document."""
        ident_stmt = select(SourceDocumentIdentifier).where(
            SourceDocumentIdentifier.source_document_id == source_document_id
        )
        ident_result = await self._session.execute(ident_stmt)
        identifiers = {ident.identifier_type: ident.identifier_value for ident in ident_result.scalars().all()}

        metadata_stmt = select(
            SourceDocument.raw_metadata,
            SourceDocument.original_text,
            SourceDocument.translated_text,
            SourceDocument.original_blocks,
            SourceDocument.translated_blocks,
        ).where(SourceDocument.source_document_id == source_document_id)
        metadata_result = await self._session.execute(metadata_stmt)
        metadata_row = metadata_result.one_or_none()
        return DocumentSnapshot(
            identifiers=identifiers,
            raw_metadata=(metadata_row[0] if metadata_row else None) or {},
            original_text=metadata_row[1] if metadata_row else None,
            translated_text=metadata_row[2] if metadata_row else None,
            original_blocks=metadata_row[3] if metadata_row else None,
            translated_blocks=metadata_row[4] if metadata_row else None,
        )

    async def latest_state_json(self, *, source_document_id: UUID, owner_id: UUID | None) -> Any:
        """Return the newest pipeline state JSON for one document."""
        run_state_stmt = (
            select(PipelineRunState.state_json)
            .where(
                PipelineRunState.source_document_id == source_document_id,
                self._owner_filter(owner_id, model=PipelineRunState),
            )
            .order_by(PipelineRunState.created_at.desc())
            .limit(1)
        )
        run_state_result = await self._session.execute(run_state_stmt)
        return run_state_result.scalar_one_or_none()

    @staticmethod
    def _owner_filter(owner_id: UUID | None, *, model: Any = CanonicalEvidenceItem) -> Any:
        """Return the owner-scoped WHERE clause used by search queries."""
        return model.owner_user_id.is_(None) if owner_id is None else model.owner_user_id == owner_id
