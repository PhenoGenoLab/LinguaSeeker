"""PostgreSQL adapter for chat sessions and messages."""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.tools.review.contracts import (
    ChatAction,
    ChatMessageResponse,
    ChatSessionResponse,
    EvidenceCardPayload,
)
from src.dao.postgresql.models import (
    CanonicalEvidenceItem,
    ChatMessage,
    ChatSession,
    EvidenceEntityBinding,
    NormalizedEntity,
    RunEvidenceItem,
)
from src.ports.chat import HistoryMessage
from src.utils.exceptions import NotFoundException


def _message_response(message: ChatMessage) -> ChatMessageResponse:
    action: ChatAction | None = None
    if message.action:
        try:
            action = ChatAction.model_validate(message.action)
        except Exception as exc:
            logger.warning("Stored chat action failed validation: {}", exc)
            action = None
    return ChatMessageResponse(
        message_id=message.message_id,
        chat_session_id=message.chat_session_id,
        role=message.role,
        content=message.content,
        evidence_id=message.evidence_id,
        entity_id=message.entity_id,
        action=action,
        created_at=message.created_at,
    )


def _session_response(session: ChatSession, message_count: int = 0) -> ChatSessionResponse:
    return ChatSessionResponse(
        chat_session_id=session.chat_session_id,
        processing_run_id=session.processing_run_id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        message_count=message_count,
    )


def _require_row(session: ChatSession | None, session_id: UUID) -> ChatSession:
    if session is None:
        raise NotFoundException("ChatSession", str(session_id))
    return session


async def _load_session(db: AsyncSession, session_id: UUID, owner_user_id: UUID | None) -> ChatSession:
    owner_filter = ChatSession.user_id.is_(None) if owner_user_id is None else ChatSession.user_id == owner_user_id
    result = await db.execute(select(ChatSession).where(ChatSession.chat_session_id == session_id, owner_filter))
    return _require_row(result.scalar_one_or_none(), session_id)


async def _message_count(db: AsyncSession, session_id: UUID) -> int:
    stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.chat_session_id == session_id)
    return int((await db.execute(stmt)).scalar_one())


async def _evidence_context(
    db: AsyncSession,
    *,
    canonical_evidence_id: UUID,
    owner_user_id: UUID | None,
) -> str:
    owner_filter = (
        CanonicalEvidenceItem.owner_user_id.is_(None)
        if owner_user_id is None
        else CanonicalEvidenceItem.owner_user_id == owner_user_id
    )
    result = await db.execute(
        select(CanonicalEvidenceItem).where(
            CanonicalEvidenceItem.canonical_evidence_id == canonical_evidence_id,
            owner_filter,
        )
    )
    evidence = result.scalar_one_or_none()
    if evidence is None:
        logger.warning("Chat evidence context requested for missing canonical evidence: {}", canonical_evidence_id)
        return ""

    payload = evidence.active_payload or {}
    best_run_id = evidence.current_best_run_evidence_id
    card = EvidenceCardPayload.from_field_payload(field_id=evidence.field_id, payload=payload)
    parts = [
        "**Evidence Card**",
        f"Gene: {card.gene or 'N/A'}",
        f"Variant: {card.variant or 'N/A'}",
        f"Phenotype: {card.phenotype or 'N/A'}",
        f"Disease: {card.disease or 'N/A'}",
        f"Classification: {card.classification or 'N/A'}",
        f"Evidence Strength: {card.evidence_strength or 'N/A'}",
        f"Summary: {card.summary or 'N/A'}",
    ]
    if best_run_id:
        result = await db.execute(
            select(NormalizedEntity)
            .join(EvidenceEntityBinding, EvidenceEntityBinding.entity_id == NormalizedEntity.entity_id)
            .where(EvidenceEntityBinding.run_evidence_item_id == best_run_id)
        )
        entities = result.scalars().all()
        if entities:
            parts.append("\n**Associated Entities**")
            for entity in entities[:5]:
                parts.append(f"- {entity.entity_type}: {entity.display_name} ({entity.external_id})")

        result = await db.execute(
            select(RunEvidenceItem).where(
                RunEvidenceItem.run_evidence_item_id == best_run_id,
                RunEvidenceItem.owner_user_id.is_(None)
                if owner_user_id is None
                else RunEvidenceItem.owner_user_id == owner_user_id,
            )
        )
        run_item = result.scalar_one_or_none()
        if run_item and run_item.source_span:
            snippet = run_item.source_span.get("text_snippet", "")[:300]
            if snippet:
                parts.append(f"\n**Source Text**\n{snippet}")
    return "\n".join(parts)


async def _history(db: AsyncSession, session_id: UUID, limit: int) -> list[HistoryMessage]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return [HistoryMessage(role=m.role, content=m.content) for m in rows if m.content]


