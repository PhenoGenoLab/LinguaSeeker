"""Evidence search service with field-level pivoting."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.text.content import parse_gene_from_group_id, parse_variant_from_group_id
from src.utils.text.render_quality import (
    is_likely_untranslated_render_blocks,
    is_likely_untranslated_render_payload,
)

from src.core.tools.review.contracts import (
    EvidenceGroupDetailResponse,
    EvidenceSearchResponse,
    EvidenceSearchResult,
    GroupDocumentPair,
    ReviewProgressResponse,
    VariantIndexEntryResponse,
    VariantSearchCandidatesResponse,
    VariantSearchResponse,
    VariantSearchStatsResponse,
)
from src.dao.postgresql.review.evidence_search_repository import EvidenceSearchRepository
from src.core.tools.review.search_blocks import (
    coerce_str,
    detect_source_language_from_text,
    extract_source_language,
    extract_source_language_from_state,
    filter_body_blocks,
    filter_body_text,
    load_full_document_blocks,
    load_full_document_text,
    load_translation_alignment,
    row_fact_key,
)
from src.core.tools.review.search_presentation import (
    build_group_items,
    build_traces,
    evidence_search_result_from_dict,
    pivot_group_summaries,
)
from src.core.tools.review.variant_aggregation import (
    VariantIndexFilters as _VariantIndexFilters,
    aggregate_variants,
    filter_and_paginate_variants,
)

# Page size used when fetching the full evidence-group corpus for server-side
# variant aggregation. This cap bounds a single request's memory; crossing it
# means aggregation must move into SQL (GROUP BY on the variant slug).
_VARIANT_AGGREGATE_MAX_ROWS = 50_000


class VariantAggregationLimitError(RuntimeError):
    """Raised when the evidence corpus exceeds the in-memory aggregation cap."""


class SearchService:
    """Search evidence cards grouped by group_id, pivoting field-level extractions."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._repository = EvidenceSearchRepository(session)

    async def search_evidence(
        self,
        *,
        gene: str | None = None,
        variant: str | None = None,
        disease: str | None = None,
        pmid: str | None = None,
        doi: str | None = None,
        page: int = 1,
        page_size: int = 50,
        owner_user_id: str | UUID | None = None,
    ) -> EvidenceSearchResponse:
        """Search evidence with optional filters and DB-level pagination.

        Groups field-level extractions by group_id and pivots them into
        summary rows with gene/variant/disease/classification columns.
        Uses a two-pass approach:
        1. DB-level GROUP BY + OFFSET/LIMIT to get current page group_ids
        2. Fetch details only for those groups (small bounded set)
        """
        owner_id = UUID(str(owner_user_id)) if owner_user_id else None
        matching_group_ids = await self._repository.matching_group_ids(
            owner_id=owner_id,
            gene=gene,
            variant=variant,
            disease=disease,
        )
        if matching_group_ids is not None and not matching_group_ids:
            return EvidenceSearchResponse(items=[], total=0, page=page, page_size=page_size)

        page_groups = await self._repository.page_groups(
            owner_id=owner_id,
            matching_group_ids=matching_group_ids,
            page=page,
            page_size=page_size,
        )
        if page_groups.total == 0:
            return EvidenceSearchResponse(items=[], total=0, page=page, page_size=page_size)
        if not page_groups.rows:
            return EvidenceSearchResponse(items=[], total=page_groups.total, page=page, page_size=page_size)

        page_group_ids = [row.group_id for row in page_groups.rows]
        page_summary: dict[str, dict[str, Any]] = {
            row.group_id: {
                "field_count": row.field_count,
                "avg_confidence": row.avg_confidence,
                "canonical_evidence_id": row.canonical_evidence_id,
                "source_document_id": row.source_document_id,
                "review_status": row.review_status,
                "created_at": row.created_at,
            }
            for row in page_groups.rows
        }

        detail_rows = await self._repository.detail_rows(owner_id=owner_id, group_ids=page_group_ids)
        groups = pivot_group_summaries(detail_rows, page_summary)

        metadata = await self._repository.document_metadata(
            doc_ids={group["source_document_id"] for group in groups.values()},
            owner_id=owner_id,
        )

        # Build results (apply PMID/DOI post-filters)
        items: list[EvidenceSearchResult] = []
        filtered_total = page_groups.total
        for group_id in page_group_ids:
            group = groups.get(group_id)
            if not group:
                continue

            doc_ident = metadata.identifiers.get(str(group["source_document_id"]), {})
            if pmid and pmid not in doc_ident.get("pmid", ""):
                filtered_total -= 1
                continue
            if doi and doi.lower() not in doc_ident.get("doi", "").lower():
                filtered_total -= 1
                continue

            availability = metadata.availability.get(str(group["source_document_id"]), {})
            items.append(
                EvidenceSearchResult(
                    group_id=group["group_id"],
                    source_document_id=group["source_document_id"],
                    title=metadata.titles.get(str(group["source_document_id"])),
                    pmid=doc_ident.get("pmid"),
                    doi=doc_ident.get("doi"),
                    source_language=metadata.languages.get(str(group["source_document_id"])),
                    gene=group["gene"],
                    variant=group["variant"],
                    disease=group["disease"],
                    classification=group["classification"],
                    field_count=group["field_count"],
                    avg_confidence=group["avg_confidence"],
                    review_status=group["review_status"],
                    canonical_evidence_id=group["canonical_evidence_id"],
                    created_at=group["created_at"],
                    has_full_text=availability.get("has_full_text", False),
                    has_translation=availability.get("has_translation", False),
                )
            )

        return EvidenceSearchResponse(
            items=items,
            total=filtered_total if (pmid or doi) else page_groups.total,
            page=page,
            page_size=page_size,
        )

    async def search_variants(
        self,
        *,
        gene: str | None = None,
        variant: str | None = None,
        disease: str | None = None,
        classification: str | None = None,
        review_status: str | None = None,
        source_language: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = None,
        page: int = 1,
        page_size: int = 24,
        owner_user_id: UUID | None = None,
    ) -> "VariantSearchResponse":
        """Return a page of variant-centric rows with aggregate stats.

        The variant index groups evidence rows by ``gene:variant[:disease]``
        slug. Aggregation, filtering, sorting, and pagination all happen
        server-side so the browser only receives the current page. The full
        evidence-group corpus is fetched internally (no per-request cap) via
        ``search_evidence`` and handed to the pure aggregation module.
        """
        # Fetch every evidence-group row in one shot. The corpus is small
        # enough (~10^3 groups) that a single server-side pass is far cheaper
        # than shipping the full set to the browser. Filters are applied at
        # the variant level after aggregation, matching the previous
        # client-side behaviour.
        all_groups = await self.search_evidence(
            page=1,
            page_size=_VARIANT_AGGREGATE_MAX_ROWS,
            owner_user_id=owner_user_id,
        )
        if all_groups.total > _VARIANT_AGGREGATE_MAX_ROWS:
            raise VariantAggregationLimitError(
                f"Variant aggregation requires SQL pushdown: {all_groups.total} groups "
                f"exceed the {_VARIANT_AGGREGATE_MAX_ROWS}-row in-memory cap"
            )

        entries = aggregate_variants(all_groups.items)
        filters = _VariantIndexFilters(
            gene=gene,
            variant=variant,
            disease=disease,
            classification=classification,
            review_status=review_status,
            source_language=source_language,
            sort_by=sort_by,
            sort_order=sort_order or "desc",
            page=max(page, 1),
            page_size=max(page_size, 1),
        )
        data = filter_and_paginate_variants(entries, filters)

        item_models = [
            VariantIndexEntryResponse(
                variant_slug=e.variant_slug,
                gene=e.gene,
                variant=e.variant,
                disease=e.disease,
                classification=e.classification,
                classification_level=e.classification_level,
                evidence_group_count=e.evidence_group_count,
                literature_count=e.literature_count,
                avg_confidence=e.avg_confidence,
                field_count=e.field_count,
                category_distribution=e.category_distribution,
                review_status=e.review_status,
                review_progress=ReviewProgressResponse(
                    total=e.review_progress["total"],
                    reviewed=e.review_progress["reviewed"],
                    approved=e.review_progress["approved"],
                    corrected=e.review_progress["corrected"],
                    rejected=e.review_progress["rejected"],
                    provisional=e.review_progress["provisional"],
                    reviewed_percent=e.review_progress["reviewedPercent"],
                ),
                created_at=e.created_at,
                group_ids=e.group_ids,
                source_document_ids=e.source_document_ids,
                source_languages=e.source_languages,
                group_document_pairs=[
                    GroupDocumentPair(
                        group_id=p["groupId"],
                        source_document_id=p["sourceDocumentId"],
                    )
                    for p in e.group_document_pairs
                ],
                representative=evidence_search_result_from_dict(e.representative),
            )
            for e in data.items
        ]

        return VariantSearchResponse(
            items=item_models,
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            stats=VariantSearchStatsResponse(
                total_variants=data.stats.total_variants,
                total_evidence_groups=data.stats.total_evidence_groups,
                total_literature=data.stats.total_literature,
                avg_confidence=data.stats.avg_confidence,
                classification_distribution=data.stats.classification_distribution,
            ),
            candidates=VariantSearchCandidatesResponse(
                genes=data.candidates.genes,
                variants=data.candidates.variants,
                diseases=data.candidates.diseases,
            ),
        )

    async def get_group_detail(
        self,
        *,
        group_id: str | None = None,
        source_document_id: str | None = None,
        owner_user_id: str | UUID | None = None,
    ) -> EvidenceGroupDetailResponse:
        """Return detail payload for one grouped evidence row.

        At least one of *group_id* or *source_document_id* must be given.
        When only *source_document_id* is provided the method picks the
        first ``group_id`` found for that document.  This is required
        because ``group_id`` values are not unique per source document —
        the same ``gene=<G>|variant=<V>`` string can appear across many
        papers.
        """
        owner_id = UUID(str(owner_user_id)) if owner_user_id else None
        rows = await self._repository.group_rows(
            group_id=group_id,
            source_document_id=source_document_id,
            owner_id=owner_id,
        )
        if not rows:
            raise NoResultFound()

        # Deduplicate by (field_id, track): keep the most recently updated row
        # to avoid "Duplicate track" warnings from the trace-building loop.
        seen: dict[tuple[str, str, str], int] = {}
        deduped_rows = []
        for row in sorted(rows, key=lambda r: r.updated_at or "", reverse=True):
            track = (row.active_payload or {}).get("track", "original")
            key = (row.field_id, track, row_fact_key(row))
            if key not in seen:
                seen[key] = 1
                deduped_rows.append(row)
        rows = deduped_rows

        # If group_id was not provided, extract it from the first row
        if not group_id:
            group_id = (rows[0].active_payload or {}).get("group_id", "")

        resolved_document_id = rows[0].source_document_id
        snapshot = await self._repository.document_snapshot(resolved_document_id)
        raw_metadata = snapshot.raw_metadata
        title = coerce_str(raw_metadata.get("title")) if isinstance(raw_metadata, dict) else None
        source_language = extract_source_language(raw_metadata)

        # Look up fact_chain output_dir from persisted pipeline state
        fact_chain_output_dir: str | None = None
        state_json = await self._repository.latest_state_json(
            source_document_id=resolved_document_id,
            owner_id=owner_id,
        )
        if isinstance(state_json, dict):
            fact_chain_output = state_json.get("fact_chain_output")
            if not isinstance(fact_chain_output, dict):
                # Legacy pre-4-phase-split states stored translation under parsing
                fact_chain_output = state_json.get("parsing_output")
            if isinstance(fact_chain_output, dict):
                fact_chain_output_dir = fact_chain_output.get("output_dir")
            source_language = source_language or extract_source_language_from_state(state_json)

        build = build_group_items(rows)
        traces = build_traces(rows)

        # Fallback: parse gene/variant from group_id if field-level extraction missed them
        gene = build.gene
        variant = build.variant
        if not gene and group_id:
            gene = parse_gene_from_group_id(group_id)
        if not variant and group_id:
            variant = parse_variant_from_group_id(group_id)

        identifiers = snapshot.identifiers
        loaded_original_text = snapshot.original_text or load_full_document_text(
            resolved_document_id,
            track="original",
            identifiers=identifiers,
            known_output_dir=fact_chain_output_dir,
        )
        if source_language is None:
            source_language = detect_source_language_from_text(loaded_original_text)

        usable_db_translated_text = None
        if snapshot.translated_text and not is_likely_untranslated_render_payload(
            source_language=source_language,
            original_text=loaded_original_text,
            translated_text=snapshot.translated_text,
        ):
            usable_db_translated_text = snapshot.translated_text
        loaded_translated_text = usable_db_translated_text or load_full_document_text(
            resolved_document_id,
            track="translated",
            identifiers=identifiers,
            known_output_dir=fact_chain_output_dir,
        )
        loaded_original_blocks = snapshot.original_blocks or load_full_document_blocks(
            resolved_document_id,
            track="original",
            identifiers=identifiers,
            known_output_dir=fact_chain_output_dir,
        )
        usable_db_translated_blocks = None
        if snapshot.translated_blocks and not is_likely_untranslated_render_blocks(
            source_language=source_language,
            original_blocks=loaded_original_blocks,
            translated_blocks=snapshot.translated_blocks,
        ):
            usable_db_translated_blocks = snapshot.translated_blocks
        loaded_translated_blocks = usable_db_translated_blocks or load_full_document_blocks(
            resolved_document_id,
            track="translated",
            identifiers=identifiers,
            known_output_dir=fact_chain_output_dir,
        )
        if is_likely_untranslated_render_payload(
            source_language=source_language,
            original_text=loaded_original_text,
            translated_text=loaded_translated_text,
        ):
            loaded_translated_text = None
        if is_likely_untranslated_render_blocks(
            source_language=source_language,
            original_blocks=loaded_original_blocks,
            translated_blocks=loaded_translated_blocks,
        ):
            loaded_translated_blocks = None
        original_document_text = filter_body_text(loaded_original_text)
        translated_document_text = filter_body_text(loaded_translated_text)
        original_blocks = filter_body_blocks(loaded_original_blocks, original_document_text)
        translated_blocks = filter_body_blocks(loaded_translated_blocks, translated_document_text)
        translation_alignment = load_translation_alignment(
            resolved_document_id,
            raw_metadata,
            identifiers=identifiers,
            known_output_dir=fact_chain_output_dir,
        )

        return EvidenceGroupDetailResponse(
            group_id=group_id,
            source_document_id=resolved_document_id,
            title=title,
            pmid=identifiers.get("pmid"),
            doi=identifiers.get("doi"),
            original_document_text=original_document_text,
            translated_document_text=translated_document_text,
            original_blocks=original_blocks,
            translated_blocks=translated_blocks,
            gene=gene,
            variant=variant,
            disease=build.disease,
            classification=build.classification,
            item_count=len(build.items),
            avg_confidence=(sum(build.confidences) / len(build.confidences)) if build.confidences else None,
            distribution=build.distribution,
            items=build.items,
            traces=traces,
            translation_alignment=translation_alignment,
        )
