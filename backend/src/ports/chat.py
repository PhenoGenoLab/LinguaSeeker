"""Chat persistence ports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from src.core.tools.review.contracts import (
    ChatAction,
    ChatMessageResponse,
    ChatSessionResponse,
)


@dataclass(frozen=True)
class HistoryMessage:
    """One prior message used to build router context."""

    role: str
    content: str


class ChatStore(Protocol):
    """Persist chat sessions and messages."""

    async def create_session(
        self,
        *,
        processing_run_id: UUID | None,
        user_id: UUID | None = None,
    ) -> ChatSessionResponse: ...

    async def require_session(self, *, session_id: UUID, owner_user_id: UUID | None = None) -> None: ...

    async def get_session(
        self,
        *,
        session_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> ChatSessionResponse: ...

    async def list_sessions(
        self,
        *,
        processing_run_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> list[ChatSessionResponse]: ...

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
    ) -> ChatMessageResponse: ...

    async def list_messages(
        self,
        *,
        session_id: UUID,
        limit: int = 100,
        owner_user_id: UUID | None = None,
    ) -> list[ChatMessageResponse]: ...

    async def set_title(self, *, session_id: UUID, title: str) -> None: ...

    async def evidence_context(
        self,
        *,
        canonical_evidence_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> str: ...

    async def recent_history(self, *, session_id: UUID, limit: int = 10) -> list[HistoryMessage]: ...
