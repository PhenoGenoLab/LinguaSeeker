"""Review query ports (evidence search and group detail)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.core.tools.review.contracts import (
    BilingualSpan,
    EvidenceGroupDetailResponse,
    EvidenceSearchResponse,
    TrackSpan,
    VariantSearchResponse,
)


class SourceLinkStore(Protocol):
    """Read source spans for evidence traceability."""

    async def get_track_span(
        self,
        *,
        canonical_evidence_id: UUID,
        track: str,
        owner_user_id: UUID | str | None = None,
    ) -> TrackSpan | None: ...

    async def get_bilingual_span(
        self,
        *,
        canonical_evidence_id: UUID,
        owner_user_id: UUID | str | None = None,
    ) -> BilingualSpan: ...


class EvidenceQueryStore(Protocol):
    """Read-only evidence queries used by the review API."""

    async def group_detail(
        self,
        *,
        group_id: str | None,
        source_document_id: str | None,
        owner_user_id: UUID | str | None,
    ) -> EvidenceGroupDetailResponse: ...

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
        owner_user_id: UUID | str | None = None,
    ) -> EvidenceSearchResponse: ...

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
    ) -> VariantSearchResponse: ...
