"""Evidence review, feedback, and search routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import NoResultFound
from starlette.requests import Request

from src.api.auth import get_current_account
from src.api.deps import get_evidence_store, get_feedback_store, get_literature_store
from src.api.rate_limit import limiter
from src.core.foundation.auth.contracts import AuthContext
from src.ports.review import EvidenceQueryStore, FeedbackStore, LiteratureStore
from src.core.tools.review.contracts import (
    EvidenceGroupDetailResponse,
    EvidencePatchRequest,
    EvidenceSearchResponse,
    LiteratureProfileDetailResponse,
    LiteratureRefreshResponse,
    LiteratureSearchResponse,
    PatchResultResponse,
    VariantSearchResponse,
)

router = APIRouter()


@router.get("/groups/detail", response_model=EvidenceGroupDetailResponse)
async def get_evidence_group_detail(
    group_id: str | None = Query(None, description="Evidence group identifier"),
    source_document_id: UUID | None = Query(None, description="Source document UUID to scope results"),
    store: EvidenceQueryStore = Depends(get_evidence_store),
    account: AuthContext = Depends(get_current_account),
) -> EvidenceGroupDetailResponse:
    """Return grouped evidence detail with distribution and traceability.

    At least one of *group_id* or *source_document_id* must be provided.
    When only *source_document_id* is given, the service picks the first
    group found for that document.
    """
    if not group_id and not source_document_id:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of group_id or source_document_id",
        )
    try:
        return await store.group_detail(
            group_id=group_id,
            source_document_id=str(source_document_id) if source_document_id else None,
            owner_user_id=account.owner_user_id,
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Evidence group not found")


@router.patch("/{canonical_evidence_id}", response_model=PatchResultResponse)
@limiter.limit("30/minute")
async def patch_evidence(
    request: Request,
    canonical_evidence_id: UUID,
    body: EvidencePatchRequest,
    feedback: FeedbackStore = Depends(get_feedback_store),
    account: AuthContext = Depends(get_current_account),
) -> PatchResultResponse:
    """Apply a patch to an evidence card and record audit event."""
    try:
        result = await feedback.patch_evidence(
            canonical_evidence_id=canonical_evidence_id,
            patch=body,
            reviewer_id=account.owner_user_id,
            owner_user_id=account.owner_user_id,
        )
        return PatchResultResponse(
            canonical_evidence_id=result.canonical_evidence_id,
            old_status=result.old_status,
            new_status=result.new_status,
            deltas=result.deltas,
            field_deltas=result.field_deltas,
        )
    except NoResultFound:
        raise HTTPException(status_code=404, detail="Evidence not found")


@router.get("/search", response_model=EvidenceSearchResponse)
async def search_evidence(
    store: EvidenceQueryStore = Depends(get_evidence_store),
    account: AuthContext = Depends(get_current_account),
    gene: str | None = Query(None, description="Filter by gene (partial match on A.gene_symbol)"),
    variant: str | None = Query(None, description="Filter by variant (partial match on HGVS fields)"),
    disease: str | None = Query(None, description="Filter by disease (partial match on diagnosis fields)"),
    pmid: str | None = Query(None, description="Filter by PMID (exact match)"),
    doi: str | None = Query(None, description="Filter by DOI (partial match)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
) -> EvidenceSearchResponse:
    """Search evidence cards with field-level pivoting and pagination.

    Groups field-level extractions by group_id and pivots them into summary
    rows with gene/variant/disease/classification columns.
    """
    return await store.search_evidence(
        gene=gene,
        variant=variant,
        disease=disease,
        pmid=pmid,
        doi=doi,
        page=page,
        page_size=page_size,
        owner_user_id=account.owner_user_id,
    )


@router.get("/variants", response_model=VariantSearchResponse)
async def search_variants(
    store: EvidenceQueryStore = Depends(get_evidence_store),
    account: AuthContext = Depends(get_current_account),
    gene: str | None = Query(None, description="Filter variants by gene (partial, case-insensitive)"),
    variant: str | None = Query(None, description="Filter variants by variant site (partial, case-insensitive)"),
    disease: str | None = Query(None, description="Filter variants by disease (partial, case-insensitive)"),
    classification: str | None = Query(
        None,
        description="Filter by classification level (pathogenic|likely_pathogenic|uncertain|likely_benign|benign)",
    ),
    review_status: str | None = Query(
        None,
        description="Filter by aggregate review status (provisional|approved|corrected|rejected)",
    ),
    source_language: str | None = Query(
        None,
        description="Filter by source language code (en|zh|ja|de|fr|ru)",
    ),
    sort_by: str | None = Query(
        None,
        description="Sort key (gene|variant|disease|classification|evidence|refs|confidence|updated)",
    ),
    sort_order: str | None = Query(None, description="Sort direction (asc|desc)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(24, ge=1, le=200, description="Variants per page"),
) -> VariantSearchResponse:
    """List variant-centric rows with server-side aggregation and pagination.

    Aggregates evidence groups by ``gene:variant[:disease]`` slug, applies
    filters/sort, and returns only the current page plus pre-filter aggregate
    stats and autocomplete candidates. Replaces the previous client-side flow
    that downloaded the full evidence-group corpus.
    """
    return await store.search_variants(
        gene=gene,
        variant=variant,
        disease=disease,
        classification=classification,
        review_status=review_status,
        source_language=source_language,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        owner_user_id=account.owner_user_id,
    )


@router.get("/literature/search", response_model=LiteratureSearchResponse)
async def search_literature(
    literature: LiteratureStore = Depends(get_literature_store),
    account: AuthContext = Depends(get_current_account),
    gene: str | None = Query(None, description="Filter by gene name"),
    variant: str | None = Query(None, description="Filter by variant"),
    disease: str | None = Query(None, description="Filter by disease"),
    pmid: str | None = Query(None, description="Filter by PMID (exact)"),
    doi: str | None = Query(None, description="Filter by DOI (partial)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> LiteratureSearchResponse:
    """Search literature profiles with per-article aggregation."""
    return await literature.search(
        gene=gene,
        variant=variant,
        disease=disease,
        pmid=pmid,
        doi=doi,
        page=page,
        page_size=page_size,
        owner_user_id=account.owner_user_id,
    )


@router.get(
    "/literature/{source_document_id}/detail",
    response_model=LiteratureProfileDetailResponse,
)
async def get_literature_detail(
    source_document_id: UUID,
    literature: LiteratureStore = Depends(get_literature_store),
    account: AuthContext = Depends(get_current_account),
) -> LiteratureProfileDetailResponse:
    """Return full literature profile with all evidence groups."""
    profile = await literature.detail(
        source_document_id,
        owner_user_id=account.owner_user_id,
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Literature profile not found")
    return profile


@router.post("/literature/refresh", response_model=LiteratureRefreshResponse)
@limiter.limit("5/minute")
async def refresh_literature_profiles(
    request: Request,
    literature: LiteratureStore = Depends(get_literature_store),
    account: AuthContext = Depends(get_current_account),
) -> LiteratureRefreshResponse:
    """Refresh all literature profiles from canonical evidence. Admin endpoint."""
    return await literature.refresh_all(owner_user_id=account.owner_user_id)
