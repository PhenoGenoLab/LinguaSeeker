"""Composition facade for standardization persistence.

Each collaborator owns one change reason: terminology import, normalized entity
resolution, evidence projection, and read-model refresh. The facade keeps the
historical ``StandardizationRepository`` surface so callers are unchanged.
"""

from __future__ import annotations

from typing import Any

from src.core.tools.standardization.contracts import (
    EntityMatch,
    EntityType,
    StandardizationInput,
    TerminologyCandidate,
)
from src.core.tools.standardization.db_ready_gate import DbReadyGateReport
from src.core.tools.standardization.importers import ImportBatch
from ._shared import (
    CANONICAL_ELIGIBLE_STATUSES,
    CanonicalIdentityKey,
    RunItemEntityBindings,
    RunItemSpec,
    hash_payload,
    normalize_entity_text,
    normalize_enum_like_string,
    sanitize_jsonb_value,
)
from .entities import EntityResolutionRepository
from .evidence import EvidenceProjectionRepository
from .search_index import SearchIndexRepository
from .terminology import TerminologyImportRepository

__all__ = [
    "CANONICAL_ELIGIBLE_STATUSES",
    "CanonicalIdentityKey",
    "EntityResolutionRepository",
    "EvidenceProjectionRepository",
    "RunItemEntityBindings",
    "RunItemSpec",
    "SearchIndexRepository",
    "StandardizationRepository",
    "TerminologyImportRepository",
    "hash_payload",
    "normalize_entity_text",
    "normalize_enum_like_string",
    "sanitize_jsonb_value",
]


class StandardizationRepository:
    """Facade over the standardization persistence collaborators.

    Keeps the session so callers (and tests) can still inspect/commit it, and
    exposes the historical method names by delegating to the owning collaborator.
    """

    def __init__(self, session: Any) -> None:
        self.session = session
        self.terminology = TerminologyImportRepository(session)
        self.entities = EntityResolutionRepository(session)
        self.evidence = EvidenceProjectionRepository(session)
        self.search_index = SearchIndexRepository(session)

    @property
    def db_ready_gate_report(self) -> DbReadyGateReport | None:
        """Return the latest DB-ready gate audit report for this repository instance."""
        return self.evidence.db_ready_gate_report

    @property
    def _run_item_rows(self) -> list[tuple[Any, RunItemSpec]]:
        """Return staged run-item rows (diagnostics and tests)."""
        return self.evidence._run_item_rows

    @_run_item_rows.setter
    def _run_item_rows(self, rows: list[tuple[Any, RunItemSpec]]) -> None:
        self.evidence._run_item_rows = rows

    _find_gene_variant_complete_groups = staticmethod(EvidenceProjectionRepository._find_gene_variant_complete_groups)
    _find_identity_passable_groups = staticmethod(EvidenceProjectionRepository._find_identity_passable_groups)

    async def find_alias_candidates(
        self,
        entity_type: EntityType,
        raw_text: str,
    ) -> tuple[TerminologyCandidate, ...]:
        """Query terminology aliases by normalized alias text and entity type."""
        return await self.terminology.find_alias_candidates(entity_type, raw_text)

    async def upsert_terminology_batch(self, batch: ImportBatch) -> None:
        """Persist a parsed terminology batch."""
        await self.terminology.upsert_terminology_batch(batch)

    async def upsert_normalized_entity(self, match: EntityMatch) -> str:
        """Persist or identify a normalized entity for one match."""
        return await self.entities.upsert_normalized_entity(match)

    async def ensure_run_parents(
        self,
        *,
        source_document_id: str,
        processing_run_id: str,
        owner_user_id: str | None = None,
    ) -> None:
        """Ensure source document and processing run parent rows exist."""
        await self.evidence.ensure_run_parents(
            source_document_id=source_document_id,
            processing_run_id=processing_run_id,
            owner_user_id=owner_user_id,
        )

    async def insert_run_evidence_items(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
    ) -> tuple[str, ...]:
        """Insert run-level evidence items."""
        return await self.evidence.insert_run_evidence_items(input_data, matches)

    async def insert_entity_bindings(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None:
        """Insert evidence-to-entity bindings."""
        await self.evidence.insert_entity_bindings(input_data, matches, entity_ids)

    async def upsert_canonical_evidence(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None:
        """Upsert canonical evidence state."""
        await self.evidence.upsert_canonical_evidence(input_data, matches, entity_ids)

    async def persist_run_evidence(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
    ) -> tuple[str, ...]:
        """Compatibility wrapper used by the service layer plan."""
        return await self.evidence.persist_run_evidence(input_data, matches)

    async def persist_bindings(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None:
        """Compatibility wrapper used by the service layer plan."""
        await self.evidence.persist_bindings(input_data, matches, entity_ids)

    async def refresh_literature_profile(
        self,
        source_document_id: str,
        owner_user_id: str | None = None,
    ) -> None:
        """Refresh the literature_profiles read model for a document."""
        await self.search_index.refresh_literature_profile(source_document_id, owner_user_id=owner_user_id)

    async def refresh_search_index(self) -> None:
        """Refresh the frontend_search_index read model."""
        await self.search_index.refresh_search_index()

    def _build_run_item_specs(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        scope_hashes: dict[str, str],
    ) -> list[RunItemSpec]:
        """Build run-item persistence specs (exposed for tests and diagnostics)."""
        return self.evidence._build_run_item_specs(input_data, matches, scope_hashes)
