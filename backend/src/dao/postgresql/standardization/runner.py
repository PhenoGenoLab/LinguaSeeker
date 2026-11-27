"""PostgreSQL runner for one dual-track standardization unit of work."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.tools.extraction.contracts import DualEvidenceExtractionResult
from src.core.tools.standardization.adapters import DualResultAdapter
from src.core.tools.standardization.contracts import StandardizationResult
from src.core.tools.standardization.core import StandardizationService
from src.core.tools.standardization.matchers import HybridTerminologyMatcher
from src.core.tools.standardization.mcp_match.core import HpoMcpTerminologyMatcher
from src.core.tools.standardization.precise_match.core import PreciseTerminologyMatcher
from src.core.tools.standardization.similarity_match.core import (
    SimilarityMatchConfig,
    SimilarityTerminologyMatcher,
)
from src.core.tools.standardization.similarity_match.providers import (
    EmbeddingHttpProvider,
    FallbackEmbeddingProvider,
    FallbackRerankProvider,
    RerankHttpProvider,
)
from src.dao.postgresql.standardization.cross_lingual_disease import CrossLingualDiseaseResolver
from src.dao.postgresql.standardization.repositories import StandardizationRepository
from src.dao.postgresql.standardization.similarity_repositories import PgvectorTerminologyRepository

if TYPE_CHECKING:
    from src.core.config import Settings


class PostgresStandardizationRunner:
    """Assemble matchers/repositories per run and own the transaction."""

    def __init__(
        self,
        *,
        cfg: "Settings",
        session_factory: async_sessionmaker[AsyncSession],
        graph_rag_service: Any = None,
    ) -> None:
        self._cfg = cfg
        self._session_factory = session_factory
        self._graph_rag_service = graph_rag_service

    async def run_dual_result(
        self,
        result: DualEvidenceExtractionResult,
        *,
        source_document_id: str,
        processing_run_id: str,
        owner_user_id: str | UUID | None = None,
    ) -> StandardizationResult:
        """Standardize one result and commit all persistence side effects."""
        owner_id = str(owner_user_id) if owner_user_id else None
        async with self._session_factory() as session:
            std_result = await self._run(
                session,
                result,
                source_document_id=source_document_id,
                processing_run_id=processing_run_id,
                owner_user_id=owner_id,
            )
            await session.commit()
        return std_result

    async def _run(
        self,
        session: AsyncSession,
        result: DualEvidenceExtractionResult,
        *,
        source_document_id: str,
        processing_run_id: str,
        owner_user_id: str | None,
    ) -> StandardizationResult:
        repository = StandardizationRepository(session)
        precise_matcher = PreciseTerminologyMatcher(repository)

        local_embedding = EmbeddingHttpProvider(
            base_url=self._cfg.embedding.base_url,
            model=self._cfg.embedding.model,
            api_key=self._cfg.embedding.api_key,
            api_style=self._cfg.embedding.api_style,
        )
        remote_embedding = (
            EmbeddingHttpProvider(
                base_url=self._cfg.embedding.remote_base_url,
                model=self._cfg.embedding.remote_model or self._cfg.embedding.model,
                api_keys=self._cfg.embedding.remote_all_api_keys,
            )
            if self._cfg.embedding.remote_base_url
            else None
        )
        local_rerank = RerankHttpProvider(
            base_url=self._cfg.rerank.base_url,
            model=self._cfg.rerank.model,
            api_key=self._cfg.rerank.api_key,
            api_style=self._cfg.rerank.api_style,
        )
        remote_rerank = (
            RerankHttpProvider(
                base_url=self._cfg.rerank.remote_base_url,
                model=self._cfg.rerank.remote_model or self._cfg.rerank.model,
                api_keys=self._cfg.rerank.remote_all_api_keys,
            )
            if self._cfg.rerank.remote_base_url
            else None
        )
        similarity_matcher = SimilarityTerminologyMatcher(
            embedding_provider=FallbackEmbeddingProvider(local_embedding, remote_embedding),
            rerank_provider=FallbackRerankProvider(local_rerank, remote_rerank),
            repository=PgvectorTerminologyRepository(session),
            config=SimilarityMatchConfig(
                embedding_model=self._cfg.embedding.model,
                rerank_top_k=self._cfg.rerank.top_k,
                rerank_score_threshold=self._cfg.rerank.score_threshold,
            ),
        )
        matcher = HybridTerminologyMatcher(
            precise_matcher,
            similarity_matcher,
            cross_lingual_disease_resolver=CrossLingualDiseaseResolver(session),
        )
        if self._cfg.mcp.hpocr.enabled:
            from src.core.adapters.mcp.hpocr import McpHpocrClient

            matcher = HpoMcpTerminologyMatcher(McpHpocrClient(self._cfg), matcher)
        input_data = DualResultAdapter().to_standardization_input(
            result,
            source_document_id=source_document_id,
            processing_run_id=processing_run_id,
        )
        input_data = replace(input_data, owner_user_id=owner_user_id)
        std_result = await StandardizationService(matcher, repository).run(input_data)

        if self._graph_rag_service is not None:
            try:
                await self._graph_rag_service.write_dual_result_graph(
                    input_data,
                    std_result.matches,
                    result,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to write GraphRAG subgraph for run {}: {}",
                    processing_run_id,
                    exc,
                )
                std_result = replace(
                    std_result,
                    warnings=(*std_result.warnings, f"graph_rag_write_failed: {exc}"),
                )
        return std_result
