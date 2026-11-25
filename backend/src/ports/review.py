"""Review query ports (evidence search and group detail)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from src.core.tools.review.contracts import (
    BilingualSpan,
    DeltaEntry,
    EvidenceGroupDetailResponse,
    EvidencePatchRequest,
    EvidenceSearchResponse,
    ReviewStatus,
    TrackSpan,
    VariantSearchResponse,
)


@dataclass(frozen=True)
class PatchResult:
    """Result of one evidence patch."""

    canonical_evidence_id: UUID
    old_status: ReviewStatus
    new_status: ReviewStatus
    deltas: int
    field_deltas: list[DeltaEntry]


@dataclass(frozen=True)
class AuditEventRecord:
    """One audit event without persistence types."""

    review_event_id: UUID
    canonical_evidence_id: UUID
    reviewer_id: UUID | None
    target_type: str
    old_status: str | None
    new_status: str | None
    field_deltas: list[dict[str, Any]]
    change_reason: str | None
    created_at: datetime | None


class FeedbackStore(Protocol):
    """Apply one evidence patch as a single transaction."""

    async def patch_evidence(
        self,
        *,
        canonical_evidence_id: UUID,
        patch: EvidencePatchRequest,
        reviewer_id: UUID | None = None,
        owner_user_id: UUID | str | None = None,
    ) -> PatchResult: ...


class AuditStore(Protocol):
    """Read review audit events."""

    async def list_events(
        self,
        *,
        canonical_evidence_id: UUID | None = None,
        source_document_id: UUID | None = None,
        reviewer_id: UUID | None = None,
        owner_user_id: UUID | str | None = None,
        limit: int = 100,
    ) -> list[AuditEventRecord]: ...


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
