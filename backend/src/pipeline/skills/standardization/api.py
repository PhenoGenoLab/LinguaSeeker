"""Public facade for Phase 3 entity standardization."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.tools.extraction.contracts import (
    DualEvidenceExtractionResult,
)
from src.pipeline.skills.graph_retrieval.api import GraphRagService
from src.core.tools.standardization.adapters import DualResultAdapter
from src.core.tools.standardization.contracts import (
    EntityMatch,
    StandardizationResult,
)
from src.core.tools.standardization.cross_lingual_disease import (
    CrossLingualDiseaseResolver,
)
from src.core.tools.standardization.core import StandardizationService
from src.core.tools.standardization.matchers import HybridTerminologyMatcher
from src.core.tools.standardization.precise_match.core import PreciseTerminologyMatcher
from src.core.tools.standardization.repositories import (
    StandardizationRepository,
)
from src.core.tools.standardization.similarity_match.core import (
    SimilarityMatchConfig,
    SimilarityTerminologyMatcher,
)
from src.core.tools.standardization.similarity_match.providers import (
    FallbackEmbeddingProvider,
    FallbackRerankProvider,
    EmbeddingHttpProvider,
    RerankHttpProvider,
)
from src.core.tools.standardization.similarity_match.repositories import (
    PgvectorTerminologyRepository,
)

if TYPE_CHECKING:
    from src.core.config import Settings


def serialize_matches(matches: tuple[EntityMatch, ...]) -> list[dict[str, Any]]:
    """Serialize EntityMatch tuple into auditable JSON-serializable dicts."""
    entries: list[dict[str, Any]] = []
    for match in matches:
        entry: dict[str, Any] = {
            "candidate_id": match.candidate.candidate_id,
            "raw_text": match.candidate.raw_text,
            "entity_type": match.candidate.entity_type.value,
            "chain_id": match.candidate.chain_id,
            "track": match.candidate.track,
            "field_id": match.candidate.field_id,
            "status": match.status.value,
            "external_id": match.external_id,
            "display_name": match.display_name,
            "rationale": match.rationale,
            "match_method": match.match_method.value,
            "similarity_score": match.similarity_score,
        }
        if match.terminology_candidates:
            entry["terminology_candidates"] = [
                {
                    "external_id": tc.external_id,
                    "display_name": tc.display_name,
                    "source_db": tc.source_db,
                    "alias_type": tc.alias_type,
                }
                for tc in match.terminology_candidates
            ]
        entries.append(entry)
    return entries


def build_summary_metadata(
    *,
    imported_terminology: bool,
    terminology_sources: list[str],
    terminology_version: str,
    terminology_entry_count: int = 0,
    embedding_available: bool = False,
) -> dict[str, Any]:
    """Build truthful summary metadata with terminology health indicators."""
    return {
        "imported_terminology": imported_terminology,
        "terminology_sources": terminology_sources,
        "terminology_version": terminology_version,
        "terminology_entry_count": terminology_entry_count,
        "embedding_available": embedding_available,
    }


class EntityStandardizationService:
    """Facade that wires the adapter, matcher, and orchestration service."""

    def __init__(
        self,
        cfg: Settings,
        graph_rag_service: GraphRagService | None = None,
    ):
        self._cfg = cfg
        self._graph_rag_service = graph_rag_service

    async def run_dual_result(
        self,
        session: AsyncSession,
        result: DualEvidenceExtractionResult,
        *,
        source_document_id: str,
        processing_run_id: str,
        owner_user_id: str | None = None,
    ) -> StandardizationResult:
        """Standardize one dual-track evidence extraction result."""
        repository = StandardizationRepository(session)
        precise_matcher = PreciseTerminologyMatcher(repository)
        semantic_base_url = self._cfg.embedding.base_url
        local_embedding = EmbeddingHttpProvider(
            base_url=semantic_base_url,
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
        cross_lingual_disease_resolver = CrossLingualDiseaseResolver(session)
        matcher = HybridTerminologyMatcher(
            precise_matcher,
            similarity_matcher,
            cross_lingual_disease_resolver=cross_lingual_disease_resolver,
        )
        adapter = DualResultAdapter()
        input_data = adapter.to_standardization_input(
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
                # The graph is a secondary projection of this result. Degrade,
                # but record the failure so callers can surface it.
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








