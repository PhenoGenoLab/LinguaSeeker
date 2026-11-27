"""PostgreSQL adapter for evidence review feedback."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.tools.review.contracts import (
    EvidenceCardPayload,
    EvidencePatchRequest,
    ReviewStatus,
    TargetType,
    card_field_for_field_id,
)
from src.core.tools.review.delta_audit_service import DeltaAuditService
from src.dao.postgresql.models import CanonicalEvidenceItem
from src.dao.postgresql.review.audit_store import record_audit_event
from src.ports.review import PatchResult
from src.utils.exceptions import RecordNotFoundError


class FeedbackService:
    """Patch an evidence card inside the caller's transaction."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def patch_evidence(
        self,
        *,
        canonical_evidence_id: UUID,
        patch: EvidencePatchRequest,
        reviewer_id: UUID | None = None,
        owner_user_id: UUID | str | None = None,
    ) -> PatchResult:
        """Apply a patch and record an audit event in the current session."""
        owner_id = UUID(str(owner_user_id)) if owner_user_id else None
        owner_filter = (
            CanonicalEvidenceItem.owner_user_id.is_(None)
            if owner_id is None
            else CanonicalEvidenceItem.owner_user_id == owner_id
        )
        stmt = select(CanonicalEvidenceItem).where(
            CanonicalEvidenceItem.canonical_evidence_id == canonical_evidence_id,
            owner_filter,
        )
        result = await self._session.execute(stmt)
        evidence = result.scalar_one()

        payload = dict(evidence.active_payload or {})
        field_id = str(payload.get("field_id") or evidence.field_id)

        has_card_keys = any(k in EvidenceCardPayload.DIFF_FIELDS for k in payload)
        if has_card_keys:
            old_card = EvidenceCardPayload(**{k: v for k, v in payload.items() if k in EvidenceCardPayload.DIFF_FIELDS})
        else:
            old_card = EvidenceCardPayload.from_field_payload(field_id=field_id, payload=payload)

        new_card_data = old_card.model_dump()
        new_card_data.update(patch.fields)
        new_card = EvidenceCardPayload(**new_card_data)

        field_deltas = DeltaAuditService.compute_deltas(old_card, new_card)

        old_status = ReviewStatus(evidence.review_status)
        new_status = patch.new_status or (ReviewStatus.CORRECTED if field_deltas else old_status)

        for field_name, field_value in patch.fields.items():
            payload[field_name] = field_value
        card_field = card_field_for_field_id(field_id)
        if card_field is not None and card_field in patch.fields:
            payload["value"] = patch.fields[card_field]
        payload["field_id"] = field_id
        evidence.active_payload = payload
        evidence.review_status = new_status.value
        await self._session.flush()

        if field_deltas or new_status != old_status:
            await record_audit_event(
                self._session,
                canonical_evidence_id=canonical_evidence_id,
                reviewer_id=reviewer_id,
                target_type=TargetType.EVIDENCE_ITEM,
                old_status=old_status,
                new_status=new_status,
                field_deltas=field_deltas,
                change_reason=patch.change_reason,
            )
            await self._refresh_literature_profile(evidence.source_document_id, owner_user_id=owner_id)
            await self._refresh_search_index()

        return PatchResult(
            canonical_evidence_id=canonical_evidence_id,
            old_status=old_status,
            new_status=new_status,
            deltas=len(field_deltas),
            field_deltas=field_deltas,
        )

    async def _refresh_literature_profile(
        self,
        source_document_id: UUID,
        *,
        owner_user_id: UUID | None,
    ) -> None:
        from src.dao.postgresql.literature_profile_repo import LiteratureProfileRepository

        repo = LiteratureProfileRepository(self._session)
        await repo.refresh_for_document(source_document_id, owner_user_id=owner_user_id)

    async def _refresh_search_index(self) -> None:
        from src.dao.postgresql.search_index_repo import SearchIndexRepository

        await SearchIndexRepository(self._session).refresh()


class PostgresFeedbackStore:
    """Own the transaction for one evidence patch."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def patch_evidence(
        self,
        *,
        canonical_evidence_id: UUID,
        patch: EvidencePatchRequest,
        reviewer_id: UUID | None = None,
        owner_user_id: UUID | str | None = None,
    ) -> PatchResult:
        async with self._session_factory() as session:
            try:
                result = await FeedbackService(session).patch_evidence(
                    canonical_evidence_id=canonical_evidence_id,
                    patch=patch,
                    reviewer_id=reviewer_id,
                    owner_user_id=owner_user_id,
                )
            except NoResultFound as exc:
                raise RecordNotFoundError(f"Evidence {canonical_evidence_id} not found") from exc
            await session.commit()
            return result
