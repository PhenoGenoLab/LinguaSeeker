"""Standardization ports (consumer-owned)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.core.tools.standardization.contracts import (
    EntityMatch,
    EntityType,
    StandardizationInput,
    StandardizationResult,
    TerminologyCandidate,
)


class TerminologyRepository(Protocol):
    """Persistence operations used by standardization matching and projection."""

    async def find_alias_candidates(
        self,
        entity_type: EntityType,
        raw_text: str,
    ) -> tuple[TerminologyCandidate, ...]: ...

    async def ensure_run_parents(
        self,
        *,
        source_document_id: str,
        processing_run_id: str,
        owner_user_id: str | None = None,
    ) -> None: ...

    async def upsert_normalized_entity(self, match: EntityMatch) -> str: ...

    async def persist_run_evidence(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
    ) -> tuple[str, ...]: ...

    async def persist_bindings(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None: ...

    async def upsert_canonical_evidence(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None: ...

    async def refresh_literature_profile(
        self,
        source_document_id: str,
        owner_user_id: str | None = None,
    ) -> None: ...

    async def refresh_search_index(self) -> None: ...


class CrossLingualResolver(Protocol):
    """Resolve a non-English disease name to its English display name."""

    async def resolve(self, raw_text: str) -> str | None: ...


class StandardizationRunner(Protocol):
    """Run one dual-track standardization as a single unit of work."""

    async def run_dual_result(
        self,
        result: object,
        *,
        source_document_id: str,
        processing_run_id: str,
        owner_user_id: str | UUID | None = None,
    ) -> StandardizationResult: ...
