"""Normalized-entity resolution persistence."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from src.core.tools.standardization.contracts import EntityMatch, EntityType, MatchStatus
from ._shared import normalize_entity_text
from src.core.tools.standardization.variant_id import make_internal_variant_id
from src.dao.postgresql.models import NormalizedEntity


class EntityResolutionRepository:
    """Persist or identify normalized entities from standardization matches."""

    def __init__(self, session: Any) -> None:
        self.session = session

    async def upsert_normalized_entity(self, match: EntityMatch) -> str:
        """Persist or identify a normalized entity for one match."""
        normalized_raw_text = normalize_entity_text(
            match.candidate.entity_type,
            match.candidate.raw_text,
        )
        # Variant entities always carry a non-NULL external_id: ClinVar matches
        # use ``ClinVarVariation:<id>``; unmapped/ambiguous variants get a
        # deterministic synthetic ``internal:variant:<sha8>`` id so they remain
        # a stable pivot dimension while retaining their audit ``unmapped``
        # status.
        external_id = match.external_id
        if (
            match.candidate.entity_type == EntityType.VARIANT
            and match.status != MatchStatus.STANDARDIZED
            and not external_id
        ):
            gene = str(match.candidate.metadata.get("gene_symbol", "") or "").strip()
            external_id = make_internal_variant_id(match.candidate.raw_text, gene)

        existing: NormalizedEntity | None = None
        if match.status == MatchStatus.STANDARDIZED and match.external_id:
            statement = select(NormalizedEntity).where(
                NormalizedEntity.entity_type == match.candidate.entity_type.value,
                NormalizedEntity.external_id == match.external_id,
                NormalizedEntity.standardization_status == MatchStatus.STANDARDIZED.value,
            )
            existing = (await self.session.execute(statement)).scalars().first()
        elif (
            match.candidate.entity_type == EntityType.VARIANT
            and external_id
            and external_id.startswith("internal:variant:")
        ):
            # Idempotency for synthetic variant ids: collapse repeated mentions
            # of the same unmapped variant onto one row before falling back to
            # the raw-text lookup (which covers pre-existing NULL-external_id rows).
            statement = select(NormalizedEntity).where(
                NormalizedEntity.entity_type == match.candidate.entity_type.value,
                NormalizedEntity.external_id == external_id,
                NormalizedEntity.standardization_status == match.status.value,
            )
            existing = (await self.session.execute(statement)).scalars().first()
            if existing is None:
                statement = select(NormalizedEntity).where(
                    NormalizedEntity.entity_type == match.candidate.entity_type.value,
                    NormalizedEntity.normalized_raw_text == normalized_raw_text,
                    NormalizedEntity.standardization_status == match.status.value,
                )
                existing = (await self.session.execute(statement)).scalars().first()
        else:
            statement = select(NormalizedEntity).where(
                NormalizedEntity.entity_type == match.candidate.entity_type.value,
                NormalizedEntity.normalized_raw_text == normalized_raw_text,
                NormalizedEntity.standardization_status == match.status.value,
            )
            existing = (await self.session.execute(statement)).scalars().first()
        payload = {
            "candidate_id": match.candidate.candidate_id,
            "rationale": match.rationale,
            "match_method": match.match_method.value,
            "similarity_score": match.similarity_score,
            "terminology_candidate_ids": [candidate.entry_id for candidate in match.terminology_candidates],
            **match.raw_payload,
        }
        if existing is None:
            existing = NormalizedEntity(
                entity_type=match.candidate.entity_type.value,
                external_id=external_id,
                normalized_raw_text=normalized_raw_text,
                display_name=match.display_name,
                aliases=[match.candidate.raw_text],
                standardization_status=match.status.value,
                raw_payload=payload,
            )
            self.session.add(existing)
            await self.session.flush()
        else:
            existing.display_name = match.display_name
            existing.aliases = list({*existing.aliases, match.candidate.raw_text})
            existing.raw_payload = {**existing.raw_payload, **payload}

        return str(existing.entity_id)
