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
    LiteratureProfileDetailResponse,
    LiteratureRefreshResponse,
    LiteratureSearchResponse,
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


class LiteratureStore(Protocol):
    """Literature profile queries used by the review API."""

    async def search(
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
    ) -> "LiteratureSearchResponse": ...

    async def detail(
        self,
        source_document_id: UUID,
        *,
        owner_user_id: UUID | str | None = None,
    ) -> "LiteratureProfileDetailResponse | None": ...

    async def refresh_all(self, *, owner_user_id: UUID | str | None = None) -> "LiteratureRefreshResponse": ...


@dataclass(frozen=True)
class AnnotationRecord:
    """One annotation row without persistence types."""

    id: UUID
    source_document_id: UUID
    track: str
    paragraph_id: str
    start_offset: int
    end_offset: int
    color: str | None
    note: str | None
    author: str | None
    created_at: datetime
    updated_at: datetime


class AnnotationStore(Protocol):
    """CRUD for document annotations."""

    async def list_annotations(
        self,
        source_document_id: UUID,
        *,
        track: str | None,
        owner_user_id: UUID | None,
    ) -> list[AnnotationRecord]: ...

    async def get_annotation(
        self,
        annotation_id: UUID,
        *,
        owner_user_id: UUID | None,
    ) -> AnnotationRecord | None: ...

    async def create_annotation(
        self,
        source_document_id: UUID,
        *,
        track: str,
        paragraph_id: str,
        start_offset: int,
        end_offset: int,
        color: str | None,
        note: str | None,
        author: str | None,
        owner_user_id: UUID | None,
    ) -> AnnotationRecord: ...

    async def update_annotation(
        self,
        annotation_id: UUID,
        *,
        color: str | None,
        note: str | None,
        update_color: bool,
        update_note: bool,
        owner_user_id: UUID | None,
    ) -> AnnotationRecord: ...

    async def delete_annotation(self, annotation_id: UUID, *, owner_user_id: UUID | None) -> None: ...


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
