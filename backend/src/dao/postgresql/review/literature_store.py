"""PostgreSQL adapter for literature profile queries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.tools.review.contracts import (
    EvidenceGroupSummary,
    LiteratureProfileDetailResponse,
    LiteratureProfileSummary,
    LiteratureRefreshResponse,
    LiteratureSearchResponse,
)
from src.dao.postgresql.literature_profile_repo import LiteratureProfileRepository
from src.dao.postgresql.models import CanonicalEvidenceItem


class PostgresLiteratureStore:
    """One session per call; the refresh endpoint commits inside the adapter."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

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
    ) -> LiteratureSearchResponse:
        async with self._session_factory() as session:
            items, total = await LiteratureProfileRepository(session).search(
                gene=gene,
                variant=variant,
                disease=disease,
                pmid=pmid,
                doi=doi,
                page=page,
                page_size=page_size,
                owner_user_id=owner_user_id,
            )
        return LiteratureSearchResponse(
            items=[LiteratureProfileSummary(**vars(item)) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def detail(
        self,
        source_document_id: UUID,
        *,
        owner_user_id: UUID | str | None = None,
    ) -> LiteratureProfileDetailResponse | None:
        async with self._session_factory() as session:
            profile = await LiteratureProfileRepository(session).get_by_document(
                source_document_id,
                owner_user_id=owner_user_id,
            )
        if profile is None:
            return None
        return LiteratureProfileDetailResponse(
            literature_profile_id=UUID(profile.literature_profile_id),
            source_document_id=UUID(profile.source_document_id),
            pmid=profile.pmid,
            doi=profile.doi,
            title=profile.title,
            authors=profile.authors,
            journal=profile.journal,
            publication_year=profile.publication_year,
            evidence_groups=[EvidenceGroupSummary(**eg) for eg in profile.evidence_groups],
            review_status=profile.review_status,
            review_notes=profile.review_notes,
            overall_confidence=profile.overall_confidence,
            total_evidence_fields=profile.total_evidence_fields,
            found_count=profile.found_count,
            not_found_count=profile.not_found_count,
        )

    async def refresh_all(self, *, owner_user_id: UUID | str | None = None) -> LiteratureRefreshResponse:
        owner_id = UUID(str(owner_user_id)) if owner_user_id else None
        owner_filter = (
            CanonicalEvidenceItem.owner_user_id.is_(None)
            if owner_id is None
            else CanonicalEvidenceItem.owner_user_id == owner_id
        )
        async with self._session_factory() as session:
            stmt = select(CanonicalEvidenceItem.source_document_id).where(owner_filter).distinct()
            result = await session.execute(stmt)
            doc_ids = [row[0] for row in result.all()]

            repo = LiteratureProfileRepository(session)
            for doc_id in doc_ids:
                await repo.refresh_for_document(doc_id, owner_user_id=owner_id)
            await session.commit()
        return LiteratureRefreshResponse(refreshed=len(doc_ids), total_documents=len(doc_ids))