class SessionChatStore:
    """Bind chat persistence to an existing session; the caller commits."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_session(
        self,
        *,
        processing_run_id: UUID | None,
        user_id: UUID | None = None,
    ) -> ChatSessionResponse:
        session = ChatSession(processing_run_id=processing_run_id, user_id=user_id)
        self._session.add(session)
        await self._session.flush()
        return _session_response(session)

    async def require_session(self, *, session_id: UUID, owner_user_id: UUID | None = None) -> None:
        await _load_session(self._session, session_id, owner_user_id)

    async def get_session(self, *, session_id: UUID, owner_user_id: UUID | None = None) -> ChatSessionResponse:
        session = await _load_session(self._session, session_id, owner_user_id)
        return _session_response(session, await _message_count(self._session, session_id))

    async def list_sessions(
        self,
        *,
        processing_run_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> list[ChatSessionResponse]:
        return await _list_sessions(self._session, processing_run_id, owner_user_id)

    async def append_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
        evidence_id: UUID | None = None,
        entity_id: UUID | None = None,
        action: ChatAction | None = None,
        owner_user_id: UUID | None = None,
    ) -> ChatMessageResponse:
        await self.require_session(session_id=session_id, owner_user_id=owner_user_id)
        message = ChatMessage(
            chat_session_id=session_id,
            role=role,
            content=content,
            evidence_id=evidence_id,
            entity_id=entity_id,
            action=action.model_dump(mode="json") if action else None,
        )
        self._session.add(message)
        await self._session.flush()
        return _message_response(message)

    async def list_messages(
        self,
        *,
        session_id: UUID,
        limit: int = 100,
        owner_user_id: UUID | None = None,
    ) -> list[ChatMessageResponse]:
        await self.require_session(session_id=session_id, owner_user_id=owner_user_id)
        result = await self._session.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return [_message_response(m) for m in result.scalars().all()]

    async def set_title(self, *, session_id: UUID, title: str) -> None:
        session = await _load_session(self._session, session_id, None)
        session.title = title
        await self._session.flush()

    async def evidence_context(self, *, canonical_evidence_id: UUID, owner_user_id: UUID | None = None) -> str:
        return await _evidence_context(
            self._session,
            canonical_evidence_id=canonical_evidence_id,
            owner_user_id=owner_user_id,
        )

    async def recent_history(self, *, session_id: UUID, limit: int = 10) -> list[HistoryMessage]:
        return await _history(self._session, session_id, limit)


class PostgresChatStore(SessionChatStore):
    """Session-per-call store; writes commit inside the adapter."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def _use(self, fn):
        async with self._session_factory() as session:
            store = SessionChatStore(session)
            result = await fn(store)
            await session.commit()
            return result

    async def create_session(self, *, processing_run_id, user_id=None):  # type: ignore[override]
        return await self._use(lambda s: s.create_session(processing_run_id=processing_run_id, user_id=user_id))

    async def get_session(self, *, session_id, owner_user_id=None):  # type: ignore[override]
        return await self._use(lambda s: s.get_session(session_id=session_id, owner_user_id=owner_user_id))

    async def list_sessions(self, *, processing_run_id, owner_user_id=None):  # type: ignore[override]
        return await self._use(
            lambda s: s.list_sessions(processing_run_id=processing_run_id, owner_user_id=owner_user_id)
        )

    async def append_message(self, *, session_id, role, content, evidence_id=None, entity_id=None, action=None, owner_user_id=None):  # type: ignore[override]
        return await self._use(
            lambda s: s.append_message(
                session_id=session_id,
                role=role,
                content=content,
                evidence_id=evidence_id,
                entity_id=entity_id,
                action=action,
                owner_user_id=owner_user_id,
            )
        )

    async def list_messages(self, *, session_id, limit=100, owner_user_id=None):  # type: ignore[override]
        return await self._use(lambda s: s.list_messages(session_id=session_id, limit=limit, owner_user_id=owner_user_id))

    async def set_title(self, *, session_id, title):  # type: ignore[override]
        await self._use(lambda s: s.set_title(session_id=session_id, title=title))

    async def evidence_context(self, *, canonical_evidence_id, owner_user_id=None):  # type: ignore[override]
        async with self._session_factory() as session:
            return await _evidence_context(
                session,
                canonical_evidence_id=canonical_evidence_id,
                owner_user_id=owner_user_id,
            )

    async def recent_history(self, *, session_id, limit=10):  # type: ignore[override]
        async with self._session_factory() as session:
            return await _history(session, session_id, limit)

    async def require_session(self, *, session_id, owner_user_id=None) -> None:  # type: ignore[override]
        async with self._session_factory() as session:
            await _load_session(session, session_id, owner_user_id)


async def _list_sessions(
    db: AsyncSession,
    processing_run_id: UUID,
    owner_user_id: UUID | None,
) -> list[ChatSessionResponse]:
    owner_filter = ChatSession.user_id.is_(None) if owner_user_id is None else ChatSession.user_id == owner_user_id
    count_subq = (
        select(ChatMessage.chat_session_id, func.count().label("msg_count"))
        .group_by(ChatMessage.chat_session_id)
        .subquery()
    )
    stmt = (
        select(ChatSession, func.coalesce(count_subq.c.msg_count, 0))
        .outerjoin(count_subq, ChatSession.chat_session_id == count_subq.c.chat_session_id)
        .where(ChatSession.processing_run_id == processing_run_id)
        .where(owner_filter)
        .order_by(ChatSession.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [_session_response(session, count) for session, count in rows]
