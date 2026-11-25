"""PostgreSQL adapter for read-only evidence queries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.tools.review.contracts import (
    EvidenceGroupDetailResponse,
    EvidenceSearchResponse,
    VariantSearchResponse,
)
from src.dao.postgresql.review.search_service import SearchService


class PostgresEvidenceStore:
    """One session per query; read-only, so no commit is needed."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def group_detail(
        self,
        *,
        group_id: str | None,
        source_document_id: str | None,
        owner_user_id: UUID | str | None,
    ) -> EvidenceGroupDetailResponse:
        async with self._session_factory() as session:
            return await SearchService(session).get_group_detail(
                group_id=group_id,
                source_document_id=source_document_id,
                owner_user_id=owner_user_id,
            )

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
    ) -> EvidenceSearchResponse:
        async with self._session_factory() as session:
            return await SearchService(session).search_evidence(
                gene=gene,
                variant=variant,
                disease=disease,
                pmid=pmid,
                doi=doi,
                page=page,
                page_size=page_size,
                owner_user_id=owner_user_id,
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
    ) -> VariantSearchResponse:
        async with self._session_factory() as session:
            return await SearchService(session).search_variants(
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
                owner_user_id=owner_user_id,
            )
