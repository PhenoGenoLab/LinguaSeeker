"""Delta audit query routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_current_account
from src.api.deps import get_audit_store
from src.core.foundation.auth.contracts import AuthContext
from src.core.tools.review.contracts import (
    DeltaEntry,
    ReviewAuditEventResponse,
    ReviewStatus,
    TargetType,
)
from src.ports.review import AuditEventRecord, AuditStore

router = APIRouter()


@router.get("/", response_model=list[ReviewAuditEventResponse], include_in_schema=False)
@router.get("", response_model=list[ReviewAuditEventResponse])
async def list_audit_events(
    canonical_evidence_id: UUID | None = None,
    source_document_id: UUID | None = None,
    reviewer_id: UUID | None = None,
    limit: int = Query(100, ge=1, le=1000),
    audit: AuditStore = Depends(get_audit_store),
    account: AuthContext = Depends(get_current_account),
) -> list[ReviewAuditEventResponse]:
    """List review audit events with optional filters."""
    events = await audit.list_events(
        canonical_evidence_id=canonical_evidence_id,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
        owner_user_id=account.owner_user_id,
        limit=limit,
    )
    return [_to_response(e) for e in events]


def _to_response(event: AuditEventRecord) -> ReviewAuditEventResponse:
    """Convert ORM model to API response."""
    return ReviewAuditEventResponse(
        review_event_id=event.review_event_id,
        canonical_evidence_id=event.canonical_evidence_id,
        reviewer_id=event.reviewer_id,
        target_type=TargetType(event.target_type),
        old_status=ReviewStatus(event.old_status) if event.old_status else None,
        new_status=ReviewStatus(event.new_status) if event.new_status else None,
        field_deltas=[DeltaEntry(**d) for d in event.field_deltas],
        change_reason=event.change_reason,
        created_at=event.created_at,
    )
