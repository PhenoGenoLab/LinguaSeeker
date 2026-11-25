"""PostgreSQL adapter for review audit events."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.tools.review.contracts import DeltaEntry, ReviewStatus, TargetType
from src.dao.postgresql.models import CanonicalEvidenceItem, ReviewAuditEvent
from src.ports.review import AuditEventRecord


def _record(event: ReviewAuditEvent) -> AuditEventRecord:
    return AuditEventRecord(
        review_event_id=event.review_event_id,
        canonical_evidence_id=event.canonical_evidence_id,
        reviewer_id=event.reviewer_id,
        target_type=event.target_type,
        old_status=event.old_status,
        new_status=event.new_status,
        field_deltas=list(event.field_deltas or []),
        change_reason=event.change_reason,
        created_at=event.created_at,
    )


async def record_audit_event(
    session: AsyncSession,
    *,
    canonical_evidence_id: UUID,
    reviewer_id: UUID | None,
    target_type: TargetType,
    old_status: ReviewStatus | None,
    new_status: ReviewStatus | None,
    field_deltas: list[DeltaEntry],
    change_reason: str | None = None,
) -> ReviewAuditEvent:
    """Stage a review audit event in the caller's transaction."""
    event = ReviewAuditEvent(
        canonical_evidence_id=canonical_evidence_id,
        reviewer_id=reviewer_id,
        target_type=target_type.value,
        old_status=old_status.value if old_status else None,
        new_status=new_status.value if new_status else None,
        field_deltas=[d.model_dump() for d in field_deltas],
        change_reason=change_reason,
    )
    session.add(event)
    await session.flush()
    return event


async def list_audit_events(
    session: AsyncSession,
    *,
    canonical_evidence_id: UUID | None = None,
    source_document_id: UUID | None = None,
    reviewer_id: UUID | None = None,
    owner_user_id: UUID | str | None = None,
    limit: int = 100,
) -> list[ReviewAuditEvent]:
    """Query review audit events with optional filters."""
    stmt = select(ReviewAuditEvent).join(
        CanonicalEvidenceItem,
        CanonicalEvidenceItem.canonical_evidence_id == ReviewAuditEvent.canonical_evidence_id,
    )
    owner_id = UUID(str(owner_user_id)) if owner_user_id else None
    if source_document_id:
        stmt = stmt.where(CanonicalEvidenceItem.source_document_id == source_document_id)
    stmt = stmt.where(
        CanonicalEvidenceItem.owner_user_id.is_(None)
        if owner_id is None
        else CanonicalEvidenceItem.owner_user_id == owner_id
    )
    if canonical_evidence_id:
        stmt = stmt.where(ReviewAuditEvent.canonical_evidence_id == canonical_evidence_id)
    if reviewer_id:
        stmt = stmt.where(ReviewAuditEvent.reviewer_id == reviewer_id)
    stmt = stmt.order_by(ReviewAuditEvent.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


class PostgresAuditStore:
    """Session-per-query adapter for audit reads."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_events(
        self,
        *,
        canonical_evidence_id: UUID | None = None,
        source_document_id: UUID | None = None,
        reviewer_id: UUID | None = None,
        owner_user_id: UUID | str | None = None,
        limit: int = 100,
    ) -> list[AuditEventRecord]:
        async with self._session_factory() as session:
            events = await list_audit_events(
                session,
                canonical_evidence_id=canonical_evidence_id,
                source_document_id=source_document_id,
                reviewer_id=reviewer_id,
                owner_user_id=owner_user_id,
                limit=limit,
            )
            return [_record(event) for event in events]
