"""PostgreSQL adapter for read-only evidence queries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.tools.review.contracts import (
    EvidenceGroupDetailResponse,
    EvidenceSearchResponse,
    VariantSearchResponse,
)
from src.core.tools.standardization.contracts import (
    StandardizedEntityList,
    StandardizedEntitySummary,
)
from src.dao.postgresql.models import (
    EvidenceEntityBinding,
    NormalizedEntity,
    RunEvidenceItem,
)
from src.dao.postgresql.review.search_service import SearchService
from src.utils.exceptions import RecordNotFoundError
from sqlalchemy.exc import NoResultFound


class PostgresEvidenceStore:
    """One session per query; read-only, so no commit is needed."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_standardized_entities(
        self,
        *,
        processing_run_id: str,
    ) -> StandardizedEntityList:
        """Return distinct entities bound to this run's evidence.

        Standardized entities sort first so the UI can show usable mappings
        before residual unmapped or ambiguous mentions.
        """
        status_rank = case(
            (NormalizedEntity.standardization_status == "standardized", 0),
            (NormalizedEntity.standardization_status == "ambiguous", 1),
            else_=2,
        )
        occurrence_count = func.count(EvidenceEntityBinding.evidence_entity_binding_id)
        statement = (
            select(
                NormalizedEntity.entity_id,
                NormalizedEntity.entity_type,
                NormalizedEntity.external_id,
                NormalizedEntity.display_name,
                NormalizedEntity.standardization_status,
                occurrence_count.label("occurrence_count"),
                func.array_agg(func.distinct(EvidenceEntityBinding.raw_entity_text)).label("raw_texts"),
            )
            .join(EvidenceEntityBinding, EvidenceEntityBinding.entity_id == NormalizedEntity.entity_id)
            .join(
                RunEvidenceItem,
                RunEvidenceItem.run_evidence_item_id == EvidenceEntityBinding.run_evidence_item_id,
            )
            .where(RunEvidenceItem.processing_run_id == UUID(processing_run_id))
            .group_by(
                NormalizedEntity.entity_id,
                NormalizedEntity.entity_type,
                NormalizedEntity.external_id,
                NormalizedEntity.display_name,
                NormalizedEntity.standardization_status,
            )
            .order_by(
                status_rank,
                NormalizedEntity.entity_type,
                occurrence_count.desc(),
                NormalizedEntity.display_name,
            )
        )
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()
        items = tuple(
            StandardizedEntitySummary(
                entity_id=str(row.entity_id),
                entity_type=row.entity_type,
                external_id=row.external_id,
                display_name=row.display_name,
                standardization_status=row.standardization_status,
                raw_texts=tuple(text for text in (row.raw_texts or ()) if text),
                occurrence_count=int(row.occurrence_count),
            )
            for row in rows
        )
        return StandardizedEntityList(items=items)

    async def group_detail(
        self,
        *,
        group_id: str | None,
        source_document_id: str | None,
        owner_user_id: UUID | str | None,
    ) -> EvidenceGroupDetailResponse:
        async with self._session_factory() as session:
            try:
                return await SearchService(session).get_group_detail(
                    group_id=group_id,
                    source_document_id=source_document_id,
                    owner_user_id=owner_user_id,
                )
            except NoResultFound as exc:
                raise RecordNotFoundError("Evidence group not found") from exc

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
